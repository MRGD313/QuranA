"""تشخیص ریشه صرفی و صورت‌های هم‌ریشه متعلق به یک واژه قرآنی.

داده صرفی از منبع مستقل «Quranic Arabic Corpus (0.4)» با کد Buckwalter
آمده و در prepare_data به عربی بازگشایی و در quran.db ذخیره شده است.

این ماژول خودش هیچ قاعده حدسی ندارد؛ همیشه از داده واقعی Coropus جواب می‌گیرد.
"""
from dataclasses import dataclass, field


@dataclass
class RootOption:
    """ریشه محتمل برای یک واژه ورودی."""
    root: str                # ریشه (عربی نرمال)
    stem_count: int          # تعداد واژه‌هایی که با آن ریشه ظاهر شدند
    occurrence_count: int    # تعداد کل رخدادهای واژگانی این ریشه در قرآن
    sample_words: list       # چند واژه نمونه

    def label(self) -> str:
        samples = "، ".join(self.sample_words[:4])
        return (f"ریشه «{self.root}» — {self.occurrence_count} رخداد — نمونه: {samples}")


@dataclass
class RootResolution:
    """نتیجه تلاش برای تشخیص ریشه ورودی کاربر."""
    word: str = ""
    normalized: str = ""
    ok: bool = False
    ambiguity: bool = False
    root: str = ""                    # اگر ok و بدون ابهام
    options: list = field(default_factory=list)   # list[RootOption] در صورت ابهام
    matched_word_form: str = ""       # واژه قرآنی که مطابق ورودی پیدا شد.


def resolve_roots(input_word: str, normalized_word: str, repo) -> RootResolution:
    """تشخیص ریشه یا ریشه‌های محتمل برای واژه ورودی.

    1. واژه‌های قرآنی که فرم نرمال‌شده آنها با ورودی برابر است (فرم‌های صرفی).
    2. اگر ورودی مستقیماً یک ریشه ثبت‌شده باشد (مثلاً «علم»).
    3. در صورت چند ریشه محتمل، ابهام برگردانده می‌شود.
    """
    res = RootResolution(word=input_word, normalized=normalized_word)

    options = []
    # روش ۱: واژه‌های قرآنی با فرم صرفی برابرِ ورودی
    lemmas = repo.lemmas_by_norm(normalized_word)
    root_info = {}
    for r in lemmas:
        root_norm = r["root"] if isinstance(r["root"], str) else ""
        if not root_norm:
            continue
        info = root_info.setdefault(root_norm, {"stems": set(), "occurrences": 0})
        info["stems"].add(r["arabic"])

    if root_info:
        for root_norm, info in root_info.items():
            occ = repo.occurrences_of_root(root_norm)
            options.append(RootOption(
                root=root_norm,
                stem_count=len(info["stems"]),
                occurrence_count=len(occ),
                sample_words=sorted(info["stems"])[:4],
            ))

    # روش ۲: ورودی مستقیماً یک ریشه ثبت‌شده است
    direct_roots = repo.roots_by_norm(normalized_word)
    for droot in direct_roots:
        if not any(o.root == droot for o in options):
            occ = repo.occurrences_of_root(droot)
            stems = sorted({o["arabic"] for o in occ})[:4]
            options.append(RootOption(
                root=droot,
                stem_count=len({o["arabic"] for o in occ}),
                occurrence_count=len(occ),
                sample_words=stems,
            ))

    if not options:
        return res  # ok=False

    options.sort(key=lambda o: (-o.occurrence_count, o.root))
    res.options = options

    if len(options) == 1:
        res.ok = True
        res.root = options[0].root
    else:
        # ابهام: چند ریشه محتمل؛ تصمیم را به کاربر می‌سپاریم.
        # حتی اگر ورودی عین ریشه ثبت‌شده باشد، چند معنا ممکن است.
        res.ambiguity = True
        res.ok = False

    return res


def words_of_root(root: str, repo):
    """واژه‌های متمایز قرآنی متعلق به ریشه، با تعداد رخداد هر واژه."""
    occ = repo.occurrences_of_root(root)
    forms = {}
    for o in occ:
        key = (o["arabic"], o["norm"])
        d = forms.setdefault(key, {"count": 0, "lemmas": set(), "tags": set()})
        d["count"] += 1
        if o.get("lemma"):
            d["lemmas"].add(o["lemma"] if isinstance(o["lemma"], str) else "")
        if o.get("tag"):
            d["tags"].add(o["tag"])
    out = []
    seen = set()
    for o in occ:
        keyo = (o["surah"], o["ayah"], o["word_pos"])
        if keyo not in seen:
            seen.add(keyo)
    unique_l = sorted({(o["surah"], o["ayah"], o["word_pos"]) for o in occ})
    return out or {
        "unique_word_positions": unique_l,
        "forms": forms,
        "occurrences": occ,
    }
