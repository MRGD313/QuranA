Verify that the current changes are healthy:

!`git status --short && python -m pytest tests -q && python scripts/check_repo_hygiene.py`

If anything fails, report only the real cause and the smallest necessary fix.
If tests are skipped because `data/quran.db` is missing, run
`python scripts/prepare_data.py` first (or state that data is unavailable).
