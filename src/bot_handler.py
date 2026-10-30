"""مدیریت درخواست‌های کاربر ربات: دریافت کلمه، رفع ابهام ریشه، تولید و ارسال فایل.

نکته‌های هم‌زمانی:
  - وضعیت هر chat_id در یک دیکشنری نگه‌داری می‌شود (انتخاب ریشه مبهم).
  - پیام‌ها به‌صورت متوالی پردازش می‌شوند (درخواست هم‌زمان صف می‌شود).
  - پس از پایان هر پردازش، وضعیت پاک می‌شود تا نتیجه دوباره ارسال نشود.
  - نتیجه هر update_id فقط یک‌بار پردازش می‌شود (با offset در BaleClient).
"""
import logging
import threading
from pathlib import Path

from .search_service import search_root
from .report_generator import generate_report
from .text_normalizer import normalize_word, normalize_arabic, valid_word, detect_script
log = logging.getLogger(__name__)

MSG_START = (
    "سلام! من QuranA (قرآنا) هستم.\n"
    "کلمه موردنظرت را بفرست تا واژه‌های هم‌ریشه آن را در قرآن کریم بررسی کنم "
    "و آیات مرتبط را در قالب فایل متنی برایت بفرستم.\n"
    "مثال: علم / كتاب / سجد"
)
MSG_PROCESSING = "در حال بررسی ریشه صرفی و استخراج آیات قرآن هستم. لطفاً کمی صبر کن."
MSG_EMPTY = "پیام شما خالی بود. لطفاً یک واژه ارسال کنید."
MSG_MULTI_WORDS = "لطفاً فقط یک واژه ارسال کنید، نه جمله یا چند کلمه."
MSG_INVALID_CHAR = "ورودی باید فقط حروف عربی/فارسی باشد (بدون اعداد یا حروف لاتین)."
MSG_NOT_FOUND = "این واژه در داده صرفی قرآن یافت نشد. صورت عربی و املای دشوار در آیه‌ها را کنترل کنید."
MSG_PERSIAN_LETTER = "صورت عربی کلمه را ارسال کنید (مثلاً به‌جای «پک وید»، واژه عربی معادل)."
MSG_DATA_MISSING = "پایگاه داده صرفی آماده نیست. لطفاً ابتدا scripts/prepare_data.py را اجرا کنید."
MSG_SEND_FAILED = "ارسال فایل به بله با خطا مواجه شد: {err}"


class BotHandler:
    def __init__(self, client, repo, out_dir=None):
        self.client = client
        self.repo = repo
        self.out_dir = out_dir          # پوشه گزارش‌ها (برای آزمون‌ها متمایز می‌شود)
        self.lock = threading.Lock()
        # chat_id -> dict(state='choose-root', options=[...], word=, normalized=)
        self.pending = {}

    # ---------- پردازش پیام‌ها (متوالی) ----------
    def handle_update(self, chat_id, message_id, text: str):
        with self.lock:
            try:
                self._handle(chat_id, message_id, text)
            except Exception as exc:
                log.exception("خطا در پردازش پیام: %s", exc)
                try:
                    self.client.send_message(chat_id, f"خطای داخلی در پردازش: {exc}")
                except Exception:
                    pass

    def _handle(self, chat_id, message_id, text: str):
        # 1) /start
        if text.startswith("/start"):
            self.client.send_message(chat_id, MSG_START)
            return

        # 2) اگر کاربر در مرحله یش ریشه است
        state = self.pending.get(chat_id)
        if state and state.get("state") == "choose-root" and text.strip().isdigit():
            self._pick_root(chat_id, message_id, text.strip())
            return

        # واژه ورودی جدید: حالت قبلی (انتخاب ریشه) را پاک می‌کند
        self.pending.pop(chat_id, None)
        if not text.strip():
            self.client.send_message(chat_id, MSG_EMPTY)
            return
        if len(text.split()) > 1:
            self.client.send_message(chat_id, MSG_MULTI_WORDS)
            return
        if not valid_word(text):
            self.client.send_message(chat_id, MSG_INVALID_CHAR)
            return
        script = detect_script(text)
        if script == "persian-only-letters":
            self.client.send_message(chat_id, MSG_PERSIAN_LETTER)
            return

        normalized = normalize_word(text)
        if not normalized:
            self.client.send_message(chat_id, MSG_EMPTY)
            return

        self.client.send_message(chat_id, MSG_PROCESSING)

        # رفع ابهام ریشه
        from .morphology import resolve_roots
        res = resolve_roots(text, normalized, self.repo)
        if res.ambiguity:
            self._offer_root_options(chat_id, text, normalized, res)
            return
        if not res.ok:
            self.client.send_message(chat_id, MSG_NOT_FOUND)
            return
        self._dispatch_root(chat_id, message_id, res.root, text, normalized)

    # ---------- ابهام ----------
    def _offer_root_options(self, chat_id, word, normalized, res):
        self.client.send_message(chat_id, "این واژه چند ریشه محتمل دارد. شماره ریشه موردنظر را بفرست:")
        opts = res.options
        lines = []
        for i, o in enumerate(opts, start=1):
            samples = "، ".join(o.sample_words[:4])
            lines.append(f"{i}. ریشه «{o.root}» — {o.occurrence_count} رخداد — نمونه: {samples}")
        lines.append("شماره گزینه موردنظر را بفرستید.")
        self.client.send_message(chat_id, "\n".join(lines))
        self.pending[chat_id] = {"state": "choose-root",
                                 "options": [o.root for o in opts],
                                 "word": word,
                                 "normalized": normalized}

    def _pick_root(self, chat_id, message_id, pick: str):
        state = self.pending.get(chat_id)
        idx = int(pick) - 1
        if not state or idx < 0 or idx >= len(state["options"]):
            self.client.send_message(chat_id, "شماره ریشه نامعتبر است. دوباره تلاش کنید یا واژه دیگری بفرستید.")
            return
        root = state["options"][idx]
        word = state["word"]
        normalized = state["normalized"]
        self.pending.pop(chat_id, None)
        self._dispatch_root(chat_id, message_id, root, word, normalized)

    # ---------- نتیجه ----------
    def _dispatch_root(self, chat_id, message_id, root, word, normalized):
        result = search_root(root, self.repo)
        log.info("search root %s => %s ayat", root, result["unique_ayahs"])
        if result["unique_ayahs"] == 0:
            self.client.send_message(chat_id, "این ریشه در داده صرفی قرآن یافت نشد.")
            return
        path: Path = generate_report(root, word, normalized, result, self.repo, out_dir=self.out_dir)
        try:
            self.client.send_document(
                chat_id, path,
                caption=f"QuranA — گزارش واژه‌های هم‌ریشه «{root}» در قرآن کریم — "
                        f"{result['distinct_word_forms']} واژه، "
                        f"{result['unique_ayahs']} آیه.")
        except Exception as exc:
            log.exception("ارسال فایل شکست خورد")
            self.client.send_message(chat_id, MSG_SEND_FAILED.format(err=exc))
