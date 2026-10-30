"""استخراج رخدادهای واژه‌های هم‌ریشه و آیات مرتبط، با حذف تکرار و مرتب‌سازی."""
from dataclasses import dataclass, field


@dataclass
class Occurrence:
    surah: int
    ayah: int
    word_pos: int
    word_arabic: str
    decoded: str = ""          # فرم با اعراب کامل از داده صرفی
    norm: str = ""
    tag: str = ""
    lemma: str = ""
    lemma_norm: str = ""
    root: str = ""


@dataclass
class AyahGroup:
    surah: int
    ayah: int
    text: str = ""
    words: list = field(default_factory=list)     # فرم‌های هم‌ریشه در این آیه

    def add(self, occ: Occurrence):
        self.words.append(occ)


def search_root(root: str, repo) -> dict:
    """تمام رخدادهای یک ریشه را پیدا و آیات یکتا را (مرتب، بدون تکرار) برمی‌گرداند."""
    raw = repo.occurrences_of_root(root)
    occurrences = []
    for r in sorted(raw, key=lambda r: (r["surah"], r["ayah"], r["word_pos"])):
        occurrences.append(Occurrence(
            surah=r["surah"], ayah=r["ayah"], word_pos=r["word_pos"],
            word_arabic=r["arabic"], decoded=r.get("decoded", ""), norm=r["norm"],
            tag=r["tag"], lemma=r["lemma"], lemma_norm=r["lemma_norm"], root=root))

    ayat_groups = {}
    for occ in occurrences:
        key = (occ.surah, occ.ayah)
        if key not in ayat_groups:
            text = repo.get_ayah(occ.surah, occ.ayah)
            g = AyahGroup(surah=occ.surah, ayah=occ.ayah, text=text or "")
            ayat_groups[key] = g
        ayat_groups[key].add(occ)

    # مرتب‌سازی آیات بر اساس شماره سوره و سپس شماره آیه
    sorted_keys = sorted(ayat_groups.keys())
    ayat = [ayat_groups[k] for k in sorted_keys]

    # دسته‌بندی فرم‌های واژگانی متمایز با تعداد رخداد هر فرم
    forms = {}
    for occ in occurrences:
        d = forms.setdefault((occ.word_arabic, occ.norm), {"count": 0, "tags": set(), "vocalized": set()})
        d["count"] += 1
        if occ.tag:
            d["tags"].add(occ.tag)
        if occ.decoded:
            d["vocalized"].add(occ.decoded)

    # آمار دقیق و متمایز
    lexical_events = len(occurrences)   # تعداد رخدادهای واژگانی
    unique_ayahs = len(ayat)

    return {"root": root, "ayat": ayat, "occurrences": occurrences,
            "forms": forms,
            "distinct_word_forms": len(forms),
            "lexical_events": lexical_events,
            "unique_ayahs": unique_ayahs}
