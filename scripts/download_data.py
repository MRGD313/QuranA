"""دانلود منابع رسمی از اینترنت و ذخیره در data/raw.

- متن قرآن Uthmani (Tanzil.net) — مجوز: استفاده با ذکر منبع (متن verbatim)
- تحلیل صرفی قرآنی (Quranic Arabic Corpus 0.4) — مجوز: GNU GPL (کپی verbatim مجاز)
- متادیتای سوره‌ها (Tanzil) — cc-by

این اسکریپت فقط به اینترنت نیاز دارد و هرگز محتوای ساختگی تولید نمی‌کند.
"""
import io
import sys
import zipfile
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW = BASE_DIR / "data" / "raw"

TANZIL_URL = "https://tanzil.net/pub/download/index.php"
TANZIL_PARAMS = {
    "marks": "true", "sajdah": "true", "rub": "true", "tatweel": "true",
    "quranType": "uthmani", "outType": "txt-2", "agree": "true",
}
CORPUS_URL = "https://corpus.quran.com/download/default.jsp"
CORPUS_EMAIL = "research@opencode.local"
META_URL = "http://tanzil.net/res/text/metadata/quran-data.xml"


def save(name: str, content: bytes):
    path = RAW / name
    path.write_bytes(content)
    print(f"با موفقیت ذخیره شد: {path.name}  ({len(content)/1024:.0f} KB)")


def fetch_tanzil():
    r = requests.post(TANZIL_URL, data=TANZIL_PARAMS, timeout=120)
    r.raise_for_status()
    if b"Tanzil Quran Text" not in r.content:
        raise RuntimeError("پاسخ Tanzil سربرگ معمول ندارد؛ احتمالاً Faster فرم تغییر کرده است.")
    save("quran-uthmani.txt", r.content)


def fetch_corpus():
    s = requests.Session()
    # گام ۱: ثبت ایمیل تحقیق در فرم رسمی
    r1 = s.post(CORPUS_URL, data={"txtEmail": CORPUS_EMAIL}, timeout=60)
    r1.raise_for_status()
    # گام ۲: دریافت فایل ZIP تحلیل صرفی (downloadID=3)
    r2 = s.post(CORPUS_URL, data={"txtEmail": CORPUS_EMAIL, "downloadID": "3", "validEmail": "true"}, timeout=120)
    r2.raise_for_status()
    content = r2.content
    if content[:2] != b"PK":
        raise RuntimeError("پاسخ Corpus یک فایل ZIP نیست؛ فرم/سرویس دانلود تغییر کرده است.")
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        candidates = [n for n in zf.namelist() if n.lower().endswith(".txt")]
        if not candidates:
            raise RuntimeError("در بستهٔ Corpus فایل متنی پیدا نشد.")
        raw = zf.read(candidates[0])
    if b"Kais Dukes" not in raw[:3000]:
        raise RuntimeError("فایل استخراج‌شده سربرگ رسمی Corpus را ندارد؛ دانلود را بازبینی کنید.")
    save("quranic-corpus-morphology-0.4.txt", raw)


def fetch_metadata():
    r = requests.get(META_URL, timeout=60)
    r.raise_for_status()
    save("quran-data.xml", r.content)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    targets = sys.argv[1:] or ["tanzil", "corpus", "metadata"]
    if "tanzil" in targets:
        fetch_tanzil()
    if "corpus" in targets:
        fetch_corpus()
    if "metadata" in targets:
        fetch_metadata()
    print("اکنون scripts/prepare_data.py را اجرا کنید.")


if __name__ == "__main__":
    main()
