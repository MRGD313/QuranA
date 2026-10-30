"""تولید فایل متنی گزارش واژه‌های هم‌ریشه (UTF-8، بدون بازنویسی متن آیات)."""
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

from config import QURAN_TEXT_SOURCE, MORPHOLOGY_SOURCE, REPORTS_DIR

TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))


def _line(char="=", width=60):
    return char * width


def _safe_filename(root: str) -> str:
    base = re.sub(r"[\\/:*?\"<>|\s]+", "_", root).strip("_")
    now = datetime.now(TEHRAN_TZ)
    stamp = now.strftime("%Y%m%d_%H%M%S")
    return f"quran_roots_{base}_{stamp}.txt"


def generate_report(root: str, input_word: str, normalized: str, result: dict,
                    repo, out_dir: Path = None) -> Path:
    """تولید کامل فایل گزارش. result خروجی search_service.search_root است."""
    out_dir = Path(out_dir) if out_dir else REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / _safe_filename(root)

    now = datetime.now(TEHRAN_TZ).strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    add = lines.append
    add(_line())
    add("گزارش واژه‌های هم‌ریشه در قرآن کریم — QuranA")
    add(_line())
    add("")
    add("کلمه ورودی:    " + input_word)
    add("صورت نرمال‌شده: " + normalized)
    add("ریشه تشخیص‌داده‌شده: " + root)
    add("وضعیت اطمینان تحلیل: ریشه بر اساس داده رسمی Quranic Arabic Corpus 0.4 استخراج شد.")
    add("منبع داده صرفی: " + MORPHOLOGY_SOURCE)
    add("نسخه متن قرآن: " + QURAN_TEXT_SOURCE)
    add("تاریخ تولید:   " + now)
    add("")
    add(_line("-"))
    add("بخش اول: فهرست واژه‌های هم‌ریشه")
    add(_line("-"))
    add("")
    forms = result.get("forms") or {}
    if not forms:
        add("واژه‌ای برای این ریشه یافت نشد.")
    for i, (key, info) in enumerate(sorted(forms.items(), key=lambda x: (-x[1]["count"], x[0][0])), start=1):
        arabic_word, norm = key
        vocalized = "، ".join(sorted(info.get("vocalized", []))) or "—"
        add(f"{pes_num(i)}. واژه: {arabic_word}")
        add(f"   صورت اعراب‌گذاری‌شده: {vocalized}")
        add(f"   صورت نرمال‌شده (برای جست‌وجو): {norm}")
        add(f"   نوع صرفی: {'، '.join(sorted(info['tags'])) or 'نامشخص'}")
        add(f"   تعداد رخداد: {info['count']}")
        add("")

    add(_line("-"))
    add("بخش دوم: آیات قرآن")
    add(_line("-"))
    add("")
    for group in result["ayat"]:
        name_ar, name_en = repo.surah_name(group.surah)
        add(f"[{name_ar} — سوره {group.surah}, آیه {group.ayah}]")
        add("")
        # متن عربی آیه عیناً از منبع مرجع، بدون هیچ تغییری
        add(group.text)
        add("")
        word_list = "؛ ".join(o.word_arabic for o in sorted(group.words, key=lambda o: o.word_pos))
        add("واژه یا واژه‌های هم‌ریشه موجود در آیه: " + word_list)
        add("ریشه صرفی: " + root)
        add("")
    add(_line("-"))
    add("آمار نهایی")
    add(_line("-"))
    add("")
    add(f"تعداد واژه‌های قرآنی متمایز: {result['distinct_word_forms']}")
    add(f"تعداد رخدادهای صرفی: {result['lexical_events']}")
    add(f"تعداد آیات یکتا: {result['unique_ayahs']}")
    add("")
    add(_line("-"))
    add("منابع و محدودیت‌ها")
    add(_line("-"))
    add("")
    add("منبع متن قرآن: " + QURAN_TEXT_SOURCE)
    add("نسخه یا شناسه انتشار: فایل رسمی قابل دانلود از tanzil.net (قابل بررسی و تکرار).")
    add("منبع داده صرفی: " + MORPHOLOGY_SOURCE + " — ریشهها بر اساس بررسی نویسه‌به‌نویسه تطبیق داده شدند.")
    add("محدودیت‌های احتمالی: در برخی آیه‌های ابتدایی سوره‌ها، بسم‌الله پیش‌آمده در متن جهت جست‌وجو حذف شده اما در نمایش متن آیات موجود است و بازنویسی نشده است.")
    add("تمام آیات به‌ترتیب و بدون تکرار از متن مرجع استخراج و در فایل گنجانده شده‌اند.")

    content = "\n".join(lines) + "\n"
    content = content.replace("\r\n", "\n")
    path.write_bytes(content.encode("utf-8"))
    return path


PES_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def pes_num(n: int) -> str:
    return "".join(PES_DIGITS[int(d)] for d in str(n))
