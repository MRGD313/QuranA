# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] — 2026-10-30

### Added

- Initial public release of QuranA (قرآنا).
- Bale messenger bot: receives a word, resolves its Arabic root, searches the
  Quran, and sends a UTF-8 `.txt` report.
- Root resolution based on Quranic Arabic Corpus 0.4 (roots, lemmas, POS).
- Quran text from Tanzil Uthmani 1.1, aligned verse-by-verse with the corpus.
- Ambiguity handling with numbered root choices.
- Duplicate-free, sorted verse lists and distinct word-form statistics.
- CLI: `scripts/download_data.py`, `prepare_data.py`, `validate_data.py`.
- Test suite covering normalization, root resolution, search, report
  generation, bot flows, failure handling, and user isolation.
- Documentation for data provenance, licensing, and local setup.
