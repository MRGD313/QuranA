"""بررسی بهداشت مخزن پیش از انتشار/کامیت.

- اطمینان از اینکه `.env` در گیت ردیابی نمی‌شود.
- جست‌وجوی الگوهای شبیه توکن در فایل‌های متنی مخزن.
- هشدار دربارهٔ فایل‌های داده/گزارش که نباید منتشر شوند.

این اسکریپت جایگزین ابزارهای تخصصی اسکن راز (مثل gitleaks) نیست، اما از
خطاهای رایج جلوگیری می‌کند. بدون نیاز به شبکه اجرا می‌شود.
"""
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", "raw", "reports"}
TEXT_EXT = {".py", ".md", ".txt", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".json", ".ps1", ".example"}

# توکن ربات بله: چند رقم + دو نقطه + رشته طولانی
TOKEN_PATTERN = re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b")
# کلیدهای عمومی رایج (احتیاطی)
GENERIC_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|token)\b\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{20,}"),
]

problems = []
warnings = []


def iter_files():
    for path in BASE_DIR.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(BASE_DIR)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if path.suffix.lower() in {".db", ".sqlite", ".pyc"}:
            continue
        if rel.name == ".env" or rel.name.startswith(".env.") and rel.name != ".env.example":
            continue
        yield path, rel


def check_gitignore():
    try:
        out = subprocess.run(
            ["git", "check-ignore", ".env"],
            cwd=BASE_DIR, capture_output=True, text=True, timeout=10,
        )
        if out.returncode != 0:
            warnings.append(".env هنوز در گیت نادیده گرفته نشده است (یا مخزن گیت نیست).")
    except Exception:
        warnings.append("اجرای git check-ignore ممکن نشد؛ به‌صورت دستی بررسی کنید.")


def main():
    if not (BASE_DIR / ".env.example").exists():
        problems.append(".env.example وجود ندارد.")

    tracked_env = False
    try:
        out = subprocess.run(
            ["git", "ls-files", "--error-unmatch", ".env"],
            cwd=BASE_DIR, capture_output=True, text=True, timeout=10,
        )
        tracked_env = out.returncode == 0
    except Exception:
        tracked_env = False
    if tracked_env:
        problems.append("فایل .env در گیت ردیابی می‌شود! توکن را فوراً باطل کنید و فایل را از ردیابی خارج کنید.")

    check_gitignore()

    for path, rel in iter_files():
        if path.suffix.lower() not in TEXT_EXT and path.name != ".env.example":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if rel.name == ".env.example":
            continue
        if TOKEN_PATTERN.search(text):
            problems.append(f"الگوی شبیه توکن بله در فایل: {rel}")
        for pat in GENERIC_PATTERNS:
            if pat.search(text):
                problems.append(f"الگوی شبیه کلید/رمز در فایل: {rel}")
                break

    if problems:
        print("❌ مشکلات بهداشت مخزن:")
        for p in problems:
            print(" -", p)
        sys.exit(1)

    if warnings:
        print("⚠ هشدارها:")
        for w in warnings:
            print(" -", w)
    print("✅ بهداشت مخزن تأیید شد: توکن/رمز آشکاری یافت نشد.")


if __name__ == "__main__":
    main()
