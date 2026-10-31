# داده‌های QuranA

این پوشه **دادهٔ شخص ثالث** را نگه می‌دارد. برای رعایت مجوزها، فایل‌های خام و
پایگاه دادهٔ ساخته‌شده در مخزن گیت ذخیره نمی‌شوند و در زمان راه‌اندازی ساخته
می‌شوند. منبع واحد مجوزها: [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

## فایل‌های مورد انتظار در `data/raw/`

- `quran-uthmani.txt` — متن قرآن، Tanzil Uthmani 1.1 (کپی verbatim با ذکر منبع).
- `quranic-corpus-morphology-0.4.txt` — تحلیل صرفی، Quranic Arabic Corpus 0.4 (GPL).
- `quran-data.xml` — نام سوره‌ها و شمار آیات، متادیتای Tanzil (CC BY).

## ساخت مجدد

```bash
python scripts/download_data.py   # دانلود منابع رسمی
python scripts/prepare_data.py    # ساخت data/quran.db
python scripts/validate_data.py   # اعتبارسنجی
```

## ساختار `quran.db`

شرح جدول‌ها و ارتباط متن/صرف در
[`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md#مدل-داده-sqlite) آمده است.

> `data/quran.db` فقط یک فهرست محلی از داده‌های بالاست و همراه مخزن منتشر
> نمی‌شود. اگر آن را بازتوزیع می‌کنید، شرایط منابع اصلی (از جمله GPL برای
> دادهٔ صرفی) را رعایت کنید.
