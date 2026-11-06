# QuranA (قرآنا) — Agent Guide

Bale bot: an Arabic word → its root (Quranic Arabic Corpus 0.4) → all same-root
Quranic words → full verses (Tanzil Uthmani 1.1) → UTF-8 `.txt` report.

## Commands

- Tests: `python -m pytest tests -q` — requires `data/quran.db`, otherwise
  data-dependent tests **skip** (a skip is not a pass).
- Fresh data (in order): `python scripts/download_data.py`, then
  `python scripts/prepare_data.py`, then `python scripts/validate_data.py`.
- Offline core E2E: `python scripts/run_core_e2e.py سَجَدَ`
- Hygiene: `python scripts/check_repo_hygiene.py`
- Local bot: `python app.py` — webhook server: `python server.py`

## Map

- `app.py` polling; `server.py` webhook; `config.py` env + paths.
- Flow: `bot_handler` → `morphology` → `search_service` → `report_generator` +
  `prompt_builder`; data access through `quran_repository` (SQLite).
- `src/` logic · `scripts/` CLI · `tests/` pytest · `docs/` design + deployment.
- Details: `docs/ARCHITECTURE.md`; data/licences: `THIRD_PARTY_NOTICES.md`.

## Invariants

- Never edit the Quran text; normalization is only for matching. Reports quote
  the reference text verbatim and cite both data sources and versions.
- Roots/lemmas come from corpus data — never guess or use string similarity.
- Secrets come only from env/`.env`; never print, log, or commit them.
- New dependencies need a clear reason in `pyproject.toml`.
- Run tests + hygiene before committing; keep behaviour covered by tests.

## Do not

- Read `data/raw/**`, `data/*.db`, `data/reports/**`, `.venv/**`, or `.env`
  (large or secret). Use `scripts/show_ayah.py`/SQL instead.
- Commit data, generated reports, databases, or `.env`.
- Read whole files blindly: `grep` first, then `read` with offset/limit for
  files over ~200 lines.
