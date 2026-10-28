# GitHub OAuth App research and practical validation

Date: 2026-10-28. Result: **live personal-account OAuth App registration succeeded**. This is an OAuth App, not a GitHub App. Registration/configuration is validated; authorization, token exchange, refresh and API behavior are not.

## Actual external change

Created one new personal-account OAuth App named **OAuth Guide validation**. GitHub showed **Application created successfully**. Saved values verified on the app settings page:

| Setting | Observed value |
|---|---|
| Application name | OAuth Guide validation |
| Homepage URL | `http://127.0.0.1:8765` |
| Description | Private local OAuth setup validation. |
| Redirect URI | `http://127.0.0.1:8765/callback` |
| Allow wildcard matching | Off |
| Device Flow | Off |
| Expire user access tokens | On in registration form; left at default |
| Authorized users | 0 |
| Client ID | Present; value omitted |
| Client secret | Not generated; **Generate a new client secret** button present |

The loopback HTTP homepage and redirect URI were accepted and saved. No local listener was started, so accepted registration does not prove callback delivery. No existing apps, repos, organization settings, Jira form, or account credentials were modified. No distribution, Marketplace publishing, payments, consent, approval submissions, or messages occurred.

“Private” here describes a local test with zero authorized users and no publication. No GitHub OAuth App private/public distribution toggle was observed, and GitHub warns that OAuth App metadata should be considered public. Do not present this app as having an Atlassian-style private distribution mode.

## Claude involvement and evidence

Actually invoked the installed authenticated Claude CLI with its Chrome tools and public-document WebFetch capabilities. Outside-sandbox access used the existing account; no credential export or bypass-permissions flag was used. Claude completed with exit 0, final result `success`, `is_error: false`.

Claude's **list_connected_browsers** returned `[]` again. Its browser tools were available but had no connected Chrome browser. Claude therefore did **not** operate the live browser. Claude fetched current official sources and produced the setup/check plan; **host CUA native Chrome automation** opened GitHub, filled the form, submitted registration, and verified the resulting app. Source claims about registration/authorization were independently checked against current official page text.

Claude successfully fetched these official sources, with no outright fetch errors:

- [Creating an OAuth App](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app).
- [Authorizing OAuth Apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps).
- [OAuth App scopes](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps).
- [GitHub Apps versus OAuth Apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps).
- [OAuth App best practices](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/best-practices-for-creating-an-oauth-app).
- [Modifying an OAuth App](https://docs.github.com/en/apps/oauth-apps/maintaining-oauth-apps/modifying-an-oauth-app).
- [Deleting an OAuth App](https://docs.github.com/en/apps/oauth-apps/maintaining-oauth-apps/deleting-an-oauth-app).
- [OAuth application REST operations](https://docs.github.com/en/rest/apps/oauth-applications).
- [Reviewing authorized OAuth Apps](https://docs.github.com/en/apps/oauth-apps/using-oauth-apps/reviewing-your-authorized-oauth-apps).
- [GitHub Terms](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service).

WebFetch returns extracted/model-summarized page content; success is evidence of actual fetch/inference, not proof every summarization claim is correct. This report avoids relying on its speculative secret-display or app-deletion consequences.

## Console-observed steps

1. In the existing signed-in Chrome session, opened a **new tab** at `https://github.com/settings/applications/new`. Personal Developer Settings registration appeared without sign-in or MFA. No organization context was used.
2. Observed **Register a new OAuth app**, required Application name and Homepage URL, optional Application description, and **Redirect URIs**.
3. Current UI explicitly allows **up to 10 redirect URIs**, each with optional wildcard matching. This differs from older single-callback tutorials.
4. Observed Device Flow off and **Expire user access tokens** on by default. No new terms acceptance checkbox or agreement gate appeared in this registration flow.
5. Entered the values listed above and clicked **Register application**.
6. Verified **Application created successfully**, matching saved loopback values, 0 users, Client ID section, and separate **Generate a new client secret** control. Did not click that control or reveal/copy its contents.

Current semantic resume location: Chrome tab displaying the **OAuth Guide validation** app's GitHub OAuth App settings. Private app-setting URL and account identity are intentionally omitted. Safe navigation is **Settings → Developer settings → OAuth apps → OAuth Guide validation**.

## Source-backed guide steps and current flow

For the requested OAuth App route, begin from an already signed-in provider session. Use **Settings → Developer settings → OAuth apps → New OAuth App** (or **Register a new application** on a first registration), enter app name, full homepage URL, optional description, and callback URI(s), then register. GitHub recommends considering GitHub Apps for fine-grained permissions, repository selection, and independent automation, but OAuth Apps remain the selected route here. [Creating](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app).

For a new local test, use a loopback callback such as `http://127.0.0.1:8765/callback`, keep wildcard matching off, and leave Device Flow off for the normal web flow. Current documentation supports loopback URLs and recommends a loopback IP over `localhost`; it describes a loopback port exception. Registration acceptance was independently observed above. [Redirect URLs](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#redirect-urls).

A secure web flow builds `GET https://github.com/login/oauth/authorize` with Client ID, intended redirect URI, unguessable session-bound state, and an S256 PKCE challenge. Validate returned state. The callback code is temporary. Exchange it using `POST https://github.com/login/oauth/access_token` with the documented Client ID, Client Secret, code, redirect URI, and PKCE verifier; request JSON response and keep credentials out of logs. Use the resulting bearer token for a permitted API operation. The source currently documents PKCE support; older guidance saying GitHub OAuth Apps lack PKCE is stale. [Web flow](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#web-application-flow).

A new test app can omit scopes for read-only public information; do not request `repo`, `user`, or email access for a minimal sign-in check. No-scope is not anonymous: the app can still identify the authorizing account from public profile data. Prior grants can cause omitted scope to reuse previously authorized permissions, so inspect granted scopes rather than assume. [Scopes](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps), [authorize parameter behavior](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#1-request-a-users-github-identity).

Current registration defaults to expiring access tokens. Documentation describes eight-hour access tokens, refresh tokens expiring after six months without use, and rotation via refresh. A generated guide should account for the selected expiry mode rather than claim OAuth App tokens never expire. [Expiring tokens](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#expiring-access-tokens).

## Evidence boundary and next action

**Validated live:** existing signed-in access, personal registration UI, current field labels/defaults, loopback URLs accepted, app successfully created, Client ID section, separate secret-generation button, and zero authorized users.

**Not attempted:** secret generation, consent screen, callback delivery, authorization-code exchange, token storage, API read, refresh, user revocation, organization approval, or provider approval. No mock test is counted as live OAuth validation.

No immediate human action is needed for the completed registration. To continue end-to-end, the app needs a minimal local confidential-client callback and secure secret handoff plus user consent. No existing secret-safe test harness is established in this run; a secret was deliberately not generated merely to display it. Do not ask the user to paste a secret/code/token into chat. Stop for the user's action if GitHub presents password/MFA or consequential consent. No approval/wait estimate is supported or claimed.

Sanitized source summary: `/tmp/github-oauth-validation/claude-summary.md`. This report contains the complete practical findings; raw CLI logs are not deliverables because they include internal run identifiers.
