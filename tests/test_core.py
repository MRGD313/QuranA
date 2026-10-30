"""آزمون‌های هسته: نرمال‌سازی، Buckwalter، تشخیص ریشه، جست‌وجو، گزارش، منطق ربات."""
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.text_normalizer import normalize_arabic, normalize_word, valid_word, detect_script
from src.buckwalter import buckwalter_to_arabic, arabic_to_buckwalter
from src.morphology import resolve_roots
from src.search_service import search_root
from src.report_generator import generate_report
from src.bot_handler import (BotHandler, MSG_START, MSG_EMPTY, MSG_MULTI_WORDS,
                             MSG_INVALID_CHAR, MSG_PERSIAN_LETTER,
                             MSG_NOT_FOUND)


def ambiguous_norm(repo):
    """پیدا کردن یک فرم نرمال واقعی ابهامدار از داده صرفی."""
    row = repo._conn.execute(
        "SELECT norm FROM words w JOIN segments s ON w.surah=s.surah AND w.ayah=s.ayah "
        "AND w.word_pos=s.word_pos WHERE s.root != '' "
        "GROUP BY norm HAVING COUNT(DISTINCT root) > 1 LIMIT 1").fetchone()
    return row[0] if row else None


# ---------------- نرمال‌سازی ----------------
def test_strip_diacritics():
    assert normalize_arabic("بِسْمِ") == "بسم"
    assert normalize_arabic("ٱلرَّحْمَٰنِ") == "الرحمان"


def test_alef_variants():
    assert normalize_arabic("أ") == "ا"
    assert normalize_arabic("إ") == "ا"
    assert normalize_arabic("ٱ") == "ا"
    assert normalize_arabic("آ") == "ا"


def test_alf_zadeh_alef():
    assert normalize_arabic("ٱللَّهُ") == normalize_arabic("اللَّهُ")


def test_tah_marbuta_and_ya():
    assert normalize_arabic("كِتَابٌ") == "كتاب"
    assert normalize_arabic("عِلْمِى") == normalize_arabic("عِلْمِي")


def test_zwnj_removed():
    zwj = "\u200c"
    assert normalize_arabic("می" + zwj + "کنم") == "\u0645\u064a\u0643\u0646\u0645"


def test_superscript_alef_removed():
    assert normalize_arabic("مَٰلِكِ") == "مالك"


def test_persian_letters_detected():
    assert detect_script("پنجره") == "persian-only-letters"
    assert detect_script("گل") == "persian-only-letters"


def test_invalid_input():
    assert not valid_word("")
    assert not valid_word("سلام علیکم")
    assert not valid_word("abc")
    assert not valid_word("12")
    assert valid_word("عَلِمَ")
    assert valid_word("كَتَبَ")


# ---------------- Buckwalter (داده رسمی) ----------------
def test_buckwalter_decode_examples():
    assert normalize_arabic(buckwalter_to_arabic("n~aAsi")) == "ناس"
    assert normalize_arabic(buckwalter_to_arabic("Elm")) == "علم"
    assert normalize_arabic(buckwalter_to_arabic("{loHamodu")) == "الحمد"


def test_buckwalter_roundtrip_letters():
    assert arabic_to_buckwalter("كتب") == "ktb"
    assert normalize_arabic(buckwalter_to_arabic(arabic_to_buckwalter("كتب"))) == normalize_arabic("كتب")


# ---------------- تشخیص ریشه ----------------
def test_root_resolve_single(repo):
    res = resolve_roots("كَتَبَ", normalize_word("كَتَبَ"), repo)
    assert res.ok and res.root == "كتب"


def test_root_resolve_direct_root_word(repo):
    res = resolve_roots("علم", normalize_word("علم"), repo)
    if res.ambiguity:
        # اگر قرآن فرم‌هایی با ریشه‌های دیگر هم دارد، ابهام به کاربر نشان داده می‌شود
        assert len(res.options) >= 2
    else:
        assert res.ok and res.root == "علم"


def test_root_ambiguity(repo):
    norm = ambiguous_norm(repo)
    if norm is None:
        pytest.skip("واژه ابهامدار در داده نیست")
    res = resolve_roots(norm, norm, repo)
    assert "ریشه" not in ""  # noop بر درستی متغیر
    assert res.ambiguity == (not res.ok and bool(res.options))
    if res.ambiguity:
        assert len(res.options) >= 2


def test_root_not_exist(repo):
    res = resolve_roots("زقشنف", normalize_word("زقشنف"), repo)
    assert not res.ok and not res.ambiguity


# ---------------- جست‌وجو و آیات ----------------
def test_search_root_real_data(repo):
    result = search_root("كتب", repo)
    assert result["unique_ayahs"] == len(result["ayat"])
    keys = [(g.surah, g.ayah) for g in result["ayat"]]
    assert keys == sorted(keys)
    assert len(keys) == len(set(keys))
    assert result["lexical_events"] >= result["distinct_word_forms"]
    assert result["unique_ayahs"] > 0


