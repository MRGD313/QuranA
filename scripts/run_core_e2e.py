"""جریان کامل هسته: ورودی واژه → ریشه → آیات → فایل گزارش. بدون شبکه."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.quran_repository import QuranRepository
from src.morphology import resolve_roots
from src.search_service import search_root
from src.report_generator import generate_report
from config import DB_PATH


def e2e(word: str):
    repo = QuranRepository(DB_PATH).connect()
    try:
        from src.text_normalizer import normalize_word
        norm = normalize_word(word)
        res = resolve_roots(word, norm, repo)
        if res.ambiguity:
            print(f"«{word}» مبهم است؛ گزینه‌ها:")
            for i, o in enumerate(res.options, 1):
                print(f"  {i}. {o.label()}")
            return
        if not res.ok:
            print(f"«{word}» یافت نشد.")
            return
        print(f"«{word}» → ریشه «{res.root}»")
        result = search_root(res.root, repo)
        print(f"  واژه‌های متمایز: {result['distinct_word_forms']}  رخداد: {result['lexical_events']}  آیات: {result['unique_ayahs']}")
        path = generate_report(res.root, word, norm, result, repo)
        print(f"  فایل: {path.name}")
        # چند نمونه
        for g in result["ayat"][:2]:
            name_ar, _ = repo.surah_name(g.surah)
            print(f"  نمونه: [{name_ar} {g.surah}:{g.ayah}] {g.text[:60]}...")
            print(f"       واژه‌ها: {'؛ '.join(o.word_arabic for o in g.words)}")
    finally:
        repo.close()


if __name__ == "__main__":
    word = sys.argv[1] if len(sys.argv) > 1 else "علم"
    e2e(word)
