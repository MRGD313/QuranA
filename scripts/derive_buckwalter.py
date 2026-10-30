"""استخراج تجربی نگاشت Buckwalter←عربی از فایل رسمی Corpus و متن Tanzil.

روش: برای هر آیه، واژه‌های Corpus (ادغام سگمنت‌های یک واژه) را با توکن‌های متن
Tanzil همان آیه تراز می‌کنیم؛ برای آیه‌هایی که تعداد توکن‌ها برابر است، جفت‌های
نویسه‌ای هم‌طول را برای استخراج نگاشت نویسه‌به‌نویسه استفاده می‌کنیم.
"""
import re
from collections import Counter, defaultdict

RAW_DIR = r"G:\personal_OC_projects\quran\data\raw"
MORPH = RAW_DIR + r"\quranic-corpus-morphology-0.4.txt"
TANZIL = RAW_DIR + r"\quran-uthmani.txt"


def load_tanzil():
    ayat = {}
    with open(TANZIL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            s, a, text = line.split("|", 2)
            ayat[(int(s), int(a))] = text
    return ayat


def load_morph():
    words = defaultdict(list)  # (s,a,w) -> list[(seg, buck, tag, feats)]
    with open(MORPH, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or not line.startswith("("):
                continue
            m = re.match(r"\((\d+):(\d+):(\d+):(\d+)\)\t(.*)", line)
            if m:
                s, a, w, seg, rest = m.groups()
                parts = rest.split("\t")
                words[(int(s), int(a), int(w))].append((int(seg), parts[0], parts[1], parts[2] if len(parts) > 2 else ""))
    return words


def main():
    ayat = load_tanzil()
    words = load_morph()

    morph_counts = {}
    for (s, a, w) in words:
        morph_counts[(s, a)] = max(morph_counts.get((s, a), 0), w)

    BISM = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ".split()
    ayat_tokens = {}
    for key, text in ayat.items():
        toks = text.split()
        # حذف بسم‌الله پیش‌آمده در اول هر سوره (به‌جز ۱ و ۹) برای تراز با Corpus
        if key[0] not in (1, 9) and key[1] == 1 and toks[:4] == BISM:
            toks = toks[4:]
        ayat_tokens[key] = toks

    matched, mismatched = [], []
    for key, toks in ayat_tokens.items():
        if morph_counts.get(key, 0) == len(toks):
            matched.append(key)
        else:
            mismatched.append(key)

    print(f"tanzil ayat: {len(ayat)} | corpus ayat: {len(set((s, a) for (s, a, _w) in words))}")
    print(f"word-count match: {len(matched)} | mismatch: {len(mismatched)}")
    print("sample mismatches:", [(k, ayat[k].split().__len__(), morph_counts[k]) for k in mismatched[:12]])

    char_map = defaultdict(Counter)  # buck char -> counter(arabic char)
    unresolved = Counter()
    matched_set = set(matched)
    for (s, a, w) in sorted(words.keys()):
        if (s, a) not in matched_set:
            continue
        toks = ayat_tokens[(s, a)]
        buck = "".join(buck for (_seg, buck, _tag, _feats) in sorted(words[(s, a, w)]))
        arb = toks[w - 1]
        if len(buck) == len(arb):
            for b, r in zip(buck, arb):
                char_map[b][r] += 1
        else:
            unresolved[(buck, arb)] += 1

    print("\n--- نگاشت نویسه‌ای (buck -> arabic) ---")
    for b in sorted(char_map):
        counts = char_map[b]
        total = sum(counts.values())
        top2 = counts.most_common(2)
        print(f"{b!r} (U+{ord(b):04X}) total={total} -> " + ", ".join(f"{r!r}(U+{ord(r):04X})x{c}" for r, c in top2))

    print("\n--- طول‌های نامساوی (نمونه) ---")
    for (buck, arb), cnt in unresolved.most_common(12):
        print(f"{buck!r} != {arb!r} x{cnt}")


if __name__ == "__main__":
    main()
