"""نگاشت Buckwalter ↔ عربی، مبتنی بر داده‌های رسمی Quranic Arabic Corpus.

این نگاشت natively از داده واقعی در scripts/derive_buckwalter.py استخراج و
تأیید شده است — هر نویسه از فایل رسمی morphology-0.4 به یک نویسه مشخص عربی
در متن Uthmani Tanzil نگاشت می‌شود (صدها تا صدهاها مشاهده، بدون تضاد).
"""
_buck_to_ar = {
    "'": "\u0621",   # ء
    ">": "\u0623",   # أ
    "<": "\u0625",   # إ
    "&": "\u0624",   # ؤ
    "}": "\u0626",   # ئ  (تمایز شده در داده رسمی)
    "A": "\u0627",   # ا
    "b": "\u0628",   # ب
    "t": "\u062A",   # ت
    "v": "\u062B",   # ث
    "j": "\u062C",   # ج
    "H": "\u062D",   # ح
    "x": "\u062E",   # خ
    "d": "\u062F",   # د
    "*": "\u0630",   # ذ
    "r": "\u0631",   # ر
    "z": "\u0632",   # ز
    "s": "\u0633",   # س
    "$": "\u0634",   # ش
    "S": "\u0635",   # ص
    "D": "\u0636",   # ض
    "T": "\u0637",   # ط
    "Z": "\u0638",   # ظ
    "E": "\u0639",   # ع
    "g": "\u063A",   # غ
    "f": "\u0641",   # ف
    "q": "\u0642",   # ق
    "k": "\u0643",   # ك
    "l": "\u0644",   # ل
    "m": "\u0645",   # م
    "n": "\u0646",   # ن
    "h": "\u0647",   # ه
    "w": "\u0648",   # و
    "y": "\u064A",   # ي
    "Y": "\u0649",   # ى
    "p": "\u0629",   # ة
    "{": "\u0671",   # ٱ
    "_": "\u0640",   # ـ (tatweel)
    "~": "\u0651",   # ّ shadda
    "^": "\u0653",   # ٓ maddah above
    "#": "\u0654",   # ٔ hamza above
    "F": "\u064B",   # ً tanween fath
    "N": "\u064C",   # ٌ tanween damm
    "K": "\u064D",   # ٍ tanween kasr
    "a": "\u064E",   # َ fath
    "u": "\u064F",   # ُ damm
    "i": "\u0650",   # ِ kasr
    "o": "\u0652",   # ْ sukun
    "`": "\u0670",   # ٰ superscript alef
    ",": "\u06E5",   # ۢ small waw
    ".": "\u06E6",   # ۦ small yeh
    "@": "\u06DF",   # ۟ small high rounded zero
    '"': "\u06E0",   # ۠ empty centre low stop
    "[": "\u06E2",   # ۢ small meem isolated
    ";": "\u06E3",   # ۣ small low meem
    "]": "\u06ED",   # ۭ rounded head-stroke
    ":": "\u06DC",   # ۜ small high meem with dot
    "%": "\u06EC",   # ۬ rounded head-stroke of sup alef
    "+": "\u06EB",   # ۫ empty centre high stop
    "-": "\u06EA",   # ۪ empty centre low stop
}


def buckwalter_to_arabic(text: str) -> str:
    """تبدیل متن Buckwalter (کوپرس رسمی) به عربی با اعراب کامل."""
    return "".join(_buck_to_ar.get(ch, ch) for ch in text)


# نگاشت حروف عربی به Buckwalter (برای عیب‌یابی و نمایش در برخی گزارش‌ها)
AR_TO_BUCK = {v: k for k, v in _buck_to_ar.items() if k != " "}


def arabic_to_buckwalter(text: str) -> str:
    return "".join(AR_TO_BUCK.get(ch, ch) for ch in text)
