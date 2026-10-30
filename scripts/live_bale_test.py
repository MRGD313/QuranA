"""آزمون یکپارچه واقعی بله.

به توکن معتبر `BALE_TOKEN` نیاز دارد. به‌صورت پیش‌فرض فقط اتصال را بررسی
می‌کند (getMe) و تعداد updates را نشان می‌دهد. با `--send` پیام‌های موجود را
پاسخ می‌دهد و یک فایل گزارش واقعی به همان گفت‌وگو ارسال می‌کند.

توکن هرگز چاپ نمی‌شود.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from config import BALE_TOKEN, DB_PATH
from src.bale_api import BaleClient, iter_text_messages
from src.bot_handler import BotHandler
from src.quran_repository import QuranRepository
from src.morphology import resolve_roots
from src.search_service import search_root
from src.report_generator import generate_report
from src.text_normalizer import normalize_word


def main():
    if not BALE_TOKEN:
        print("❌ BALE_TOKEN تنظیم نشده است.")
        sys.exit(1)

    client = BaleClient(BALE_TOKEN)
    me = client.get_me()
    print("getMe:", me.get("username"), "| id:", me.get("id"))

    info = client.get_webhook_info() or {}
    if (info.get("url") or "").strip():
        print("⚠ webhook فعال است:", info["url"])
        print("  تا وقتی webhook ثبت شده باشد، getUpdates کار نمی‌کند.")
        print("  برای تست polling: python scripts/set_webhook.py --delete")
        sys.exit(1)

    send = "--send" in sys.argv
    updates = client.get_updates(wait_timeout=0)
    print("updates:", len(updates))

    if not send:
        print("حالت بررسی اتصال. برای پاسخ و ارسال واقعی: --send")
        return

    repo = QuranRepository(DB_PATH).connect()
    handler = BotHandler(client, repo)
    chat_ids = []
    for chat_id, message_id, text in iter_text_messages(updates):
        chat_ids.append(chat_id)
        print("message from", chat_id, "| text:", text[:40])
        handler.handle_update(chat_id, message_id, text)

    if not chat_ids:
        print("⚠ هیچ پیام تازه‌ای نیست؛ ابتدا در بله به ربات پیام بدهید.")
        return

    # ارسال یک فایل گزارش واقعی برای بررسی مسیر sendDocument
    word = "مجرمون"
    norm = normalize_word(word)
    res = resolve_roots(word, norm, repo)
    print("root:", res.root, "| ambiguous:", res.ambiguity)
    if not res.ok:
        print("ریشه یکتا پیدا نشد.")
        return
    result = search_root(res.root, repo)
    path = generate_report(res.root, word, norm, result, repo)
    sent = client.send_document(chat_ids[-1], path,
                                caption=f"QuranA — آزمون ارسال فایل: ریشه «{res.root}» — {result['unique_ayahs']} آیه")
    doc = sent.get("document") or {}
    print("✅ sendDocument موفق | message_id:", sent.get("message_id"),
          "| file_name:", doc.get("file_name"), "| size:", doc.get("file_size"))
    repo.close()


if __name__ == "__main__":
    main()
