# OAuth Guide

Look up an app and get a shareable guide to registering its OAuth app: where to start, each step, how hard it is, how long setup and build take, any approval wait that blocks other users, and which steps an agent can do versus where you take over. Every step quotes the provider's official docs, and the quotes are re-checked before a guide is saved.

- **Live:** https://oauth-guide.fly.dev
- **Full product write-up** (architecture, decisions, validation results): [`PRD.html`](PRD.html), diagram in [`oauth-guide-design.png`](oauth-guide-design.png)

## Using it

1. Search for an app by name, website or documentation URL. Saved guides open immediately: GitHub, Jira Cloud, Linear, Slack, plus any generated since.
2. For an app that isn't in the library, open **Connect model**, choose **Anthropic, OpenAI or Portkey**, and paste one key. The key is held in server memory for your session only; it is never logged, stored on disk or sent back to the page. Use a key with a spending limit: a new guide costs roughly $0.45–2.25 on your account.
3. Search again. The research page shows the agent's searches, the pages it reads, its thinking and each quote check as they happen (usually 2–5 minutes), then opens the guide.
4. Guides older than a day offer **Regenerate** (uses your model) or, for hands-on tested guides, **Re-check sources only** (no model).

## Run locally

Python 3.12+.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python mock/server.py
```

Open http://127.0.0.1:8780. Guides live in `mock/data/` (seeded from `mock/seed-guides/` on first start).

Self-checks (no network or keys needed):

```bash
.venv/bin/python mock/server.py --self-check && .venv/bin/python mock/validate.py --self-check && .venv/bin/python mock/research.py
```

Re-check one guide against the live docs (exit 0 complete, 2 incomplete):

```bash
.venv/bin/python mock/validate.py mock/data/guides/github.json
```

Deploy: `fly.toml` and `Dockerfile` run one always-on machine with a 1 GB volume at `/data`.

## Key decisions

- **Guidance, not setup on your behalf.** The developer owns their provider accounts; the product tells them what to do and where they must act.
- **Generate from official sources, test a sample hands-on.** The in-app agent researches docs live so unfamiliar apps work while you watch. Testing every app before publishing was rejected: provider security checks (sign-in confirmation, 2FA, terms) need the account owner. GitHub was tested end to end twice, one run timed; the Jira console was explored up to its terms gate.
- **A validator, not the model, decides what counts as checked.** It re-fetches every cited page and requires the exact quote, accepts only domains the research actually fetched, and leaves failed steps visible and the guide marked Incomplete.
- **Two separate times plus a wait.** OAuth setup (console to first sign-in; measured for GitHub, estimated elsewhere), building it into your app (estimate with stated assumptions), and only approval waits that block other users. Optional marketplace listings are excluded.
- **Visitor brings one model key.** Model cost stays with the visitor; Portkey lets teams route through their gateway.
- **One small Fly.io server with plain JSON files**, so the same evidence check runs for every provider and there is nothing extra to operate.

## What was checked

| Guide | Evidence | Quotes |
|---|---|---|
| GitHub | Two hands-on runs: register, secret, consent, token exchange, `GET /user` (no scopes) | 11/11 |
| Jira Cloud | Docs + developer console up to the create form; **Incomplete**: creation blocked on accepting developer terms | 16/16 |
| Linear, Slack | Docs, researched live | 10/10, 14/14 |
| Gmail, GitLab, Discord | Generated in the app through Portkey (Gmail and GitLab locally, Discord on the live site); Gmail **Incomplete** (project-creation page not fetched) | 9/9, 11/11, 12/12 |

Learned and corrected along the way: being signed in doesn't avoid GitHub's Confirm access step when creating a secret; marketplace review times (Slack, Atlassian) were first counted as setup time and then removed; a correct quote failed because web fetch returns Markdown, so matching now ignores code and bold marks. Details in [`PRD.html`](PRD.html#validation).

## Limitations

- The in-app agent reads documentation only; it never signs in to a provider. Hands-on evidence exists for GitHub only.
- The direct Anthropic and OpenAI research paths have not had a live run; Portkey (to Claude) has, locally and on the live site.
- Time estimates are uncalibrated, and model-written build estimates can disagree with hand-written ones for similar work. A shared baseline is planned.
- Pages that need JavaScript to show their text would fail the quote check rather than pass.
- Keys and running research live in one process: a restart disconnects visitors, and the app runs on a single machine.
- Credentials are kept out of the repository; test apps created during validation remain on the owner's GitHub account.
