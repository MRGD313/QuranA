"""آماده‌سازی پایگاه داده quran.db از منابع رسمی:

- متن Uthmani قرآن: تحویل رسمی tanzil.net (نسخه 1.1) در data/raw/quran-uthmani.txt
- تحلیل صرفی: فایل رسمی Quranic Arabic Corpus 0.4 در data/raw/quranic-corpus-morphology-0.4.txt
- متادیتای سوره‌ها: داده رسمی tanzil.net در data/raw/quran-data.xml

مسیر یکپارچه‌سازی: هر واژه (corpus word) با token هم‌موقعیت در متن Tanzil تطبیق
داده می‌شود (بسم‌الله پیش‌آمده رسم اول هر سوره حذف می‌شود). برای مطابقت
نویسه‌ای، ارجاع در فایل‌های validate_data.py انجام می‌شود.
"""
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.buckwalter import buckwalter_to_arabic
from src.text_normalizer import normalize_arabic

RAW = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "quran.db"

BISM_TOKENS_NORM = ["بسم", "الله", "الرحمن", "الرحيم"]


def load_tanzil():
    ayat = {}
    with open(RAW / "quran-uthmani.txt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            s, a, text = line.split("|", 2)
            ayat[(int(s), int(a))] = text
    return ayat


def strip_leading_bism(surah, tokens):
    """بسم‌الله پیش‌آمده در اول سوره (به‌جز ۱ و ۹) را با تطبیق بدون اعراب حذف می‌کند."""
    if surah in (1, 9) or len(tokens) < 4:
        return tokens
    head4_norm = [normalize_arabic(t) for t in tokens[:4]]
    if head4_norm == BISM_TOKENS_NORM:
        return tokens[4:]
    return tokens


def load_morph():
    words = defaultdict(dict)  # (s,a) -> {w: [(seg, buck, tag, feats)]}
    with open(RAW / "quranic-corpus-morphology-0.4.txt", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or not line.startswith("("):
                continue
            m = re.match(r"\((\d+):(\d+):(\d+):(\d+)\)\t(.*)", line)
            if m:
                s, a, w, seg, rest = m.groups()
                parts = rest.split("\t")
                buck, tag, feats = parts[0], parts[1], parts[2] if len(parts) > 2 else ""
                words[(int(s), int(a))].setdefault(int(w), []).append((int(seg), buck, tag, feats))
    for key in words:
        words[key] = dict(words[key])
    return words


def parse_features(features: str):
    lemma_buck, root_buck = "", ""
    for part in features.split("|"):
        if part.startswith("LEM:"):
            lemma_buck = part[4:]
        elif part.startswith("ROOT:"):
            root_buck = part[5:]
    return lemma_buck, root_buck


def lcs_align(a_norms, b_norms):
    """پیدا کردن تراز بین دو فهرست نرمال‌شده با LCS. خروجی: دیکشنری i→j."""
    n, m = len(a_norms), len(b_norms)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if a_norms[i] == b_norms[j]:
                dp[i][j] = dp[i + 1][j + 1] + 1
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])
    alignment = {}
    i, j = 0, 0
    while i < n and j < m:
        if a_norms[i] == b_norms[j]:
            alignment[i] = j
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1
        else:
            j += 1
    return alignment


def build_alignment(surah, ayah, corpus_words, tanzil_tokens):
    """تراز واژه‌های corpus با توکن‌های متن مرجع.

    خروجی: دیکشنری word_pos → توکن مرجع (برای واژه‌هایی که موضع‌شان تأیید شد).
    در آیه‌های بدون اختلاف تعداد توکن، تراز مستقیم موقعیتی است.
    در آیه‌های دارای اختلاف نسخه (تغییرات ۱.۱)، تراز با LCS روی فرم نرمال انجام می‌شود.
    """
    if len(tanzil_tokens) == max(corpus_words or [0]):
        return {w: tanzil_tokens[w - 1] for w in corpus_words}
    # تراز با LCS روی فرمِ نرمال‌شده
    a_norms = [normalize_arabic(buckwalter_to_arabic("".join(b for (_seg, b, _tg, _f) in sorted(segs))))
               for _w, segs in sorted(corpus_words.items())]
    b_norms = [normalize_arabic(t) for t in tanzil_tokens]
    alignment = lcs_align(a_norms, b_norms)
    out = {}
    for i, w in enumerate(sorted(corpus_words.keys())):
        if i in alignment:
            out[w] = tanzil_tokens[alignment[i]]
    return out


