# OAuth-Guide

## Run the mock

The mock demonstrates the planned flow: search → saved guide, or research → evidence check → saved guide. It needs only Python 3.12+; nothing to install.

```bash
python3 mock/server.py
```

Open http://127.0.0.1:8780 and search for an app by name, website, or documentation URL. Saved guides: GitHub, Jira Cloud, Linear, Slack.

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
- **Real:** GitHub steps marked "Authorization tested" come from two local end-to-end runs on 2026-10-28 (token exchange and one `GET /user`, no scopes). The second run was timed: register 37 s, client secret including Confirm access 76 s, consent to API call 26 s, with Claude driving Chrome. Jira, Linear and Slack guides are source-checked but not flow-tested.
- **Simulated:** the research agent. A search that misses the library writes `mock/queue/<slug>.json`; Claude, running in a Claude Code session that watches that folder, researches official docs, drafts the guide in `mock/staging/`, runs `validate.py`, and moves it into `mock/static/guides/` only if it passes. With no session watching, requests stay queued.

### What each guide tells you

- **Difficulty** (easy / moderate / hard) with the main reason.
- **OAuth setup time**, from opening the provider console to the first successful sign-in. Shown as **measured** where we ran a timed test (GitHub, 2026-10-28) and as a labeled **estimate** otherwise.
- **Building it into your app**: a separate, labeled estimate for the callback, token storage and refresh code. Every guide states the assumptions behind its estimates.
- **Approval wait before other users can connect**: only approvals that gate OAuth itself, quoted from the provider when possible. Optional marketplace or directory listings are not counted.
- **What an agent can do for you and where you take over**, with the reason for each handoff (for example GitHub's Confirm access, Atlassian's developer terms, the user's consent click).

The research agent must fill in all of the above for every new guide; `validate.py` rejects times without a basis, estimates without stated assumptions, and handoffs without a reason.

### Limits

- Pages are matched with a plain HTTPS fetch; docs that need JavaScript to render text will show as failed checks rather than passing.
- No model credentials, user accounts, or deployment. Single local process.
