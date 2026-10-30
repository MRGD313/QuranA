# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Webhook deployment mode (`server.py`) for free, trigger-based hosting on
  Render: Bale wakes the service on each message instead of 24/7 polling.
- `setWebhook` / `deleteWebhook` / `getWebhookInfo` in the Bale client.
- `scripts/set_webhook.py` to register, inspect, or remove the webhook.
- `render.yaml` Blueprint (free plan, Frankfurt, build-time database creation).
- Duplicate `update_id` suppression and a friendly "session expired" message.
- `/healthz` endpoint plus `WEBHOOK_SECRET`, `PUBLIC_BASE_URL`, and `PORT`
  settings.

### Changed

- `MSG_START` now tells users that the first reply after an idle period may take
  up to about a minute.
- `app.py` refuses to start in polling mode while a webhook is registered
  (`--force` removes it), to avoid disabling a production deployment by accident.
- SQLite connection can now be used from the webhook server's worker threads.

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