def load_surah_metadata():
    tree = ET.parse(RAW / "quran-data.xml")
    suras = {}
    for s in tree.getroot().find("suras"):
        no = int(s.get("index"))
        suras[no] = {
            "ayas": int(s.get("ayas")),
            "name_ar": s.get("name"),
            "name_en": s.get("ename"),
            "tname": s.get("tname"),
            "type": s.get("type"),
        }
    return suras


def main():
    ayat_raw = load_tanzil()
    morph = load_morph()
    meta = load_surah_metadata()
    print(f"tanzil ayat: {len(ayat_raw)}  corpus ayat: {len(morph)}  metadata suras: {len(meta)}")

    # حذف بسم‌الله اول سوره از متن برای تراز
    ayat_tokens = {}
    ayat_text = {}
    for (s, a), text in ayat_raw.items():
        src_toks = text.split()
        toks = strip_leading_bism(s, src_toks)
        ayat_tokens[(s, a)] = toks
        ayat_text[(s, a)] = " ".join(toks)

    # DB
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
    CREATE TABLE surahs (index_ INTEGER PRIMARY KEY, ayas INTEGER, name_ar TEXT, name_en TEXT, tname TEXT, type TEXT);
    CREATE TABLE ayat (surah INTEGER, ayah INTEGER, text TEXT, PRIMARY KEY (surah, ayah));
    CREATE TABLE words (surah INTEGER, ayah INTEGER, word_pos INTEGER, buck TEXT, arabic TEXT, surface TEXT, norm TEXT, PRIMARY KEY (surah, ayah, word_pos));
    CREATE TABLE segments (
        surah INTEGER, ayah INTEGER, word_pos INTEGER, seg_pos INTEGER,
        buck TEXT, tag TEXT, lemma TEXT, lemma_norm TEXT, root TEXT, features TEXT,
        PRIMARY KEY (surah, ayah, word_pos, seg_pos));
    CREATE INDEX idx_words_norm ON words(norm);
    CREATE INDEX idx_segments_root ON segments(root);
    CREATE INDEX idx_segments_word ON segments(surah, ayah, word_pos);
    """)
    conn.executemany("INSERT INTO surahs VALUES (?,?,?,?,?,?)",
                     [(no, info["ayas"], info["name_ar"], info["name_en"], info["tname"], info["type"])
                      for no, info in meta.items()])
    conn.executemany("INSERT INTO ayat VALUES (?,?,?)",
                     [(s, a, t) for (s, a), t in sorted(ayat_text.items())])

    # گردآوری words و segments
    word_rows, seg_rows = [], []
    skipped_missing_text = 0
    unaligned_words = 0
    for (s, a) in sorted(morph.keys()):
        toks = ayat_tokens.get((s, a))
        if toks is None:
            skipped_missing_text += 1
            continue
        aligned = build_alignment(s, a, morph[(s, a)], toks)
        for w, segs in morph[(s, a)].items():
            if w > len(toks):
                print(f"  ⚠ واژه بیرون از متن: ({s}:{a}:{w})")
                continue
            buck_full = "".join(b for (_seg, b, _tag, _feats) in sorted(segs))
            arabic_full = buckwalter_to_arabic(buck_full)
            surface = aligned.get(w)
            if surface:
                norm_val = normalize_arabic(surface)
            else:
                unaligned_words += 1
                surface = None  # واژه بی‌تراز (اختلاف نسخه ۱.۱)؛ از فرم تحلیل صرفی استفاده می‌شود
                norm_val = normalize_arabic(arabic_full)
            word_rows.append((s, a, w, buck_full, arabic_full, surface, norm_val))
            for (seg, buck, tag, feats) in sorted(segs):
                lemma_b, root_b = parse_features(feats)
                lemma_ar = buckwalter_to_arabic(lemma_b) if lemma_b else ""
                root_ar = buckwalter_to_arabic(root_b) if root_b else ""
                seg_rows.append((s, a, w, seg, buck, tag, lemma_ar,
                                 normalize_arabic(lemma_ar), root_ar, feats))

    conn.executemany("INSERT INTO words VALUES (?,?,?,?,?,?,?)", word_rows)
    conn.executemany("INSERT INTO segments VALUES (?,?,?,?,?,?,?,?,?,?)", seg_rows)
    conn.commit()
    print(f"words: {len(word_rows)}  segments: {len(seg_rows)}  missing_text: {skipped_missing_text}  unaligned_words: {unaligned_words}")

    stats = conn.execute("SELECT COUNT(DISTINCT root) FROM segments WHERE root != ''").fetchone()[0]
    print(f"distinct roots: {stats}")
    conn.close()


if __name__ == "__main__":
    main()
