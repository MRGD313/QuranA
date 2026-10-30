"""پیدا کردن واژه‌های قرآنی که بیش از یک ریشه محتمل دارند — ابزار پژوهش/آزمون."""
import sqlite3
import sys
from collections import defaultdict

conn = sqlite3.connect(r"G:\personal_OC_projects\quran\data\quran.db")
conn.row_factory = sqlite3.Row
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

norm_roots = defaultdict(set)
for row in conn.execute(
        "SELECT words.norm AS norm, segments.root AS root FROM segments "
        "JOIN words ON segments.surah=words.surah AND segments.ayah=words.ayah "
        "AND segments.word_pos=words.word_pos WHERE segments.root != ''"):
    norm_roots[row["norm"]].add(row["root"])

multi = {n: rs for n, rs in norm_roots.items() if len(rs) > 1}
print("total norms:", len(norm_roots), "| multi-root:", len(multi))
shown = 0
for n, rs in sorted(multi.items(), key=lambda x: -len(x[1])):
    print(n, "->", sorted(rs))
    shown += 1
    if shown >= 25:
        break