def test_occurrence_word_in_ayah(repo):
    result = search_root("علم", repo)
    for g in result["ayat"][:80]:
        for occ in g.words:
            assert occ.word_arabic in g.text


def test_sorting_and_dedup(repo):
    result = search_root("بسم", repo)
    assert len({(g.surah, g.ayah) for g in result["ayat"]}) == len(result["ayat"])


# ---------------- گزارش ----------------
def test_report_generation_utf8(repo, tmp_path):
    result = search_root("سجد", repo)
    path = generate_report("سجد", "سَجَدَ", "سجد", result, repo, out_dir=tmp_path)
    data = path.read_bytes()
    text = data.decode("utf-8")
    assert "گزارش واژه‌های هم‌ریشه در قرآن کریم" in text
    assert "تعداد آیات یکتا: " + str(result["unique_ayahs"]) in text
    for g in result["ayat"][:30]:
        assert g.text in text


def test_report_filename_safe(repo, tmp_path):
    result = search_root("سجد", repo)
    path = generate_report("سجد", "سَجَدَ", "سجد", result, repo, out_dir=tmp_path)
    assert path.suffix == ".txt"
    bad = set('\\/:*?"<>|')
    assert not any(c in path.name for c in bad)


# ---------------- منطق ربات (بله) ----------------
def test_start_message(repo, fake_client):
    h = BotHandler(fake_client, repo)
    h.handle_update(1, 1, "/start")
    assert fake_client.last_text() == MSG_START


def test_empty_message(repo, fake_client):
    h = BotHandler(fake_client, repo)
    h.handle_update(1, 1, "")
    assert fake_client.last_text() == MSG_EMPTY


def test_multi_word_message(repo, fake_client):
    h = BotHandler(fake_client, repo)
    h.handle_update(1, 1, "سلام علیکم")
    assert fake_client.last_text() == MSG_MULTI_WORDS


def test_latin_input(repo, fake_client):
    h = BotHandler(fake_client, repo)
    h.handle_update(1, 1, "arabic123")
    assert fake_client.last_text() == MSG_INVALID_CHAR


def test_persian_only_letters_input(repo, fake_client):
    h = BotHandler(fake_client, repo)
    h.handle_update(1, 1, "پنجره")
    assert fake_client.last_text() == MSG_PERSIAN_LETTER


def test_word_not_found(repo, fake_client):
    h = BotHandler(fake_client, repo)
    h.handle_update(1, 1, "زقشنف")
    assert fake_client.last_text() == MSG_NOT_FOUND
    assert fake_client.docs == []


def test_word_to_report(repo, fake_client, tmp_path):
    h = BotHandler(fake_client, repo, out_dir=tmp_path)
    h.handle_update(1, 1, "كتاب")
    assert fake_client.docs, "باید فایل ارسال شود"
    chat_id, path, caption = fake_client.docs[-1]
    assert chat_id == 1 and path.exists() and path.suffix == ".txt"
    assert "كتب" in caption


def test_ambiguous_flow_with_digit(repo, fake_client, tmp_path):
    norm = ambiguous_norm(repo)
    if norm is None:
        pytest.skip("واژه ابهامدار در داده نیست")
    if not resolve_roots(norm, norm, repo).ambiguity:
        pytest.skip("نخستین فرم پیدا شده مستقیماً تطبیق ریشه بود")

    h = BotHandler(fake_client, repo, out_dir=tmp_path)
    h.handle_update(10, 1, norm)
    assert any("شماره" in t for t in fake_client.texts())
    h.handle_update(10, 2, "1")
    assert any(cid == 10 for (cid, _p, _c) in fake_client.docs)


def test_doc_send_failure_handled(repo, fake_client, tmp_path):
    fake_client.fail_document = RuntimeError("network down")
    h = BotHandler(fake_client, repo, out_dir=tmp_path)
    h.handle_update(1, 1, "كتاب")
    texts = fake_client.texts()
    assert any("ارسال فایل به بله با خطا" in t for t in texts)


def test_user_isolation(repo, fake_client, tmp_path):
    h = BotHandler(fake_client, repo, out_dir=tmp_path)
    norm = ambiguous_norm(repo)
    if norm is not None and resolve_roots(norm, norm, repo).ambiguity:
        h.handle_update(1, 1, norm)
        assert 1 in h.pending
    h.handle_update(2, 1, "كتاب")
    assert any(cid == 2 for (cid, _p, _c) in fake_client.docs)


# ---------------- اتصال بله ----------------
def test_bale_client_requires_token():
    from src.bale_api import BaleClient
    c = BaleClient("")
    assert not c.ready
    with pytest.raises(RuntimeError):
        c.get_updates()
