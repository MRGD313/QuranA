"""دیدن مستقیم یک آیه از پایگاه داده — ابزار پژوهش."""
import sqlite3
import sys
import os

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

conn = sqlite3.connect(r"G:\personal_OC_projects\quran\data\quran.db")
s, a = int(sys.argv[1]), int(sys.argv[2])
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT text FROM ayat WHERE surah=? AND ayah=?", (s, a)).fetchone()
print(row["text"])
