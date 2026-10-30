"""کلاینت API ربات بله (messenger Bale) — فقط از متدهای مستند رسمی استفاده می‌کند.

بررسی منبع: مسیرها با پکیج متن‌باز python-bale-bot (جایی که SDK رسمی با
API سرور بله سازگار است) تأیید شد. base_url = https://tapi.bale.ai/bot{token}

  GET  https://tapi.bale.ai/bot{token}/getMe
  POST https://tapi.bale.ai/bot{token}/getUpdates       {offset, limit, timeout}
  POST https://tapi.bale.ai/bot{token}/sendMessage     {chat_id, text}
  POST https://tapi.bale.ai/bot{token}/sendDocument    multipart: chat_id + document + caption
  POST https://tapi.bale.ai/bot{token}/setWebhook      {url}
  POST https://tapi.bale.ai/bot{token}/deleteWebhook   {}
  GET  https://tapi.bale.ai/bot{token}/getWebhookInfo

بدون توکن هیچ تماس شبکه انجام نمی‌شود؛ در آن حالت فقط سازنده و منطق داخلی ساخته می‌شود.
"""
import logging
import time
from pathlib import Path

import requests

log = logging.getLogger(__name__)


class BaleApiError(Exception):
    def __init__(self, code, description):
        self.code = code
        self.description = description
        super().__init__(f"bale API error {code}: {description}")


class BaleClient:
    def __init__(self, token: str, base_url: str = None):
        self.token = (token or "").strip()
        self.base_url = (base_url or "https://tapi.bale.ai/bot").rstrip("/")
        self.session = requests.Session()
        self._offset = 0
        self._ready = bool(self.token)

    @property
    def ready(self) -> bool:
        return self._ready

    def _call(self, method: str, http_method: str = "POST", **kwargs):
        url = f"{self.base_url}{self.token}/{method}"
        resp = self.session.request(http_method, url=url, timeout=kwargs.pop("timeout", None) or 45, **kwargs)
        try:
            data = resp.json()
        except ValueError:
            raise BaleApiError(resp.status_code, "خروجی سرور JSON نبود: " + resp.text[:200])
        if not data.get("ok"):
            raise BaleApiError(data.get("error_code", resp.status_code), data.get("description", "خطای ناشناخته"))
        return data["result"]

    # ---------- دریافت پیام‌ها ----------
    def get_updates(self, offset: int = None, limit: int = 10, wait_timeout: int = 0):
        if not self.ready:
            raise RuntimeError("کلاینت بله آماده نیست (توکن تنظیم نشده).")
        params = {"offset": self._offset if offset is None else offset,
                  "limit": limit, "timeout": wait_timeout}
        result = self._call("getUpdates", json=params, timeout=wait_timeout + 45)
        updates = result if isinstance(result, list) else []
        if updates:
            self._offset = max(u["update_id"] for u in updates) + 1
        return updates

    # ---------- ارسال ----------
    def send_message(self, chat_id, text: str, reply_to_message_id=None):
        payload = {"chat_id": chat_id, "text": text}
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        return self._call("sendMessage", json=payload)

    def send_document(self, chat_id, file_path: Path, caption: str = None):
        if not self.ready:
            raise RuntimeError("کلاینت بله آماده نیست (توکن تنظیم نشده).")
        url = f"{self.base_url}{self.token}/sendDocument"
        data = {"chat_id": str(chat_id)}
        if caption:
            data["caption"] = caption
        with open(file_path, "rb") as fh:
            files = {"document": (Path(file_path).name, fh, "text/plain")}
            resp = self.session.post(url, data=data, files=files, timeout=120)
        try:
            payload = resp.json()
        except ValueError:
            raise BaleApiError(resp.status_code, "خروجی سرور JSON نبود: " + resp.text[:200])
        if not payload.get("ok"):
            raise BaleApiError(payload.get("error_code", resp.status_code), payload.get("description", "خطای ناشناخته"))
        return payload["result"]

    # ---------- webhook ----------
    def set_webhook(self, url: str, max_connections: int = None):
        """ثبت آدرس دریافت update. بله پورت‌های ۴۴۳ و ۸۸ را مستند کرده است."""
        if not self.ready:
            raise RuntimeError("کلاینت بله آماده نیست (توکن تنظیم نشده).")
        payload = {"url": url}
        if max_connections is not None:
            payload["max_connections"] = int(max_connections)
        return self._call("setWebhook", json=payload)

    def delete_webhook(self):
        """حذف webhook و بازگشت به حالت polling."""
        if not self.ready:
            raise RuntimeError("کلاینت بله آماده نیست (توکن تنظیم نشده).")
        return self._call("deleteWebhook", json={})

    def get_webhook_info(self):
        if not self.ready:
            raise RuntimeError("کلاینت بله آماده نیست (توکن تنظیم نشده).")
        return self._call("getWebhookInfo", http_method="GET")

    # ---------- ابزار ----------
    def get_me(self):
        return self._call("getMe", http_method="GET")


def iter_text_messages(updates):
    """استخراج پیام‌های متن از بسته updates. پیام‌های بدون متن نادیده گرفته می‌شوند."""
    for u in updates:
        msg = u.get("message") or u.get("edited_message")
        if not msg:
            continue
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        text = msg.get("text") or ""
        if chat_id is not None:
            yield chat_id, msg.get("message_id"), text.strip()
