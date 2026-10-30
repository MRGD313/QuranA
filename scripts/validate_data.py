"""بررسی صحت و کامل بودن پایگاه داده quran.db (متن قرآن + تحلیل صرفی)."""
import sqlite3
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.text_normalizer import normalize_arabic

RAW = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "quran.db"

problems = []


def _cfg_stdout():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def check(cond, msg):
    if not cond:
        problems.append(msg)
    return cond


def _eq(a, b):
    from src.text_normalizer import normalize_arabic
    return normalize_arabic(a) == normalize_arabic(b)


def main():
    _cfg_stdout()
    if not DB_PATH.exists():
        print("❌ quran.db موجود نیست. ابتدا scripts/prepare_data.py")
        sys.exit(2)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # --- ۱) ساختار مصحف ---
    ayat_count = conn.execute("SELECT COUNT(*) FROM ayat").fetchone()[0]
    check(ayat_count == 6236, f"تعداد آیات {ayat_count} ≠ 6236")

    surahs = {r["index_"]: r for r in conn.execute("SELECT * FROM surahs")}
    check(len(surahs) == 114, f"سوره‌ها {len(surahs)} ≠ 114")

    per = defaultdict(int)
    for (s, a) in conn.execute("SELECT surah, ayah FROM ayat"):
        per[s] += 1
    meta = {}
    for s in ET.parse(RAW / "quran-data.xml").getroot().find("suras"):
        meta[int(s.get("index"))] = int(s.get("ayas"))
    for no, cnt in meta.items():
        check(per.get(no, -1) == cnt, f"سوره {no}: آیات {per.get(no)} ≠ {cnt}")

    # --- ۲) پوشش صرفی ---
    segs = conn.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
    words = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    roots = conn.execute("SELECT COUNT(DISTINCT root) FROM segments WHERE root != ''").fetchone()[0]
    no_root = conn.execute("SELECT COUNT(*) FROM segments WHERE root = ''").fetchone()[0]
    # سگمنت‌های اسم و فعل باید تقریباً همگی ریشه داشته باشند؛
    # حروف جای‌نما (P, PRON, REL, DEM, ACC, ...) طبیعتاً ریشه ندارند.
    def stemmed_pos(pos):
        return (conn.execute("SELECT COUNT(*) FROM segments WHERE features LIKE 'STEM|POS:" + pos + "|%' AND root != ''").fetchone()[0],
                conn.execute("SELECT COUNT(*) FROM segments WHERE features LIKE 'STEM|POS:" + pos + "|%'").fetchone()[0])
    for pos in ("N", "V", "ADJ"):
        have, total = stemmed_pos(pos)
        share = have / max(total, 1)
        print(f"پوشش ریشه POS={pos}: {have}/{total} = {share:.2%}")
        check(share >= 0.98, f"پوشش ریشه برای POS={pos} کم است: {share:.2%}")
    print(f"words={words} segments={segs} roots={roots} without_root={no_root}")
    check(roots >= 1500, f"ریشه‌های متمایز کم‌اند: {roots}")

    # --- ۳) تطبیق نویسه‌ای واژه‌های بازگشایی‌شده با متن Tanzil ---
    # واژه‌های عربی بازگشایی شده از Buckwalter باید با توکن متن واقعی مطابقت داشته باشند
    mirror_mismatch = 0
    mirror_total = 0
    mismatch_samples = []
    for row in conn.execute("SELECT surah, ayah, text FROM ayat"):
        toks = row["text"].split()
        cw = conn.execute("SELECT word_pos, arabic FROM words WHERE surah=? AND ayah=? ORDER BY word_pos",
                          (row["surah"], row["ayah"])).fetchall()
        if len(toks) != len(cw):
            mirror_mismatch += 1
            continue
        for t, row2 in zip(toks, cw):
            mirror_total += 1
            if normalize_arabic(t) != normalize_arabic(row2["arabic"]):
                mirror_mismatch += 1
                if len(mismatch_samples) < 10:
                    mismatch_samples.append((row["surah"], row["ayah"], t, row2["arabic"]))
    print(f"جفت‌های تراز نویسه‌ای: {mirror_total}, ناسازگار: {mirror_mismatch}")
    for m in mismatch_samples:
        print("  ناسازگاری:", m)
    check(mirror_mismatch / max(mirror_total, 1) < 0.01, "میزان ناسازگاری واژه‌ای معمولی نیست")

    # --- ۴) نمونه‌های معروف ---
    q = conn.execute("SELECT text FROM ayat WHERE surah=2 AND ayah=255").fetchone()
    check(q is not None and "ٱللَّهُ" == "ٱللَّهُ" and any(_eq("ٱللَّهُ", w) for w in q["text"].split()),
          "آیه ۲:۲۵۵ فاقد واژه الله است (مشکل متن)")
    check(q is not None and any(_eq("ٱلْعَظِيمُ", w) for w in q["text"].split()),
          "آیه ۲:۲۵۵ فاقد ٱلْعَظِيمُ است")

    ayat_first = conn.execute("SELECT text FROM ayat WHERE surah=1 AND ayah=2").fetchone()
    check(ayat_first is not None and any(_eq("ٱلْحَمْدُ", w) for w in ayat_first["text"].split()),
          "آیه ۱:۲ فاقد الحَمْدُ است")

    # --- ۵) نمونهٔ ریشه علم ---
    occ = conn.execute("SELECT COUNT(*) FROM segments WHERE root = 'علم'").fetchone()[0]
    check(occ > 460, f"ریشه «علم» فقط {occ} رخداد دارد")
    print(f"ریخدادهای ریشه علم: {occ}")

    # --- ۶) واژه‌های بی‌ربْر و ناسازگار در word_counts متن vs corpus ---
    wordless = conn.execute("SELECT COUNT(*) FROM words WHERE norm=''").fetchone()[0]
    check(wordless == 0, f"واژه‌های با نرمال خالی: {wordless}")

    conn.close()
    print()
    if problems:
        print("❌ مشکلات یافت‌شده:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    else:
        print("✅ همه بررسی‌ها موفق بود.")


if __name__ == "__main__":
    main()
