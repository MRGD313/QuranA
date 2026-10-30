"""نرمال‌سازی متن عربی و فارسی برای جست‌وجوی مطمئن ریشه.

متن اصلی قرآن هرگز تغییر نکرده و ذخیره نمی‌شود؛ این ماژول فقط برای مقایسه
و جست‌وجوی واژه به‌کار می‌رفته و نسخه نرمال‌شده جداگانه تولید می‌کند.
"""
import re
import unicodedata

# نشانه‌های اعراب و علائم قرآنی كه باید برای جست‌وجو حذف شوند
_DIACRITICS = re.compile(
    "[\u064B-\u0655"      # اعراب استاندارد + maddah/hamza above/below
    "\u0640"              # ـ tatweel
    "\u0656-\u065F"       # علائم دیگر
    "\u06D6-\u06ED"       # علائم قرآنی (small stops, rub signs)
    "\u06DF-\u06E8"
    "\u06E9\u06EA\u06EB\u06EC\u06ED"
    "]+"
)

_CHAR_MAP = {
    "\u0623": "\u0627",  # أ -> ا
    "\u0625": "\u0627",  # إ -> ا
    "\u0622": "\u0627",  # آ -> ا
    "\u0624": "\u0648",  # ؤ -> و
    "\u0626": "\u064A",  # ئ -> ي
    "\u0be3": "\u0627",
    "\u0671": "\u0627",  # ٱ -> ا (استاندارد قرآنی)
    "\u0670": "\u0627",  # ٰ (superscript alef) نماینده حرف الف است
    "\u0629": "\u0647",  # ة -> ه
    "\u0649": "\u064A",  # ى -> ي
    "\u06CC": "\u064A",  # ی فارسی -> ي
    "\u06A9": "\u0643",  # ک فارسی -> ك
    "\u200C": "",        # ZWNJ فارسی
}

_ARABIC_LETTERS = re.compile(r"[\u0600-\u07FF]")


def strip_diacritics(text: str) -> str:
    return _DIACRITICS.sub("", text)


def normalize_arabic(text: str) -> str:
    """نرمال‌سازی برای مطابقت واژه‌های قرآن: حذف اعراب و استانداردسازی متغیرها."""
    t = text
    for src, dst in _CHAR_MAP.items():
        t = t.replace(src, dst)
    t = strip_diacritics(t)
    t = unicodedata.normalize("NFC", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_word(input_text: str) -> str:
    """نرمال‌سازی واژه ورودی کاربر (عربی/فارسی)."""
    return normalize_arabic(input_text)


def detect_script(word: str) -> str:
    """تشخیص اینکه ورودی را میتوان پیش از تطبیق، عربی معتبر در نظر گرفت یا نه."""
    if not word:
        return ""
    if not _ARABIC_LETTERS.search(word):
        return "non-arabic"
    # حروف اختصاصی فارسی که عربی معتبر نیستند
    persian_exclusive = set("\u067E\u0686\u0698\u06AF\u06CC\u06A9\u0654\u062F\u062F")
    if any(ch in persian_exclusive for ch in word if ch in "\u067E\u0686\u0698\u06AF"):
        return "persian-only-letters"
    return "arabic-fa-compatible"


def valid_word(text: str) -> bool:
    """اعتبار واژه ورودی: فقط یک واژه و فقط حروف عربی/فارسی مجاز."""
    if not text:
        return False
    if not _ARABIC_LETTERS.search(text):
        return False
    # نباید حروف لاتین یا ارقام داشته باشد
    if re.search(r"[A-Za-z0-9\u0020\u0040]", text.replace(" ", "")):
        return False
    words = text.split()
    if len(words) > 1:
        return False
    return True
