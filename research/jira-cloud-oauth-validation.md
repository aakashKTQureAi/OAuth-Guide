# Jira Cloud OAuth practical validation

Date: 2026-10-28. Scope: attempt reversible private Jira Cloud OAuth setup using Claude and the existing browser; no distribution, paid activity, approval submission, or Jira writes.

## Result

Live Atlassian Developer console access succeeded using the existing Chrome session. No login or MFA was required. Setup reached the real **Create a new OAuth 2.0 (3LO) integration** form, and stopped at required agreement to **Atlassian's developer terms**. No integration has been created. The user needs to accept the terms and click Create in the open form if they want validation to continue.

The form is prepared with name **OAuth Guide validation** and **Resource-level** selected. The agreement checkbox remains unchecked and Create remains disabled. This is an unsaved form only; no scopes, callback, credentials, distribution, or grants have been configured.

## Who did what

- **Installed Claude CLI:** actually invoked using the existing authenticated account with Chrome integration enabled and scoped public WebFetch tools. The CLI exposed browser-control tools, but its `list_connected_browsers` call returned `[]`. Thus Claude could not directly control Chrome through its integration. It did not install or connect anything.
- **Claude source check:** fetched the current official Jira Cloud 3LO guide and scope catalog, and produced a practical setup/check plan. Its endpoint-reference fetch did not expose the required endpoint-specific scope section, so that proposed scope remains provisional.
- **Host computer automation:** used native Chrome accessibility controls through CUA to open the developer console in a new tab, inspect the form, enter the test name, and select Resource-level. Host automation performed all live browser actions. Claude did not directly operate that browser.
- **Execution evidence:** Claude process exited 0, final result subtype `success`, `is_error: false`. Actual public source-fetch tool results were present. Connection status was an empty list, not a successful browser connection. Raw prompts, private URLs, emails, identifiers, and credentials are omitted from this report.

## Observed live steps and corrections

1. Opened `https://developer.atlassian.com/console/myapps/` in a new Chrome tab. The existing account reached **Developer console**. The page showed **My apps**, a **Create** menu, and **No apps assigned yet** for the selected developer space. Existing apps were not changed or inspected.
2. Clicked **Create**. Menu contained **Get started with Forge** and **OAuth 2.0 integration**. Selected OAuth 2.0 integration.
3. Observed **Create a new OAuth 2.0 (3LO) integration**. The visible form had **Name**, **Access type**, **Resource-level**, **Account-level**, an agreement checkbox, **Create**, and **Cancel**.
4. The form confirmed the current source's grant choice. Live **Resource-level** text describes restricting access to the specific site selected during authorization. **Account-level** describes access across resources within the customer's account. Neither radio was selected initially.
5. A visible notice states that new OAuth integrations must use rotating refresh tokens. This notice does not mean the test should request `offline_access`; no refresh flow was attempted.
6. Entered **OAuth Guide validation**, selected **Resource-level**, and verified the changed form values.
7. Observed the required unchecked agreement **I agree to be bound by Atlassian's developer terms.** The Create button was disabled. Stopped before acceptance or submission.

### Why the stop is required

The computer-use confirmation policy explicitly requires action-time confirmation before accepting a legally binding agreement. The earlier general instruction to try setup does not waive that requirement. No login blocker exists; the minimal human action is accepting the displayed developer terms and creating this prepared private test integration. Creation is expected to generate persistent API credentials; none currently exist for this proposed app.

## What remains unvalidated

- Whether private creation succeeds and the resulting app is private by default.
- Scope-picker labels and actual endpoint-required read-only scope.
- Whether a local HTTP callback is accepted, or what validation constraints the form applies.
- Credentials' UI presence/location; no credential values were viewed or copied.
- Authorization/consent, accessible-resources, API read, refresh, and site-admin restrictions.
- Distribution and Atlassian review: deliberately not attempted.

Claude proposed `GET /rest/api/3/myself` with classic `read:jira-user` for a read-only test, but the direct endpoint reference fetch was truncated/empty. Treat that as a candidate to verify against the actual operation docs before adding scopes. No write/manage scopes or `offline_access` were requested.

## Supporting public sources

- [Jira Cloud OAuth 2.0 (3LO)](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/) — Claude successfully fetched; live creation UI agrees on grant choice.
- [Jira scope catalog](https://developer.atlassian.com/cloud/jira/platform/scopes-for-oauth-2-3LO-and-forge-apps/) — Claude successfully fetched; scope descriptions do not independently prove every endpoint's required scope.
- [Current-user operation reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-myself/#api-rest-api-3-myself-get) — attempted fetch did not reveal the required operation section; no endpoint-specific claim is treated as verified.
- [Atlassian developer terms](https://developer.atlassian.com/platform/marketplace/atlassian-developer-terms/) — linked on the live required agreement; not accepted.

No raw screenshots are provided because the Chrome window includes unrelated tab titles and account controls. Evidence is the sanitized live UI observation above; it is not a screenshot-backed success claim.

## Resume location and status

**Status: needs-user-action.** Current Chrome tab is **Developer console**, displaying **Create a new OAuth 2.0 (3LO) integration** at `https://developer.atlassian.com/console/myapps/create-3lo-app`. Prepared name: **OAuth Guide validation**; access type: **Resource-level**. Parent should ask the user to review/accept developer terms and click Create themselves, then resume after confirmation. Do not accept or submit on the user's behalf in this stopped run.
