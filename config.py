"""تنظیمات پروژه QuranA (قرآنا) — ربات واژه‌های هم‌ریشه قرآن کریم."""
import os
from pathlib import Path

APP_NAME = "QuranA"
APP_NAME_FA = "قرآنا"
APP_VERSION = "0.1.0"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "quran.db"
REPORTS_DIR = DATA_DIR / "reports"

BALE_API_BASE = "https://tapi.bale.ai/bot"
BALE_API_FILE_BASE = "https://tapi.bale.ai/file/bot"

BALE_TOKEN = os.environ.get("BALE_TOKEN", "").strip()

# ---------- استقرار با webhook (اختیاری؛ اجرای محلی با polling به آن نیاز ندارد) ----------
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "").strip()
WEBHOOK_PATH_PREFIX = "/hook"
PUBLIC_BASE_URL = (
    os.environ.get("PUBLIC_BASE_URL")
    or os.environ.get("RENDER_EXTERNAL_URL")
    or ""
).strip().rstrip("/")


def _int_env(name, default):
    try:
        return int(os.environ.get(name, "") or default)
    except (TypeError, ValueError):
        return default


PORT = _int_env("PORT", 8080)

POLL_TIMEOUT = 30
REPORT_DIR_MAX_AGE_DAYS = 7

QURAN_TEXT_SOURCE = "Tanzil Quran Text (Uthmani, version 1.1) — tanzil.net"
MORPHOLOGY_SOURCE = "Quranic Arabic Corpus (morphology, version 0.4) — corpus.quran.com"
