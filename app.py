"""نقطه شروع ربات: polling حلقه getUpdates و پردازش متوالی پیام‌ها."""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# سازگاری لاگ فارسی روی ویندوز (پیش‌فرض کنسول cp1252 است)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from config import BALE_TOKEN, DB_PATH, APP_NAME, APP_VERSION
from src.bale_api import BaleClient, iter_text_messages
from src.bot_handler import BotHandler
from src.quran_repository import QuranRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("qurana")


def main():
    if not BALE_TOKEN:
        print("خطا: توکن ربات تنظیم نشده است. فایل .env را بسازید و BALE_TOKEN را پر کنید.")
        print("مشابه:  Copy-Item .env.example .env   سپس توکن واقعی را داخل .env بگذارید.")
        sys.exit(1)

    log.info("%s v%s — شروع", APP_NAME, APP_VERSION)
    repo = QuranRepository(DB_PATH).connect()
    client = BaleClient(BALE_TOKEN)
    me = client.get_me()
    log.info("ربات بله متصل شد: %s", me)

    handler = BotHandler(client, repo)
    log.info("شروع polling. برای خارج شدن Ctrl+C بزنید.")
    try:
        while True:
            try:
                updates = client.get_updates(wait_timeout=30)
            except Exception as exc:
                log.warning("خطای شبکه/API بله: %s — ۵ ثانیه صبر", exc)
                import time
                time.sleep(5)
                continue
            for chat_id, message_id, text in iter_text_messages(updates):
                log.info("پیام از chat=%s: %r", chat_id, text)
                handler.handle_update(chat_id, message_id, text)
    except KeyboardInterrupt:
        log.info("ربات متوقف شد.")
    finally:
        repo.close()


if __name__ == "__main__":
    main()
