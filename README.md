# QuranA (قرآنا)

[![CI](https://github.com/MRGD313/QuranA/actions/workflows/ci.yml/badge.svg)](https://github.com/MRGD313/QuranA/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![release](https://img.shields.io/badge/release-v0.1.0-orange.svg)](https://github.com/MRGD313/QuranA/releases/tag/v0.1.0)

ربات پیام‌رسان بله برای استخراج **واژه‌های هم‌ریشه** در قرآن کریم.
یک واژه می‌فرستید؛ QuranA ریشه صرفی آن را پیدا می‌کند، همه واژه‌های قرآنی
هم‌ریشه را از داده رسمی Quranic Arabic Corpus استخراج می‌کند، متن کامل آیات را
از متن مرجع Tanzil می‌خواند و گزارش را در قالب فایل `.txt` (UTF-8) در همان
گفت‌وگو می‌فرستد.

> وضعیت: نسخه ۰.۱.۰ (بتا) — هسته و آزمون‌ها پایدارند؛ رابط ربات ساده و قابل توسعه است.

## ویژگی‌ها

- تشخیص ریشه بر پایه تحلیل صرفی رسمی (نه شباهت رشته‌ای یا حدس مدل زبانی).
- پوشش فعل ماضی/مضارع/امر، اسم، مصدر، صفت و مشتقات، همراه پیشوند/پسوند.
- رفع ابهام: اگر واژه چند ریشه محتمل داشته باشد، فهرست شماره‌دار نمایش داده
  می‌شود و کاربر خودش ریشه را انتخاب می‌کند.
- اتصال رخدادها به متن کامل آیه با نام سوره و شماره آیه؛ حذف تکرار آیه و
  مرتب‌سازی بر اساس سوره و آیه.
- آمار تفکیک‌شده: تعداد واژه‌های متمایز، تعداد رخدادهای واژگانی، تعداد آیات یکتا.
- گزارش UTF-8 با ذکر منبع، نسخه داده، ریشه و محدودیت‌ها.
- پردازش متوالی درخواست‌ها، جداسازی گفت‌وگوها و مدیریت خطای ارسال فایل.
- بدون وابستگی سنگین: فقط `requests` و `python-dotenv` (و `pytest` برای آزمون).

مستندات بیشتر: [معماری و تصمیم‌های طراحی](docs/ARCHITECTURE.md) و
[داده‌ها و مجوزها](data/README.md).

## معماری

```
app.py                     حلقهٔ polling بله (اجرای محلی)
server.py                  سرور webhook برای استقرار تریگری (Render رایگان)
config.py                  تنظیمات و مسیرها
src/
  bale_api.py              کلاینت HTTP برای API بله
  bot_handler.py           منطق گفت‌وگو، رفع ابهام، ارسال فایل
  text_normalizer.py       نرمال‌سازی عربی/فارسی (بدون تغییر متن اصلی)
  buckwalter.py            نگاشت Buckwalter ↔ عربی
  morphology.py            تشخیص ریشه و گزینه‌های محتمل
  quran_repository.py      دسترسی به متن و داده صرفی (SQLite)
  search_service.py        استخراج رخدادها و آیات یکتا
  report_generator.py      تولید گزارش متنی
scripts/
  download_data.py         دریافت منابع رسمی
  prepare_data.py          ساخت data/quran.db
  validate_data.py         اعتبارسنجی داده‌ها
  check_repo_hygiene.py    بررسی نبود توکن/رمز در مخزن
  run_core_e2e.py          آزمون سرتاسری هسته بدون شبکه
  live_bale_test.py        آزمون اتصال واقعی بله (نیازمند توکن)
  set_webhook.py           ثبت/حذف/بررسی webhook بله
  derive_buckwalter.py     استخراج و اثبات نگاشت نویسه‌ای از داده واقعی
  find_ambiguous.py        فهرست واژه‌های چندریشه (پژوهشی)
  show_ayah.py             نمایش یک آیه از پایگاه داده
render.yaml                تعریف دیپلوی رایگان روی Render
docs/ARCHITECTURE.md       توضیح معماری و تصمیم‌های طراحی
tests/                     آزمون‌های pytest
data/raw/                  داده‌های رسمی دانلودشده (در گیت نیست)
data/quran.db              پایگاه داده محلی (در گیت نیست)
data/reports/              گزارش‌های تولیدی (در گیت نیست)
```

## داده‌های مرجع

متن قرآن و داده صرفی دو منبع مستقل هستند و هرگز در هم ادغام یا بازنویسی نمی‌شوند.

| نقش | منبع | نسخه | شرایط استفاده |
|---|---|---|---|
| متن Uthmani قرآن | [Tanzil](https://tanzil.net/download/) | 1.1 (۲۰۲۱) | کپی verbatim با ذکر منبع؛ تغییر متن ممنوع |
| تحلیل صرفی (ریشه/مدخل) | [Quranic Arabic Corpus](https://corpus.quran.com/download) | 0.4 | GNU GPL؛ تغییر داده ممنوع |
| نام سوره و شمار آیات | [Tanzil Metadata](http://tanzil.net/res/text/metadata/quran-data.xml) | 1.0 | CC BY |

این فایل‌ها همراه مخزن منتشر نمی‌شوند. با `scripts/download_data.py` از منبع
رسمی دریافت و با `scripts/prepare_data.py` به `data/quran.db` تبدیل می‌شوند.
جزئیات مجوزها: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

### اعتبارسنجی انجام‌شده

- ۶۲۳۶ آیه و ۱۱۴ سوره؛ تعداد آیات هر سوره با متادیتای رسمی مقایسه شد.
- ۷۷٬۴۲۹ واژه، ۱۲۸٬۲۱۹ سگمنت صرفی، ۱٬۶۴۲ ریشه.
- تراز آیه‌به‌آیه بین متن مرجع و داده صرفی؛ اختلاف‌های نویسه‌ای شناخته‌شده
  (مستند در changelog منبع) شمارش و مستند شدند. ۵ واژهٔ متأثر از تغییر
  توکن‌بندی نسخه ۱.۱ با هم‌ترازی LCS مدیریت می‌شوند.
- پوشش ریشه در سگمنت‌های اسم/فعل/صفت بررسی شد (فعل ۱۰۰٪، صفت ۹۹.۹۵٪، اسم ۹۸.۵٪).

> **محدودیت صریح:** ادعا نمی‌کنیم متن، حرف‌به‌حرف با نسخهٔ چاپی رایج در ایران
> یکسان است. نسخهٔ مرجع Uthmani Tanzil 1.1 است. برای جایگزینی، فقط
> `data/raw/quran-uthmani.txt` را با قالب `سوره|آیه|متن` عوض کنید و
> `prepare_data.py` را دوباره اجرا کنید.

## پیش‌نیازها

- Python 3.10 یا جدیدتر
- اینترنت برای دریافت یک‌بارهٔ داده‌ها
- توکن ربات بله (از BotFather در ble.ir)
- ویندوز، لینوکس یا مک

## راه‌اندازی

### ویندوز (PowerShell)

```powershell
git clone https://github.com/MRGD313/QuranA.git
Set-Location QuranA

py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt pytest

Copy-Item .env.example .env
notepad .env    # مقدار BALE_TOKEN را وارد کنید

.\.venv\Scripts\python scripts\download_data.py
.\.venv\Scripts\python scripts\prepare_data.py
.\.venv\Scripts\python scripts\validate_data.py

.\.venv\Scripts\python app.py
```

### لینوکس / مک

```bash
git clone https://github.com/MRGD313/QuranA.git
cd QuranA

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest

cp .env.example .env
# BALE_TOKEN را در .env ویرایش کنید

python scripts/download_data.py
python scripts/prepare_data.py
python scripts/validate_data.py

python app.py
```

### متغیرهای محیطی

| متغیر | الزامی | توضیح |
|---|---|---|
| `BALE_TOKEN` | بله | توکن ربات بله؛ فقط در `.env` یا متغیرهای محیطی میزبان |
| `WEBHOOK_SECRET` | توصیه‌شده | بخش مخفی مسیر webhook؛ بدون آن مسیر قابل حدس است |
| `PUBLIC_BASE_URL` | خیر | آدرس عمومی سرویس؛ روی Render از `RENDER_EXTERNAL_URL` خوانده می‌شود |
| `PORT` | خیر | پورت سرور webhook؛ پیش‌فرض ۸۰۸۰ (Render خودش مقدار می‌دهد) |

`.env` در `.gitignore` است. هرگز توکن را در Issue، PR، اسکرین‌شات یا کد قرار ندهید.

## استفاده

1. در بله به ربات خود پیام `/start` بدهید.
2. یک واژهٔ عربی بفرستید؛ مثلاً `علم`، `كتاب`، `سَجَدَ`.
3. اگر واژه چند ریشهٔ محتمل داشته باشد، شمارهٔ ریشهٔ موردنظر را بفرستید.
4. فایل گزارش با نام `quran_roots_<ریشه>_<تاریخ>.txt` دریافت می‌شود.

آزمون سریع هسته بدون شبکه و بدون توکن:

```bash
python scripts/run_core_e2e.py سَجَدَ
```

نتیجه در `data/reports/` ذخیره می‌شود.

## آزمون‌ها

```bash
python -m pytest tests -q
```

بیش از ۴۰ آزمون شامل نرمال‌سازی عربی/فارسی، اعتبار ورودی، نگاشت Buckwalter، تشخیص
ریشه، نمایش ابهام، بازیابی آیات، حذف تکرار، مرتب‌سازی، حفظ متن عربی، خروجی
UTF-8، خطای ارسال سند، جداسازی کاربران، نبود توکن و لایهٔ webhook (مسیر مخفی،
ضد تکرار، سلامت).

CI در `.github/workflows/ci.yml` داده‌های رسمی را دانلود می‌کند، پایگاه داده را
می‌سازد، اعتبارسنجی می‌کند و آزمون‌ها را روی Python 3.10 و 3.12 اجرا می‌کند.

### آزمون اتصال واقعی بله

```bash
# فقط بررسی اتصال (getMe)
python scripts/live_bale_test.py

# پاسخ به پیام‌های موجود و ارسال یک فایل گزارش واقعی
python scripts/live_bale_test.py --send
```

این آزمون به `BALE_TOKEN` نیاز دارد و توکن را چاپ نمی‌کند. در جریان توسعهٔ
نسخهٔ ۰.۱.۰، اتصال `getMe` و ارسال واقعی سند (`sendDocument`) با موفقیت اجرا شد.

## استقرار رایگان با webhook (Render)

به‌جای اجرای ۲۴/۷، ربات با هر پیام بیدار می‌شود:

```text
بله ──POST──▶ https://<app>.onrender.com/hook/<secret> ──▶ server.py ──▶ پاسخ
```

- سرویس رایگان Render بعد از ۱۵ دقیقه بی‌ترافیک می‌خوابد و با اولین درخواست
  بیدار می‌شود؛ در این معماری همان پیام کاربر درخواست بیدارکننده است.
- اولین پاسخ بعد از یک دورهٔ سکوت حدود ۳۰ تا ۶۰ ثانیه (گاهی بیشتر) طول می‌کشد.
  این موضوع در پیام `/start` به کاربر اطلاع داده می‌شود.
- بله پیام‌ها را تا ۲۴ ساعت نگه می‌دارد؛ اگر سرویس خواب باشد پیام از دست نمی‌رود.
- هر `update_id` فقط یک‌بار پردازش می‌شود، پس تلاش مجدد بله پاسخ تکراری نمی‌سازد.
- اگر جلسهٔ انتخاب ریشه با خوابیدن سرویس از بین برود، کاربر پیام راهنمای
  «جلسه منقضی شده» می‌گیرد و باید واژه را دوباره بفرستد.

### با Blueprint

1. مخزن را در Render به‌صورت Blueprint وصل کنید (`render.yaml`).
2. مقدار `BALE_TOKEN` را در پنل وارد کنید؛ `WEBHOOK_SECRET` خودکار ساخته می‌شود.
3. پس از دیپلوی، `https://<app>.onrender.com/healthz` باید `{"ok": true, ...}` بدهد.
4. آدرس webhook هنگام بالا آمدن خودکار ثبت می‌شود (از `RENDER_EXTERNAL_URL`).

### دستی

```bash
python scripts/set_webhook.py --info
python scripts/set_webhook.py --url https://your-app.onrender.com
python scripts/set_webhook.py --delete   # بازگشت به polling
```

`python app.py` برای اجرای محلی است. اگر webhook فعال باشد، هشدار می‌دهد و
متوقف می‌شود تا اشتباهی سرویس production را از کار نیندازد؛ در آن حالت
`python app.py --force` یا `python scripts/set_webhook.py --delete` بزنید.

### یادداشت دربارهٔ دیتابیس

`data/quran.db` در گیت نیست؛ `render.yaml` آن را در مرحلهٔ build با
`scripts/download_data.py` و `scripts/prepare_data.py` می‌سازد. اگر build به
شبکه دسترسی نداشت، دیتابیس را با `git add -f data/quran.db` کامیت کنید.

## امنیت

- توکن فقط از `BALE_TOKEN` خوانده می‌شود.
- `scripts/check_repo_hygiene.py` الگوهای شبیه توکن را در فایل‌های مخزن بررسی می‌کند.
- گزارش‌ها در `data/reports/` می‌مانند و در گیت نیستند.
- برای گزارش آسیب‌پذیری: [SECURITY.md](SECURITY.md).

## محدودیت‌ها

- دقت ریشه‌ها به داده Quranic Arabic Corpus وابسته است؛ این پروژه خودش تحلیل
  صرفی جدید تولید نمی‌کند.
- واژه‌های با حروف اختصاصی فارسی (پ، چ، ژ، گ) به صورت عربی پذیرفته نمی‌شوند و
  کاربر به ارسال صورت عربی راهنمایی می‌شود.
- متن مرجع قابل جایگزینی است؛ تطبیق با نسخهٔ چاپی خاص باید مستند شود.
- گزارش، جایگزین تفسیر یا پژوهش تخصصی نیست.

## نقشه راه

- [ ] افزودن گزینهٔ نمایش ترجمهٔ فارسی آیات (منبع دارای مجوز)
- [ ] خروجی PDF در کنار TXT
- [ ] کش پاسخ‌ها برای ریشه‌های پرتکرار
- [x] حالت وب‌هوک برای استقرار سبک (Render رایگان)
- [ ] سنجش دقت با مجموعهٔ آزمون طلایی

## مشارکت

پیشنهادها و PRها خوش‌آمدند. لطفاً [CONTRIBUTING.md](CONTRIBUTING.md) و
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) را بخوانید.

## مجوز

کد این پروژه با [MIT License](LICENSE) منتشر می‌شود. داده‌های قرآن و صرف
دارای مجوز مستقل خود هستند و در مخزن نیستند؛ [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## سپاسگزاری

- [Tanzil Project](https://tanzil.net/) برای متن قرآن و متادیتا.
- [Quranic Arabic Corpus](https://corpus.quran.com/) (Kais Dukes) برای تحلیل صرفی.
- تیم [python-bale-bot](https://github.com/python-bale-bot/python-bale-bot) برای مستندسازی عملی API بله.

---

## English overview

QuranA (قرآنا) is an open-source Bale messenger bot. Given an Arabic word, it
resolves the word's root using the Quranic Arabic Corpus, collects all Quranic
words sharing that root, retrieves the full verses from Tanzil's Uthmani text,
and sends a UTF-8 text report. Reference datasets are downloaded from their
official sources at setup time and are not redistributed in this repository.
Licensed under MIT; third-party data has its own terms (see
THIRD_PARTY_NOTICES.md).
