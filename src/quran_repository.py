"""دسترسی به متن قرآن و داده‌های صرفی ذخیره‌شده در quran.db.

جدول‌ها و ساختار:
  ayat(surah, ayah, text)               -- متن Uthmani (بدون بسم‌الله پیش‌سرهای تکراری)
  words(surah, ayah, word_pos, buck, arabic, norm)
  segments(surah, ayah, word_pos, seg_pos, buck, tag, lemma, root, features)
"""
import sqlite3
from pathlib import Path


class QuranRepository:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self._conn = None
        self._surah_names = {}

    def connect(self):
        if not self.db_path.exists():
            raise FileNotFoundError(f"پایگاه داده پیدا نشد: {self.db_path} (ابتدا scripts/prepare_data.py را اجرا کنید)")
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._load_surah_names()
        return self

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _load_surah_names(self):
        cur = self._conn.execute("SELECT index_, name_ar, name_en FROM surahs")
        self._surah_names = {r["index_"]: (r["name_ar"], r["name_en"]) for r in cur}

    def surah_name(self, surah_no: int):
        return self._surah_names.get(surah_no, ("", ""))

    def get_ayah(self, surah: int, ayah: int) -> str:
        cur = self._conn.execute("SELECT text FROM ayat WHERE surah=? AND ayah=?", (surah, ayah))
        row = cur.fetchone()
        return row["text"] if row else None

    def distinct_roots(self):
        cur = self._conn.execute("SELECT DISTINCT root FROM segments WHERE root != '' ORDER BY root")
        return [r["root"] for r in cur]

    def lemmas_by_norm(self, norm):
        """تمام واژه‌های قرآنی که فرم نرمال‌شده‌شان با ورودی برابر است."""
        cur = self._conn.execute(
            "SELECT DISTINCT segments.root AS root, segments.lemma AS lemma, "
            "segments.lemma_norm AS lemma_norm, COALESCE(words.surface, words.arabic) AS arabic "
            "FROM segments JOIN words ON segments.surah=words.surah "
            "AND segments.ayah=words.ayah AND segments.word_pos=words.word_pos "
            "WHERE words.norm=? AND segments.root != ''", (norm,))
        rows = [dict(r) for r in cur]
        out = []
        seen = set()
        for r in rows:
            key = (r["arabic"], r["lemma"], r["root"])
            if key not in seen:
                seen.add(key)
                out.append(r)
        return out

    def roots_by_norm(self, norm):
        """ریشه‌هایی که شکل نرمال‌شده آنها با ورودی برابر است (مثلاً ورودی خود ریشه است)."""
        cur = self._conn.execute(
            "SELECT DISTINCT root FROM segments WHERE root != ''")
        return [r["root"] for r in cur if r["root"] == norm]

    def occurrences_of_root(self, root):
        """تمام رخدادهای یک ریشه در قرآن: هر segment با واژه پوشاننده."""
        cur = self._conn.execute(
            "SELECT w.surah, w.ayah, w.word_pos, COALESCE(w.surface, w.arabic) AS word_arabic, "
            "w.arabic AS decoded, w.norm, "
            "s.tag, s.lemma, s.lemma_norm "
            "FROM segments s JOIN words w ON "
            "w.surah=s.surah AND w.ayah=s.ayah AND w.word_pos=s.word_pos "
            "WHERE s.root=? ORDER BY w.surah, w.ayah, w.word_pos", (root,))
        rows = [dict(r) for r in cur]
        for r in rows:
            r["arabic"] = r["word_arabic"]  # فرم واقعی متن قرآن (نسخه مرجع)
        return rows

    def word_form_by_surah_ayah_pos(self, surah, ayah, word_pos):
        cur = self._conn.execute(
            "SELECT COALESCE(surface, arabic) AS arabic, norm FROM words WHERE surah=? AND ayah=? AND word_pos=?",
            (surah, ayah, word_pos))
        row = cur.fetchone()
        return dict(row) if row else None

    def stats(self):
        ayat_count = self._conn.execute("SELECT COUNT(*) AS c FROM ayat").fetchone()["c"]
        word_count = self._conn.execute("SELECT COUNT(*) AS c FROM words").fetchone()["c"]
        seg_count = self._conn.execute("SELECT COUNT(*) AS c FROM segments").fetchone()["c"]
        root_count = self._conn.execute("SELECT COUNT(DISTINCT root) AS c FROM segments WHERE root != ''").fetchone()["c"]
        return {"ayat": ayat_count, "words": word_count, "segments": seg_count, "roots": root_count}
