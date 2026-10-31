"""مدیریت webhook ربات بله از خط فرمان.

نمونه‌ها
--------
    python scripts/set_webhook.py --info
    python scripts/set_webhook.py --url https://qurana.onrender.com
    python scripts/set_webhook.py --url https://qurana.onrender.com --secret my-secret
    python scripts/set_webhook.py --delete

اگر --url داده نشود، از PUBLIC_BASE_URL (یا RENDER_EXTERNAL_URL) استفاده می‌شود.
توکن هرگز چاپ نمی‌شود.
"""
import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from config import (BALE_TOKEN, PUBLIC_BASE_URL, WEBHOOK_PATH_PREFIX,
                    WEBHOOK_SECRET)
from src.bale_api import BaleClient, redact_secret_url


def _print_info(info):
    """وضعیت webhook را بدون افشای secret چاپ می‌کند."""
    safe = dict(info or {})
    if safe.get("url"):
        safe["url"] = redact_secret_url(safe["url"])
    print(json.dumps(safe, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="ثبت/حذف/بررسی webhook ربات بله")
    parser.add_argument("--url", help="آدرس پایهٔ سرویس، مثلاً https://qurana.onrender.com")
    parser.add_argument("--secret", default=WEBHOOK_SECRET,
                        help="بخش مخفی مسیر (پیش‌فرض: WEBHOOK_SECRET)")
    parser.add_argument("--info", action="store_true", help="فقط وضعیت فعلی را نشان بده")
    parser.add_argument("--delete", action="store_true", help="webhook را حذف کن (بازگشت به polling)")
    args = parser.parse_args()

    if not BALE_TOKEN:
        print("❌ BALE_TOKEN تنظیم نشده است.")
        return 1

    client = BaleClient(BALE_TOKEN)

    if args.info:
        _print_info(client.get_webhook_info())
        return 0

    if args.delete:
        print(client.delete_webhook())
        print("✅ webhook حذف شد؛ حالا می‌توانید با app.py به‌صورت polling اجرا کنید.")
        return 0

    base = (args.url or PUBLIC_BASE_URL or "").strip().rstrip("/")
    if not base:
        print("❌ آدرس پایه مشخص نیست: --url بدهید یا PUBLIC_BASE_URL را تنظیم کنید.")
        return 1

    path = f"{WEBHOOK_PATH_PREFIX}/{args.secret}" if args.secret else WEBHOOK_PATH_PREFIX
    url = f"{base}{path}"
    client.set_webhook(url)
    print("✅ webhook ثبت شد:", redact_secret_url(url))
    _print_info(client.get_webhook_info())
    return 0


if __name__ == "__main__":
    sys.exit(main())
