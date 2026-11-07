# QuranA (قرآنا)

[![CI](https://github.com/MRGD313/QuranA/actions/workflows/ci.yml/badge.svg)](https://github.com/MRGD313/QuranA/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![release](https://img.shields.io/badge/release-v0.2.0-orange.svg)](https://github.com/MRGD313/QuranA/releases/tag/v0.2.0)

**QuranA** یک ربات اوپن‌سورس برای پیام‌رسان بله است: یک واژهٔ عربی می‌فرستید،
ریشهٔ صرفی آن از Quranic Arabic Corpus استخراج می‌شود، واژه‌های قرآنی هم‌ریشه
پیدا می‌شوند و متن کامل آیات از Tanzil Uthmani در قالب یک فایل `.txt` (UTF-8)
در همان گفت‌وگو ارسال می‌شود. وضعیت: نسخهٔ ۰.۲.۰ (بتا).

## ویژگی‌ها

- ریشه از دادهٔ صرفی رسمی، نه شباهت رشته‌ای یا حدس مدل زبانی.
- پس از هر گزارش، یک **متن پرامپت آمادهٔ کپی** برای چت‌بات ارسال می‌شود تا با فایل پیوست گفت‌وگو کنید؛ پرامپت شامل **بازبینی نقادانه** و فهرست آیات ناهم‌خوان/متعارض با معنای محوری هم هست.
- رفع ابهام چندریشه با فهرست شماره‌دار و انتخاب کاربر.
- آیات یکتا و مرتب، با نام سوره و شمارهٔ آیه و آمار تفکیک‌شده.
- گزارش با ذکر منبع/نسخهٔ داده؛ پشتیبانی از polling و webhook.

## شروع سریع

```powershell
git clone https://github.com/MRGD313/QuranA.git
Set-Location QuranA
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt pytest
Copy-Item .env.example .env    # BALE_TOKEN را وارد کنید
.\.venv\Scripts\python scripts\download_data.py
.\.venv\Scripts\python scripts\prepare_data.py
.\.venv\Scripts\python scripts\validate_data.py
.\.venv\Scripts\python app.py
```

در لینوکس/مک، فعال‌سازی محیط `source .venv/bin/activate` است و دستورها با
`python` اجرا می‌شوند. توکن فقط از `BALE_TOKEN` خوانده می‌شود. متغیرهای
webhook و استقرار: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## استفاده

1. در بله به ربات `/start` بدهید و یک واژه بفرستید (`علم`، `كتاب`، `سَجَدَ`).
2. اگر چند ریشه محتمل بود، شمارهٔ ریشه را بفرستید.
3. فایل `quran_roots_<ریشه>_<تاریخ>.txt` را دریافت می‌کنید.
4. در پیام بعدی، متن پرامپت آماده می‌آید؛ آن را کپی کنید و همراه فایل پیوست به چت‌بات بدهید.

آزمون هسته بدون شبکه و بدون توکن: `python scripts/run_core_e2e.py سَجَدَ`

## داده‌ها و دقت

متن قرآن و صرف دو منبع مستقل‌اند و بازنویسی نمی‌شوند؛ فایل‌های خام در مخزن
نیستند و با `scripts/download_data.py` از منابع رسمی دانلود می‌شوند. متن از
[Tanzil Uthmani 1.1](https://tanzil.net/download/)، صرف از
[Quranic Arabic Corpus 0.4](https://corpus.quran.com/download). اعتبارسنجی:
۶۲۳۶ آیه، ۱۱۴ سوره، ۷۷٬۴۲۹ واژه، ۱٬۶۴۲ ریشه. جزئیات مجوز:
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)؛ روش بازسازی:
[data/README.md](data/README.md). ادعای تطابق حرف‌به‌حرف با نسخهٔ چاپی خاصی
مطرح نیست و نسخهٔ مرجع قابل جایگزینی است.

## آزمون‌ها

```bash
python -m pytest tests -q
python scripts/check_repo_hygiene.py
```

۵۰ آزمون شامل نرمال‌سازی، ریشه، آیات، گزارش UTF-8، ربات، webhook و خطاها.
اگر `data/quran.db` نباشد، آزمون‌های داده‌محور **skip** می‌شوند (skip ≠ pass)؛
ابتدا `scripts/prepare_data.py`. CI روی Python 3.10/3.12:
`.github/workflows/ci.yml`.

## استقرار

- محلی: `python app.py` (polling)
- میزبانی سبک: `python server.py` (webhook) — راهنمای Render:
  [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## مستندات

| سند | محتوا |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | جریان درخواست، مدل داده، هم‌ترازی |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | webhook، Render، متغیرها |
| [docs/AI_HARNESS.md](docs/AI_HARNESS.md) | کار بهینه با عامل هوش مصنوعی |
| [AGENTS.md](AGENTS.md) | دستورها و قواعد عامل |

## امنیت و محدودیت‌ها

- توکن فقط در محیط/`.env`؛ `.env` در `.gitignore` است.
- دقت ریشه به Corpus وابسته است؛ گزارش جایگزین تفسیر نیست.
- گزارش آسیب‌پذیری: [SECURITY.md](SECURITY.md).

## مشارکت و مجوز

[CONTRIBUTING.md](CONTRIBUTING.md) و [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
کد با [MIT](LICENSE) منتشر می‌شود؛ داده‌ها مجوز مستقل دارند. سپاس از Tanzil،
Quranic Arabic Corpus و [python-bale-bot](https://github.com/python-bale-bot/python-bale-bot).
