# استقرار QuranA

دو حالت اجرا وجود دارد: polling محلی (`app.py`) و webhook برای میزبانی
(`server.py`). برای اجرای محلی فقط بخش اول README کافی است؛ این سند مخصوص
استقرار است.

## متغیرهای محیطی

| متغیر | الزامی | توضیح |
|---|---|---|
| `BALE_TOKEN` | بله | توکن ربات بله؛ فقط در `.env` یا متغیرهای محیطی میزبان |
| `WEBHOOK_SECRET` | توصیه‌شده | بخش مخفی مسیر webhook؛ بدون آن مسیر قابل حدس است |
| `PUBLIC_BASE_URL` | خیر | آدرس عمومی سرویس؛ روی Render از `RENDER_EXTERNAL_URL` خوانده می‌شود |
| `PORT` | خیر | پورت سرور webhook؛ پیش‌فرض ۸۰۸۰ (Render خودش مقدار می‌دهد) |

هرگز توکن را در Issue، PR، اسکرین‌شات یا کد قرار ندهید. `.env` در `.gitignore` است.

## حالت webhook (Render رایگان)

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

## دیتابیس در استقرار

`data/quran.db` در گیت نیست؛ `render.yaml` آن را در مرحلهٔ build با
`scripts/download_data.py` و `scripts/prepare_data.py` می‌سازد. اگر build به
شبکه دسترسی نداشت، دیتابیس را با `git add -f data/quran.db` کامیت کنید
(به یاد داشته باشید که داده‌های صرفی GPL هستند؛ `THIRD_PARTY_NOTICES.md`).

## حالت polling محلی

```bash
python app.py
```

حلقهٔ `getUpdates` هر ۳۰ ثانیه اجرا می‌شود. برای توقف `Ctrl+C`. اگر ربات روی
webhook تنظیم شده باشد، ابتدا با `scripts/set_webhook.py --delete` آن را بردارید.

## عیب‌یابی دیپلوی خودکار

اگر با وجود `Auto-Deploy = On Commit`، commit جدید در تب **Events** رندر دیده
نمی‌شود:

1. در **Settings → Build → Source** مخزن و برنچ `main` را دوباره تأیید کنید و
   **Git Credentials → Use My Credentials** را بزنید.
2. در GitHub، بخش **Settings → Applications → Installed GitHub Apps** مطمئن
   شوید اپ Render نصب است و مخزن QuranA در دسترسی آن قرار دارد.
3. یک‌بار **Manual Deploy → Deploy latest commit** بزنید تا سرویس همگام شود.
4. اگر همچنان خودکار نشد، از **Deploy Hook** رندر به‌همراه GitHub Actions
   استفاده کنید (Secret با نام `RENDER_DEPLOY_HOOK`) و Auto-Deploy رندر را
   خاموش کنید تا دیپلوی دوتایی رخ ندهد.

پس از هر دیپلوی، نسخهٔ زنده را از `/healthz` بررسی کنید؛ مقدار `version` باید با
`APP_VERSION` در `config.py` یکی باشد.
