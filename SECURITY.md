# Security Policy

## Supported versions

Security fixes are applied to the latest release on the default branch.

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Use GitHub's private vulnerability reporting (Security → Report a vulnerability)
or contact the maintainer privately through the contact method on their GitHub
profile. Include:

- affected version or commit,
- steps to reproduce,
- potential impact,
- any suggested fix.

You can expect an acknowledgement within a few days. Please allow reasonable
time for a fix before public disclosure.

## Secrets

- QuranA reads the Bale bot token from the `BALE_TOKEN` environment variable
  (via a local `.env` file). `.env` is git-ignored.
- Never commit tokens, passwords, or exported reports containing private data.
- If a token is accidentally committed, revoke it immediately in Bale
  (BotFather) and issue a new one. Deleting the commit is not sufficient.
- `scripts/check_repo_hygiene.py` performs a lightweight scan for token-like
  strings before committing.
