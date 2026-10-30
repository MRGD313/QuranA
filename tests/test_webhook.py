"""آزمون‌های لایهٔ webhook: مسیر مخفی، ضد تکرار، سلامت و پیام جلسهٔ منقضی."""
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from server import WebhookApp
from src.bot_handler import BotHandler, MSG_SESSION_EXPIRED

SECRET = "test-secret"


def make_app(repo, fake_client, tmp_path, secret=SECRET):
    handler = BotHandler(fake_client, repo, out_dir=tmp_path)
    return WebhookApp(handler, secret=secret)


def update_payload(update_id, chat_id=1, text="كتاب"):
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id,
            "chat": {"id": chat_id},
            "text": text,
        },
    }


def post(app, payload, path=None):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return app.dispatch("POST", path or app.path, body)


# ---------------- مسیر و سلامت ----------------
def test_webhook_path_contains_secret(repo, fake_client, tmp_path):
    app = make_app(repo, fake_client, tmp_path)
    assert app.path == f"/hook/{SECRET}"


def test_public_url(repo, fake_client, tmp_path):
    app = make_app(repo, fake_client, tmp_path)
    assert app.public_url("https://qurana.onrender.com/") == \
        f"https://qurana.onrender.com/hook/{SECRET}"


def test_health_ok_and_does_not_leak_secret(repo, fake_client, tmp_path):
    app = make_app(repo, fake_client, tmp_path)
    status, payload = app.dispatch("GET", "/healthz")
    assert status == 200 and payload["ok"] is True
    assert SECRET not in json.dumps(payload, ensure_ascii=False)


def test_wrong_secret_is_404(repo, fake_client, tmp_path):
    app = make_app(repo, fake_client, tmp_path)
    status, payload = post(app, update_payload(1), path="/hook/wrong")
    assert status == 404 and payload["ok"] is False
    assert fake_client.docs == []


def test_unknown_path_is_404(repo, fake_client, tmp_path):
    app = make_app(repo, fake_client, tmp_path)
    status, _payload = app.dispatch("GET", "/nope")
    assert status == 404


# ---------------- پردازش ----------------
def test_post_processes_message(repo, fake_client, tmp_path):
    app = make_app(repo, fake_client, tmp_path)
    status, payload = post(app, update_payload(10))
    assert status == 200 and payload["processed"] is True
    assert fake_client.docs, "باید گزارش ارسال شده باشد"


def test_duplicate_update_ignored(repo, fake_client, tmp_path):
    app = make_app(repo, fake_client, tmp_path)
    status1, payload1 = post(app, update_payload(20))
    status2, payload2 = post(app, update_payload(20))
    assert status1 == 200 and payload1["processed"] is True
    assert status2 == 200 and payload2["processed"] is False
    assert len(fake_client.docs) == 1


def test_non_message_update_is_accepted(repo, fake_client, tmp_path):
    app = make_app(repo, fake_client, tmp_path)
    status, payload = post(app, {"update_id": 30})
    assert status == 200 and payload["processed"] is True
    assert fake_client.sent == []


def test_invalid_json_is_400(repo, fake_client, tmp_path):
    app = make_app(repo, fake_client, tmp_path)
    status, payload = app.dispatch("POST", app.path, b"{not json")
    assert status == 400 and payload["ok"] is False


def test_json_array_is_400(repo, fake_client, tmp_path):
    app = make_app(repo, fake_client, tmp_path)
    status, _payload = app.dispatch("POST", app.path, b"[]")
    assert status == 400


def test_missing_update_id_is_400(repo, fake_client, tmp_path):
    app = make_app(repo, fake_client, tmp_path)
    status, payload = post(app, {"message": {"chat": {"id": 1}, "text": "كتاب"}})
    assert status == 400 and payload["ok"] is False
    assert fake_client.docs == []


# ---------------- محافظ حالت polling ----------------
class _PollingFakeClient:
    def __init__(self, url=""):
        self.url = url
        self.deleted = False

    def get_webhook_info(self):
        return {"url": self.url}

    def delete_webhook(self):
        self.deleted = True
        return True


def test_polling_allowed_without_webhook():
    from app import ensure_polling_mode

    client = _PollingFakeClient("")
    assert ensure_polling_mode(client) is True
    assert client.deleted is False


def test_polling_blocked_when_webhook_active():
    from app import ensure_polling_mode

    client = _PollingFakeClient("https://qurana.onrender.com/hook/x")
    assert ensure_polling_mode(client) is False
    assert client.deleted is False


def test_polling_force_deletes_webhook():
    from app import ensure_polling_mode

    client = _PollingFakeClient("https://qurana.onrender.com/hook/x")
    assert ensure_polling_mode(client, force=True) is True
    assert client.deleted is True


def test_digit_without_session_is_friendly(repo, fake_client, tmp_path):
    app = make_app(repo, fake_client, tmp_path)
    status, _payload = post(app, update_payload(40, text="1"))
    assert status == 200
    assert fake_client.last_text() == MSG_SESSION_EXPIRED


def test_handler_runs_in_worker_thread(repo, fake_client, tmp_path):
    """در حالت webhook، پردازش در thread سرور HTTP انجام می‌شود (SQLite باید بسازد)."""
    import threading

    app = make_app(repo, fake_client, tmp_path)
    errors = []

    def run():
        try:
            post(app, update_payload(50))
        except Exception as exc:  # pragma: no cover - فقط برای گزارش بهتر
            errors.append(exc)

    t = threading.Thread(target=run)
    t.start()
    t.join(timeout=30)

    assert not errors
    assert fake_client.docs, "باید گزارش ارسال شده باشد"
    assert not any("خطای داخلی" in text for text in fake_client.texts())
