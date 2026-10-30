"""دانلود منابع رسمی از اینترنت و ذخیره در data/raw.

- متن قرآن Uthmani (Tanzil.net) — مجوز: استفاده با ذکر منبع (متن verbatim)
- تحلیل صرفی قرآنی (Quranic Arabic Corpus 0.4) — مجوز: GNU GPL (کپی verbatim مجاز)
- متادیتای سوره‌ها (Tanzil) — cc-by

این اسکریپت فقط به اینترنت نیاز دارد و هرگز محتوای ساختگی تولید نمی‌کند.
"""
import sys
from pathlib import Path

import requests

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
    # گام ۱: صفحه دانلود با ایمیل تحقیق
    r1 = s.post(CORPUS_URL, data={"txtEmail": CORPUS_EMAIL}, timeout=60)
    r1.raise_for_status()
    # گام ۲: درخواست فایل morphology 0.4 (downloadID=3)
    r2 = s.post(CORPUS_URL, data={"txtEmail": CORPUS_EMAIL, "downloadID": "3", "validEmail": "true"}, timeout=120)
    r2.raise_for_status()
    if b"Kais Dukes" not in r2.content[:3000]:
        raise RuntimeError("فایل دریافت‌شده سربرگ رسمی Corpus را ندارد؛ دانلود را مرور کنید.")
    save("quranic-corpus-morphology-0.4.txt", r2.content)


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
