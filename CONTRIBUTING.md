# Contributing to QuranA

Thanks for your interest. This document explains how to propose changes.

## Code of conduct

By participating you agree to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Ways to contribute

- Report bugs or usability problems (use the issue templates).
- Propose new features that fit the project scope.
- Improve documentation, translations, or tests.
- Review pull requests.

## Development setup

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt pytest
python scripts/download_data.py
python scripts/prepare_data.py
python scripts/validate_data.py
python -m pytest tests -q
```

A live Bale token is required only to run the bot (`app.py`). Never commit a
real token. Use `.env` locally (it is git-ignored).

## Pull requests

1. Open an issue first for significant changes.
2. Keep changes focused; do not mix refactoring with behavior changes.
3. Add or update tests. Run `python -m pytest tests -q`.
4. Run `python scripts/check_repo_hygiene.py` before committing.
5. Update `CHANGELOG.md` for user-visible changes.
6. Describe the motivation and the verification you performed.

## Data changes

The Quran text and morphology annotation are third-party works and must not be
modified. If you believe the reference text should change, open an issue with a
verifiable source. Do not regenerate or edit the text to make tests pass.

## Commit messages

Conventional prefixes are welcome but not mandatory:

- `feat:` new behavior
- `fix:` bug fix
- `docs:` documentation only
- `test:` tests only
- `chore:` tooling, dependencies

## Licensing

By contributing you agree that your code contributions are licensed under the
MIT License (see [LICENSE](LICENSE)). Do not add datasets that cannot be
redistributed under their own terms.
