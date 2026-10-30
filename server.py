"""سرور webhook: بله با هر پیام، سرور را بیدار می‌کند (مناسب پلن رایگان Render).

معماری
------
    بله ──POST──▶ https://<host>/hook/<secret> ──▶ BotHandler ──▶ پاسخ

برخلاف app.py که ۲۴/۷ با getUpdates نظرسنجی می‌کند، این حالت فقط وقتی بیدار
می‌شود که پیامی برسد؛ در نتیجه سهمیهٔ سرویس رایگان هدر نمی‌رود.

نکته‌های طراحی
--------------
* مسیر webhook یک بخش مخفی دارد، چون بله هدر امضا/secret ندارد.
* هر update_id فقط یک‌بار پردازش می‌شود؛ بنابراین تلاش مجدد بله پاسخ تکراری
  تولید نمی‌کند.
* پردازش پیش از پاسخ ۲۰۰ انجام می‌شود تا اگر پروسه وسط کار متوقف شد پیام از
  دست نرود (جست‌وجو در SQLite چند میلی‌ثانیه است).
"""
import json
import logging
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
# سازگاری لاگ فارسی روی ویندوز (پیش‌فرض کنسول cp1252 است)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from config import (APP_NAME, APP_VERSION, BALE_TOKEN, DB_PATH, PORT,
                    PUBLIC_BASE_URL, WEBHOOK_PATH_PREFIX, WEBHOOK_SECRET)
from src.bale_api import BaleClient, iter_text_messages
from src.bot_handler import BotHandler
from src.quran_repository import QuranRepository

log = logging.getLogger("qurana.webhook")

MAX_BODY_BYTES = 1 << 20   # ۱ مگابایت کافی است؛ update متنی چند کیلوبایت است
SEEN_LIMIT = 2000          # هم‌اندازهٔ پنجرهٔ نگه‌داری update در بله


class WebhookApp:
    """منطق خالص مسیریابی/پردازش؛ مستقل از سوکت تا آزمون‌پذیر باشد."""

    def __init__(self, handler, secret: str = "", path_prefix: str = WEBHOOK_PATH_PREFIX):
        self.handler = handler
        self.secret = (secret or "").strip()
        self.path_prefix = "/" + path_prefix.strip("/")
        self.started_at = time.time()
        self._seen = {}
        self._seen_lock = threading.Lock()

    @property
    def path(self):
        if self.secret:
            return f"{self.path_prefix}/{self.secret}"
        return self.path_prefix

    def public_url(self, base_url: str) -> str:
        return f"{base_url.rstrip('/')}{self.path}"

    # ---------- پردازش ----------
    def process_update(self, update) -> bool:
        """update را پردازش می‌کند. اگر تکراری باشد False برمی‌گرداند."""
        update_id = update.get("update_id")
        if update_id is not None:
            with self._seen_lock:
                if update_id in self._seen:
                    log.info("update تکراری نادیده گرفته شد: %s", update_id)
                    return False
                self._seen[update_id] = time.time()
                while len(self._seen) > SEEN_LIMIT:
                    self._seen.pop(next(iter(self._seen)), None)
        for chat_id, message_id, text in iter_text_messages([update]):
            log.info("پیام از chat=%s: %r", chat_id, text)
            self.handler.handle_update(chat_id, message_id, text)
        return True

    # ---------- مسیریابی ----------
    def dispatch(self, method: str, path: str, body: bytes = b""):
        """(status, payload) را برمی‌گرداند؛ بدون سوکت، برای آزمون و لایهٔ HTTP."""
        path = (path or "/").split("?", 1)[0].rstrip("/") or "/"

        if method == "GET" and path == "/healthz":
            return 200, {"ok": True, "service": APP_NAME, "version": APP_VERSION,
                         "uptime_s": round(time.time() - self.started_at, 1)}

        if method == "GET" and path == "/":
            return 200, {"ok": True, "service": APP_NAME, "version": APP_VERSION}

        if method == "POST" and path == self.path:
            try:
                update = json.loads(body.decode("utf-8") or "{}")
            except (UnicodeDecodeError, ValueError):
                log.warning("بدنهٔ webhook JSON معتبر نبود")
                return 400, {"ok": False, "error": "invalid json"}
            if not isinstance(update, dict):
                return 400, {"ok": False, "error": "invalid update"}
            if not isinstance(update.get("update_id"), int):
                return 400, {"ok": False, "error": "missing update_id"}
            try:
                fresh = self.process_update(update)
            except Exception:
                # handle_update خودش خطا را می‌گیرد؛ این فقط تور ایمنی است.
                # ۲۰۰ برمی‌گردانیم چون با ضد تکرار، تلاش مجدد بی‌فایده است.
                log.exception("پردازش update شکست خورد")
                return 200, {"ok": True, "processed": False}
            return 200, {"ok": True, "processed": fresh}

        return 404, {"ok": False, "error": "not found"}


class _WebhookHTTPHandler(BaseHTTPRequestHandler):
    server_version = "QuranA"
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def _handle(self, method):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length > MAX_BODY_BYTES:
            self._send(413, {"ok": False, "error": "body too large"})
            return
        body = self.rfile.read(length) if length > 0 else b""
        status, payload = self.server.app.dispatch(method, self.path, body)
        self._send(status, payload)

    def _send(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        log.info("%s - %s", self.address_string(), fmt % args)


def _register_webhook(client, url, retry_delay=30):
    """ثبت idempotent آدرس webhook؛ اگر بله در دسترس نبود، تا موفقیت تلاش می‌کند."""
    while True:
        try:
            info = client.get_webhook_info() or {}
            if info.get("url") == url:
                log.info("webhook از قبل ثبت شده است: %s", url)
                return
            client.set_webhook(url)
            log.info("webhook ثبت شد: %s", url)
            return
        except Exception as exc:
            log.warning("ثبت webhook ناموفق بود (%s)؛ %s ثانیه دیگر تلاش مجدد",
                        exc, retry_delay)
            time.sleep(retry_delay)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    if not BALE_TOKEN:
        log.error("خطا: توکن ربات تنظیم نشده است (BALE_TOKEN).")
        return 1

    if not WEBHOOK_SECRET:
        log.warning("WEBHOOK_SECRET تنظیم نشده؛ مسیر webhook قابل حدس است.")

    log.info("%s v%s — شروع (حالت webhook)", APP_NAME, APP_VERSION)
    repo = QuranRepository(DB_PATH).connect()
    client = BaleClient(BALE_TOKEN)
    app = WebhookApp(BotHandler(client, repo), secret=WEBHOOK_SECRET)

    if PUBLIC_BASE_URL:
        url = app.public_url(PUBLIC_BASE_URL)
        threading.Thread(target=_register_webhook, args=(client, url),
                         daemon=True, name="register-webhook").start()
    else:
        log.warning("PUBLIC_BASE_URL/RENDER_EXTERNAL_URL تنظیم نشده؛ "
                    "webhook خودکار ثبت نمی‌شود (از scripts/set_webhook.py استفاده کنید).")

    server = ThreadingHTTPServer(("0.0.0.0", PORT), _WebhookHTTPHandler)
    server.daemon_threads = True
    server.app = app
    log.info("در حال گوش دادن روی پورت %s — مسیر webhook: %s/<secret>", PORT, app.path_prefix)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("سرور متوقف شد.")
    finally:
        server.server_close()
        repo.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
