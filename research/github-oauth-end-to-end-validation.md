# GitHub OAuth read-only end-to-end validation

Date: 2026-10-28. Status: **succeeded — host-executed OAuth exchange and one authenticated API read**.

## Actual outcome

The existing personal-account OAuth App **OAuth Guide validation** completed a fresh authorization-code flow with random state and S256 PKCE. GitHub returned an access token with empty granted scopes. The temporary client used that bearer token for exactly one fixed `GET https://api.github.com/user`, receiving HTTP 200 and a structurally valid authenticated identity response. It emitted no profile fields or credential values.

| Check | Observed result |
|---|---|
| Callback received | true |
| Returned state validated | true |
| PKCE S256 used | true |
| Requested OAuth scopes | empty |
| Token-exchange HTTP status | 200 |
| Token exchange succeeded | true |
| Granted scopes empty | true |
| Access token expires | true |
| Refresh token returned | true |
| Authenticated API operation | GET /user |
| API HTTP status | 200 |
| Response contains expected identity shape | true; actual identity omitted |
| API OAuth-scope header empty | true |
| Refresh behavior tested | false |

This was an authenticated `/user` request using the newly exchanged OAuth bearer token, not an unauthenticated public-profile lookup. No repository, org, email, write, or admin scopes were requested; no repositories or unrelated account data were fetched.

## Actual sequence and corrections

1. Registration was previously observed live and succeeded with loopback homepage `http://127.0.0.1:8765`, callback `http://127.0.0.1:8765/callback`, wildcard matching off, Device Flow off, and expiring-token default on. Earlier registration steps were not screenshotted.
2. Generating the one test-app secret required GitHub **Confirm access**. The user completed verification directly; no code was requested or handled in chat.
3. Revalidation found the existing generated secret. It was transferred directly inside browser-control runtime to a mode-600 transient file, never printed to tool/model output. No duplicate secret was generated.
4. First consent showed **Public data only**. Callback arrived and state matched, but Python's default certificate store failed to verify GitHub before token-exchange HTTP completed. No authenticated API request occurred in that attempt.
5. A credential-free diagnostic confirmed the trusted OS bundle `/etc/ssl/cert.pem` verifies GitHub. The client was changed to use that bundle while retaining TLS certificate/hostname verification. No certificate bypass was used.
6. CUA reset interrupted credential reuse. After the user opened a neutral blank tab, control was safely reacquired and the same existing secret transferred with output suppressed. No secret rotation occurred.
7. A fresh flow reused the previous public-data grant without requiring another consent click. Fresh callback/state validated; code exchange and the single authenticated API read both returned HTTP 200.
8. The browser reached a query-free local completion message. The listener exited; transient credential input and authorization URL file were absent, and the local port was verified closed.

## Execution and Claude attribution

Claude CLI previously fetched official GitHub docs successfully. On the retry it again completed with process exit 0, final result `success`, `is_error: false`, and successfully fetched the current authorization-flow source. Its Chrome connection returned an empty list; it did not operate Chrome or call GitHub with a token.

Host CUA performed actual browser actions; the temporary local Python client performed token exchange and authenticated read. Claude also completed a sanitized guide-note synthesis invocation with exit 0/result success. Its draft included unused plan directives and some imprecise wording; host review corrected attribution and TLS wording before saving guide.md. No draft directives were executed. This demonstrates a local agent-controlled execution path can complete OAuth and use resulting access; it does not demonstrate Claude independently controlling a browser, or a deployed website inheriting the user's host-browser session.

## Client safety checks

Client: `/tmp/github-oauth-validation/oauth_check.py`.

The client binds only loopback, uses exact callback path, random state, S256 PKCE, no requested scopes, fixed endpoint/method allowlist, redirect refusal, rejection of missing/non-empty grant-scope evidence, verified TLS, suppressed request logging, no token/profile persistence, a bounded listener, and a query-free completion redirect. Offline self-check passed the RFC PKCE S256 vector, verifier/challenge lengths, state comparison, and loopback host check.

Sanitized result: `/tmp/github-oauth-validation/result.json`. First failed-attempt result is separately preserved at `/tmp/github-oauth-validation/first-attempt-result.json`. Neither contains secrets, tokens, codes, or profile fields.

## Screenshots and guide

- `/tmp/github-oauth-validation/guide.md` — observation-based setup/test guide with evidence index and handoffs.
- `/tmp/github-oauth-validation/screenshots/01-live-callback-completion.png` — cropped screenshot of actual query-free local completion. It proves browser completion only; API results come from `result.json`.
- `/tmp/github-oauth-validation/screenshots/02-official-creation-documentation.png` — cropped official public docs, explicitly documentation evidence rather than live registration proof.
- `/tmp/github-oauth-validation/screenshots/03-official-registration-steps.png` — cropped official field instructions; documentation evidence only.
- `/tmp/github-oauth-validation/claude-guide-notes.md` — unreviewed Claude draft retained separately; guide.md is the corrected deliverable.

Only safe regions were saved. Raw native screenshots containing browser chrome/unrelated tabs were processed in memory and not persisted. Earlier credential/consent screens were not replayed for screenshots.

## Residual state and limits

The test OAuth App, its single generated secret, and the public-data authorization/grant remain on GitHub. No app/secret/grant was deleted, rotated, or revoked. The new access/refresh tokens existed only in the client process and were discarded when it exited; GitHub's issued credentials can remain valid server-side until expiry/revocation. No token/profile files remain locally. No listener remains.

No additional human action is required for this completed test. Refresh, revocation, organization approval, repository access, distribution, provider review, production hosting, secure multi-user credential storage and deployed-service browser access were not tested. No approval or duration estimate is claimed.

## Official sources

- [Creating OAuth Apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app).
- [Authorization, PKCE, callback and token flow](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps).
- [OAuth scopes](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps).
