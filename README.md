# OAuth-Guide

## Run the mock

The mock demonstrates the planned flow: search → saved guide, or research → evidence check → saved guide. It needs only Python 3.12+; nothing to install.

```bash
python3 mock/server.py
```

Open http://127.0.0.1:8780 and search for an app by name, website, or documentation URL. Saved guides: GitHub, Jira Cloud, Linear.

Self-checks:

```bash
python3 mock/server.py --self-check
python3 mock/validate.py --self-check
```

Re-check a guide against its live sources (exit 0 complete, 2 incomplete):

```bash
python3 mock/validate.py mock/static/guides/github.json
```

### What is real and what is simulated

- **Real:** every guide step quotes an official provider page; `validate.py` re-fetches each page and fails any step whose quote is missing or whose URL is off the provider's official domains. Guides with failed checks or blocking gaps show as Incomplete.
- **Real:** GitHub steps marked "Authorization tested" come from a local end-to-end test on 2026-10-28 (token exchange and one `GET /user`, no scopes).
- **Simulated:** the research agent. A search that misses the library writes `mock/queue/<slug>.json`; Claude, running in a Claude Code session that watches that folder, researches official docs, drafts the guide in `mock/staging/`, runs `validate.py`, and moves it into `mock/static/guides/` only if it passes. With no session watching, requests stay queued.

### Limits

- Pages are matched with a plain HTTPS fetch; docs that need JavaScript to render text will show as failed checks rather than passing.
- No model credentials, user accounts, or deployment. Single local process.
