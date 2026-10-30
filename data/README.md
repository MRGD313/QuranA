# داده‌های QuranA

این پوشه **داده‌های شخص ثالث** را نگه می‌دارد. برای رعایت مجوزها، فایل‌های خام
و پایگاه دادهٔ ساخته‌شده در مخزن گیت ذخیره نمی‌شوند و در زمان راه‌اندازی دانلود
و ساخته می‌شوند.

## فایل‌های مورد انتظار در `data/raw/`

| فایل | منبع | نسخه | مجوز/شرایط |
|---|---|---|---|
| `quran-uthmani.txt` | [Tanzil.net](https://tanzil.net/download/) | 1.1 | کپی verbatim با ذکر منبع و لینک؛ تغییر متن ممنوع |
| `quranic-corpus-morphology-0.4.txt` | [Quranic Arabic Corpus](https://corpus.quran.com/download) | 0.4 | GNU GPL؛ کپی verbatim با حفظ سربرگ |
| `quran-data.xml` | [Tanzil metadata](http://tanzil.net/res/text/metadata/quran-data.xml) | 1.0 | CC BY |

جزئیات کامل در [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) آمده است.

## ساخت مجدد

```bash
python scripts/download_data.py   # دانلود منابع رسمی
python scripts/prepare_data.py    # ساخت data/quran.db
python scripts/validate_data.py   # اعتبارسنجی
```

## ساختار `quran.db`

- `surahs` — شماره، تعداد آیات، نام عربی/انگلیسی.
- `ayat` — متن Uthmani هر آیه (بدون بسم‌الله تکراری اول سوره‌ها).
- `words` — واژه‌های هر آیه: فرم Buckwalter، فرم عربی تحلیل، فرم واقعی متن، فرم نرمال.
- `segments` — سگمنت‌های صرفی: نوع، مدخل (lemma)، ریشه (root)، ویژگی‌های خام.

> پایگاه داده صرفاً یک فهرست محلی از داده‌های بالا است و همراه مخزن منتشر
> نمی‌شود. اگر آن را بازتوزیع می‌کنید، شرایط منابع اصلی (از جمله GPL برای
> داده‌های صرفی) را رعایت کنید.
