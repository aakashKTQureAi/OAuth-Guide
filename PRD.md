# OAuth Setup Guide — Product Requirements

Status: Working notes from brainstorming. Product scope and architecture are not finalized.

## Working process

- User requests notes, safe screenshots, and a guide/workflow produced alongside practical OAuth validation. This is the behavior the research/validation service behind the web application should ultimately reproduce. Screenshots must exclude credentials, authorization codes/tokens, account identifiers, and unrelated browser content; missing captures remain explicit, never reconstructed as live evidence.
- User preference: use Claude by default for project research and practical validation activities. Verify actual Claude use and report unavailable tools or host automation separately; do not attribute host browser actions to Claude. This preference does not replace the web product's user-provided model-access decision.
- Brainstorm together using the Elephant and Goldfish workflow before finalizing a plan.
- Keep this document current as ideas, questions, and decisions emerge.
- Use the Excalidraw skill for system designs; update the same diagrams as the design changes.
- Finish with a PRD, system design, and an implementation plan.
- Run fresh-context Goldfish reviews after the brainstorming readiness checkpoint is approved.

## Assignment

Help developers and AI agent builders understand and advance through provider OAuth app registration and approval, so their users can connect accounts.

The intended library eventually covers 100 OAuth apps. The take-home needs only a few real apps with different setup challenges, plus live guide generation for unfamiliar apps supplied by name or website.

Budget: 6–8 hours. A focused working slice is sufficient. Paid accounts, completed provider approvals, and production readiness are not required. Credentials must stay out of the submission.

## Required user outcomes

Confirmed guide-delivery preference: provide visually appealing HTML that opens in a browser, with screenshots, workflow, sources, setting explanations, and evidence labels. Markdown may remain the editable source; it is not the only review artifact. A portable HTML guide must preserve local-versus-production examples and tested-versus-documented limitations.

Confirmed product boundary: guide developers through a web interface, rather than perform provider setup on their behalf. The product's research service investigates providers and generates guidance. Developers follow the instructions, configure their own OAuth registrations, and submit any required approval requests. Practical setup attempts remain part of our research and validation for the assignment, not an automated setup feature offered to users.

- Find a provider and obtain a useful, shareable guide.
- Understand where to start and what to do next.
- Distinguish developer effort from provider approval waiting time.
- See prerequisites, provider-specific requirements, and likely blockers.
- Understand what an agent can do and what requires human action.
- Distinguish tested behavior, documented requirements, and unresolved uncertainty.

## Required demonstration and submission

- Demonstrate several real apps with varied challenges.
- Generate a guide live for an unfamiliar app.
- Check a sample against real sources or setup attempts; report findings, corrections, and unverified claims.
- Supply a working experience URL and source repository.
- Include README setup instructions, key decisions, and limitations.

## Research foundation

An OAuth app is a provider registration for an integration. A user connection is an individual authorization through that registration. Registration, test access, and approval for wider distribution are separate milestones whose requirements must be checked per provider.

Composio can supply an OAuth app for supported OAuth methods. Developers can also register their own app for requirements such as consent branding, custom scopes, or separate rate-limit quota.

Source checked October 28, 2026: https://docs.composio.dev/toolkits/managed-auth

## Hypotheses to explore

- Searchable guides and live investigation may form the core experience.
- Next actions, blockers, evidence, and uncertainty may be more useful than a long prose tutorial.

These are proposals, not agreed product decisions.

## Primary entry flow

Current user direction: deliver a web interface, replacing the skill implementation. Developer enters an app name or website, the product checks for an existing guide, and otherwise researches and generates an OAuth setup and approval guide.

Keep the ready-made library for lookup and reuse as a secondary browse path. The assignment requires both the library and live unfamiliar-app generation. The input-first web mockup is a design reference for the selected surface, not a working research implementation.

App name or website must be sufficient to begin. The earlier suggestion to require intended actions and audience is not an accepted requirement. A generated guide should identify conditional requirements and uncertainties rather than silently assume a use case. Whether to offer optional refinement remains open.

The user also proposed submitting an app's documentation URL directly. The research service should inspect that documentation for OAuth registration, implementation, and approval requirements, then return a clean, precise setup workflow diagram alongside actionable guidance. Diagram steps must have the same source support and uncertainty handling as prose; a diagram must not turn missing evidence into an asserted step. Support app-name discovery for the assignment's unfamiliar-app demo even when no documentation URL is supplied.

### First screen — accepted for now

- Headline: "Get your OAuth setup roadmap."
- Short explanation: sourced setup and approval steps, prerequisites, effort, provider waiting time, and blockers.
- Primary input accepts an app name, website, or documentation URL; action is "Find or generate guide."
- Compact model-connection status and "Connect model" action. Connection settings expose provider, model, credentials, and applicable endpoint, rather than crowding the primary research input.
- Secondary "Browse existing guides" entry; no dominant pre-listed app catalog.
- Source-backed guidance promise with honest uncertainty, not a guarantee of provider approval or universal correctness.

The user accepted the first-screen layout for now and is walking through the website-URL submission path. The layout is not yet implemented in the mockup.

Proposed behavior: library lookup does not require model credentials. Open a suitable saved guide directly; prompt for model connection only when fresh research or refresh needs inference. No mandatory account/signup step is proposed for the initial slice. Detailed submission behavior remains under discussion.

## Guide reuse and library growth

User direction: save a generated provider guide in the library and reuse it when the same application is requested again, rather than researching from scratch on every request.

Proposed flow: resolve the app identity from the submitted name or website, check the library, return an existing guide if suitable, otherwise research and generate a guide, then save it for subsequent requests. Preserve source links and uncertainty alongside the saved guidance. Failed or incomplete research must not be presented as a verified complete guide.

Freshness is an unresolved design issue: show when information was checked and offer a way to refresh it. Automatic expiry rules are not decided. Reusing a provider guide must not imply that every permission set or distribution scenario has identical requirements.

## Evidence and correctness discussion

### Public research versus authenticated validation

User clarified that "agent" in the desired product means the service behind the web application. It should be able to investigate steps, record evidence, and assemble a usable workflow guide. Authenticated browser access for this service remains an implementation dependency; a visitor being logged in does not automatically connect that session to the website.
Confirmed user assumption for hands-on validation: the user is already signed into the target application, such as GitHub. Verify the available authorized browser session before attempting setup; this is a precondition, not a claim that every visitor is signed in. Missing login or permissions must produce an explicit human handoff.

Reading Atlassian's public developer documentation does not require the visitor to log into Jira. Interacting with the developer console, creating an integration, or testing user authorization requires appropriate authenticated access. If that access is unavailable, report the precise validation limit rather than claiming the steps were exercised.

Our practical Jira attempt used the user's existing local signed-in Chrome session. A deployed website does not automatically inherit visitors' Jira sessions, cookies, or desktop-browser access. It must not imply that supplying a model API key grants Jira access.

Proposed initial behavior: visitors can receive documentation-backed guides without providing Jira credentials. Validate a sample of provider flows using explicitly authorized test accounts during product development and retain that evidence with its conditions. Per-visitor authenticated browser automation is a separate capability, not an assumed feature of this guidance-only product. Guides clearly distinguish documentation-backed, console-observed, authorization-tested, and approval status.

Confirmed user requirement: trust is essential. Generate guides only from verified sources; do not invent provider instructions, requirements, or approval timelines. This applies to newly generated guides and reused library guides.

Source-backed publication rules:

- Use official provider documentation as the default authority for provider registration, permissions, and approval requirements. Use a platform's own documentation for claims about that platform, such as Composio-managed OAuth availability. Check source identity, relevance, and retrieved content; a search result or plausible URL alone is insufficient.
- Every actionable provider-specific step and material claim must link to evidence that supports the claim, with the applicable conditions and checked date. Generating a citation does not prove that the source supports the instruction.
- Label local/test configuration values beside the value itself and provide clearly marked production examples where useful. Explain which values belong to the developer's agent application versus the guide website. Do not present an illustrative domain or callback path as deployed or tested production configuration.
- Explain each configuration field beside its value: what it does, why it is needed, and when to enable, disable, leave blank, or retain the default. Source decision rules and distinguish observed settings from untested alternatives; copied test values alone are not sufficient guidance.
- Put a prominent per-step validation label where a step was actually tested, followed by plain-language action, result, test scope/date, executor, and limits. Separate instructions the developer must perform from the agent's completed test record. "Tested" must not imply Claude executed host-only actions or the deployed web app already has this capability.
- If sources are unavailable, incomplete, outdated, or conflicting, identify the exact gap and offer the next research or human verification action. Do not fill gaps from model memory and present them as confirmed facts.
- Distinguish documentation-backed guidance from steps observed in the console, end-to-end authorization tests, and actual provider approval. These are different evidence levels.
- A guide with unresolved critical requirements must remain visibly incomplete. Saving or reusing a guide does not upgrade its evidence status.
- Model review can help flag missing or unsupported claims, but does not itself verify a provider flow. The exact checking implementation remains open.

User asked how we know the Gmail steps shown in the mock are the actual provider steps. Inspection confirms the prototype uses a shared generic checklist for all apps; inserting the app name does not make it provider-specific. It is labeled unverified demo content. Claude's UI review and browser interaction checks do not establish OAuth instruction correctness.

Proposed requirements for the real guide generator:

- Research official provider documentation and identify the correct app and OAuth method.
- Tie each provider-specific instruction and important claim to a supporting source, including when it was checked and the conditions where it applies.
- Separate documented requirements, directly observed setup steps, successful authorization tests, and unknowns. Do not label a whole guide verified based only on sources or a reviewer model agreeing.
- Check actual console steps and a minimal authorization flow for a sample of providers where practical; record where access or approval prevents testing.
- Validate source support and required coverage before saving a guide as ready-to-use. Partial results remain explicitly incomplete, rather than becoming trusted merely because they are cached.
- Separate active effort estimates from provider wait estimates; omit unsupported timelines or mark them unknown.

Gmail documentation spot-check, October 28, 2026: Google documents Cloud project creation, API enablement, OAuth consent configuration, and OAuth credentials. Scope choice materially changes the approval path: Gmail read-only is classified restricted, while sending mail is classified sensitive. These findings are documentation-backed, not tested in a Google account.

Sources:
- https://developers.google.com/workspace/guides/get-started
- https://developers.google.com/workspace/guides/configure-oauth-consent
- https://developers.google.com/workspace/guides/create-credentials
- https://developers.google.com/workspace/gmail/api/auth/scopes
- https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification

## Jira Cloud research example

Current validation target has switched to GitHub OAuth at the user's request. Jira findings below remain partial evidence; its developer-terms gate was not completed. GitHub research and practical outcomes will be recorded separately after observation.

### GitHub validation scope

GitHub test OAuth App registration succeeded. User explicitly extended validation to actual OAuth authorization and read-only agent use, with Claude as default executor. Target evidence: validated callback, real token exchange, and Claude invoking a constrained local client for a harmless authenticated API read. Secrets must stay outside model context, output, and logs. Host browser automation may assist consent but must be identified separately from Claude's actions. No repository writes, broad OAuth permissions, organization changes, or harmful modifications are authorized.

Latest user safety override: Claude need not execute the test if local/host automation is safer. Prefer the safest supported executor without extra model orchestration solely to demonstrate Claude use. Report host-only testing as host-only; it does not prove Claude independently completed OAuth. Actual token exchange and authenticated read remain the validation target.

Registration alone does not establish token exchange or API success. A local temporary test harness is validation tooling, not implementation of the website. Final outcomes and any remaining test app, credentials, or grants must be reported explicitly.

Latest observed boundary: a temporary loopback read-only client was prepared and passed syntax compilation, but GitHub requested additional "Confirm access" verification when generating the test app's secret. No secret was obtained, listener started, token exchanged, or API request made. [End-to-end attempt report](./research/github-oauth-end-to-end-validation.md).

The user will complete verification directly in GitHub and has authorized retry after confirming it is done. This is conditional authorization, not evidence that verification has already succeeded. Do not request the verification code through chat.

Resumed validation after user confirmation: GitHub verification cleared, existing test secret reused without duplicate generation, public-data-only consent completed, and callback state matched. Token exchange failed before receiving an HTTP response because the local Python trust store could not verify GitHub. A system CA bundle fix was checked with TLS verification enabled, but the OAuth exchange has not yet been successfully retried.

Browser automation then reset. Safe blank-tab recovery API was unavailable; reacquiring the native app could expose a one-time secret page. Current human handoff: open a new blank Chrome tab while leaving the secret page open. No token or authenticated API result yet. Listener stopped; transient local credential input removed. Test app, one secret, and public-data consent remain. These are partial validation results, not end-to-end success.

Latest recovery update: user reported the blank tab ready and authorized screen inspection. Parent capture confirmed Chrome New Tab active, with no secret visible. Validation and evidence-guide creation are resumed; token/API outcome remains unconfirmed until new results are recorded.

### GitHub end-to-end result — completed

The resumed local test succeeded: callback/state validated, S256 PKCE used, token exchange returned HTTP 200 with empty granted scopes, and exactly one authenticated read of the current-user endpoint returned HTTP 200 with empty API scope header. Sanitized results were checked. An expiring access token and refresh token were returned, but refresh was not exercised.

[Screenshot-supported guide](./research/github-oauth/guide.md) · [Sanitized results](./research/github-oauth/result.json) · [Full validation](./research/github-oauth/validation.md) · [Observed Excalidraw workflow](./research/github-oauth-workflow.excalidraw)

Primary browser-review artifact: [portable HTML guide](./research/github-oauth/guide.html), with four embedded images, configuration explanations, plain-language consent/token sections, and prominent per-step validation outcome. Markdown remains editable source. [HTML checks](./research/github-oauth/html-validation.json) recorded source-content parity and desktop/mobile checks; print layout is included but printed output was not tested.

Three safe screenshots are included: two capture official documentation and one captures the actual query-free callback completion page. They are labeled by evidence type. Earlier registration, credential creation, and consent were observed without retained screenshots; documentation captures do not prove those actions occurred. API success is supported by sanitized execution results, not the completion screenshot alone.

Claude researched official sources, rechecked the plan, and drafted notes; host browser automation and the local client executed live OAuth/API steps. Host review corrected attribution and unsupported draft instructions. This validates local read-only OAuth, not independent Claude token use or deployed-web-app readiness.

Listener stopped, transient credential inputs removed, and tokens discarded from local process memory. The GitHub test app, one secret, and public-data grant remain; they were not deleted or revoked. No repository content, organization settings, broader scopes, publishing, or harmful modifications were involved. Refresh, revocation, production deployment, and approval timing remain untested/unknown.

The user selected Jira Cloud and explicitly requested Claude-led research of authentic OAuth configuration steps. [Research evidence and guide](./research/jira-cloud-oauth.md) records two successful installed Claude CLI invocations and eight successful source-fetch calls across seven official Atlassian pages.

Documented path: create a Cloud OAuth integration, choose account-level or resource-level grant, choose scopes from intended endpoints, configure callback, implement consent and code exchange, identify authorized sites and test a permitted API call, optionally support refresh tokens, and enable sharing when distributing. Creation, sharing, Marketplace listing, and Atlassian approval are separate milestones.

Evidence status: documentation-backed only. No account configuration, authorization test, provider approval, or supported effort/wait estimate. Official wording conflicts and unresolved review/admin details remain explicit in the research artifact. The product must not present this as a completed integration.

### Practical validation attempt

User authorized Claude-assisted practical setup attempts. [Validation report](./research/jira-cloud-oauth-validation.md) records live access to Atlassian Developer Console through an existing signed-in Chrome session, opening the Create flow, and observing Resource-level and Account-level grant options. A private test creation form was prepared with name "OAuth Guide validation" and Resource-level selected.

Creation is blocked by required acceptance of Atlassian developer terms. Checkbox was left unchecked; no test app was created. User must review and accept terms and click Create before registration validation can continue. Callback configuration, scopes, credentials, consent, and API tests remain unvalidated.

Claude successfully fetched instructions but its Chrome connection returned no tabs. Host computer automation operated the actual console; do not claim Claude directly performed browser actions. This report adds observed-console evidence without upgrading untested later steps.

## Integration surface discussion

### Private customized guide

A customized GitHub OAuth App guide for an internal service was produced separately and is kept outside this repository. Its reusable lesson: a classic OAuth App can read private repository contents only with the broad `repo` scope, which also grants write access; it cannot issue a repository-selected, read-only token. Guides must disclose this tradeoff and show GitHub Apps as the narrower alternative.

### Current decision and assumptions

The user explicitly switched back to a web interface. This supersedes the skill-first direction. Skill, MCP, and external API delivery interfaces are outside the current initial scope.

Our product must arrange source-retrieval tools and model orchestration for live guide generation. Confirmed decision: each user supplies their own model API credentials through the web interface. The visitor does not need to supply a compatible agent or research tools. Supported providers, endpoint configuration, usage limits, and deployment remain unresolved; no model service is promised by the assignment.

Historical assumption, now superseded: the skill-first proposal assumed the developer's host agent supplied configured model access and source-retrieval tools, consuming the host's quota. That assumption must not be used to claim the web product has live research capabilities.

If model access or source retrieval is unavailable, report the missing capability instead of presenting model-memory output as freshly researched guidance.

Assignment interpretation correction: the brief says "You decide the approach, format, and implementation." It does not require a standalone website or prohibit a skill. It does require a working experience link, source repository, varied examples, and live unfamiliar-app guide generation; skill-first packaging must still demonstrate those outcomes.

The web experience returns source-backed steps, prerequisites, blockers, effort, and expected provider waiting time where evidence supports an estimate.

The product owns research orchestration, evidence rules, guide output, and library lookup/reuse. A separate agent framework or a particular backend topology is not yet selected.

There are three distinct roles:

1. The developer or their coding assistant prepares the integration before launch.
2. Our research agent investigates providers and creates evidence-backed guides.
3. The developer's deployed agent uses provider APIs with users' authorization.

The assignment requires research capability to help the developer. Our product's research service provides that capability. The developer's own agent uses provider APIs separately after setup and user authorization; it does not need our skill installed.

Possible surfaces:

| Surface | How it fits | Tradeoff |
| --- | --- | --- |
| Web app | Developer searches, requests research, follows steps, and shares a guide URL. | Directly demonstrates the brief; initially requires leaving their coding environment. |
| Skill | A compatible coding assistant follows our setup workflow and references guides. | Useful development-time entry point; execution capabilities depend on the host and available tools. |
| MCP | A compatible agent calls our guide lookup or research service as tools. | Direct access from existing agents; server and client setup add scope. |
| HTTP API | Existing applications call the guide service directly. | General programmatic interface; callers must integrate it. |

The surface comparison above records alternatives considered. Web is selected. Model access, research tooling, persistent library storage, shareable guide URLs, and hosting need concrete implementation choices.

### Model access and cost

The user proposed explicit model-connection sections in the web experience: provider/connection type, API endpoint or base URL where applicable, model, and API key or access token where required. These configure model inference, not the provider OAuth app being researched. Documentation URL is a separate research input. Source search and page retrieval are separate capabilities and must be implemented even when a model endpoint is configured.

Confirmed product decision: users supply their own model API key or access token and applicable endpoint/model configuration. Model usage is billed to or limited by the user's provider account. The website uses those credentials for guide research and generation; it does not collect OAuth credentials for the app being researched. Connection checks must distinguish successful model access from working source retrieval; neither establishes guide correctness.

Credential lifetime remains to be decided. The smallest proposed default is session-only use with no durable credential storage; persistent saved connections are not an accepted requirement. No credentials should be requested through this planning chat.

Credentials must be handled by the backend or an appropriate secret store, excluded from guide output, logs, screenshots, and submission. The mockup's browser-local guide persistence must not be reused to persist model API keys. Model access configuration is a proposed UI section; actual credential storage and connection code are not yet implemented.

The user raised cost/access as a reason to consider skill-first. A standalone hosted product needs model inference access and research tools arranged by us. A skill can use its supported host agent's existing model access and research tools, shifting rather than eliminating inference cost and limits. No new implementation decision follows merely from exploring standalone costs.

Official documentation checked October 28, 2026: Gemini Developer API offers free tiers for eligible models with limits; actual account/model/tool availability must be checked before relying on it for a demo. Claude subscription and Claude API access have separate billing. Our verified Claude Code login does not establish free hosted API access. No API account or free quota has been verified for this project.

Sources: https://ai.google.dev/gemini-api/docs/pricing ; https://support.claude.com/en/articles/9876003-i-have-a-paid-claude-subscription-pro-max-team-or-enterprise-plans-why-is-claude-api-usage-billed-separately-from-my-paid-claude-plan

## Inspiration research

Official pages reviewed October 28, 2026. Documentation review only; no products installed or setup flows tested.

- **Composio:** Managed OAuth can supply the registration for supported methods; developers may bring their own registration. Inspiration: explain whether custom registration is necessary before giving setup steps. Source: https://docs.composio.dev/toolkits/managed-auth
- **Nango coding-agent setup:** Explicitly distinguishes coding-agent integration work from exposing integrations to a product's agents. Offers management MCP, documentation MCP, and skills. Inspiration: separate development-time assistance from runtime integration. Source: https://nango.dev/docs/getting-started/coding-agent-setup
- **Nango auth:** Documents managed authorization, pre-approved apps, and a recommendation to use a developer's own app before launch for branding, scopes, and control. Inspiration: distinguish starting a prototype from launch preparation. Source: https://nango.dev/platform/auth/
- **Pipedream Connect:** Offers managed auth and runtime API/tool access through SDK/proxy and MCP. Inspiration: several interfaces can share a backend, while runtime token management is a distinct product responsibility. Source: https://pipedream.com/connect
- **Agent Skills:** Packages procedural knowledge, scripts, and resources for compatible agents. Source: https://agentskills.io/home
- **MCP:** Standardizes tools, resources, and prompts exposed to AI applications. Source: https://modelcontextprotocol.io/docs/learn/server-concepts

These are adjacent products and interface patterns, not verified equivalents of an OAuth approval guide generator.

## Open questions

- What does the developer arrive knowing, and what immediate decision should the product help them make?
- How much does intended use, requested access, or distribution change the guide?
- Which providers best demonstrate different setup and approval paths?
- What setup work can agents safely attempt within the time budget?
- What evidence is sufficient to publish a claim or estimate?
- What is the smallest credible live-generation experience?
- What already exists in the project, and what deployment/model access is available?

## System design

### Live generation architecture discussion

The assignment explicitly requires an agent to investigate submitted apps and generate shareable guides in real time, including unfamiliar apps. It also asks for practical agent-led investigation and setup attempts to inform the guidance. Live investigation and generation are required capabilities, not optional scope additions. The brief does not prescribe an LLM vendor, agent framework, or particular backend topology.

The HTML mockup currently uses preset generic content and simulated research timing. It has no LLM-backed research service. Claude reviewing the UI does not mean the product is connected to Claude for guide generation. The mockup alone does not fulfill the live-generation requirement.

Current proposed flow: developer enters an app name or website in the web interface -> backend library lookup -> on a miss, product research tools obtain official documentation -> a model structures a guide from evidence -> evidence checks flag unsupported claims and critical gaps -> save the guide and its sources/status -> return a shareable guide page. Existing guides can be reused with their evidence status and checked date intact.

Our product arranges model inference and research tools. Without research access, the service must report that limitation instead of claiming a current guide was researched. Evidence checks reduce unsupported claims but do not guarantee correctness or constitute provider approval.

Model access, search/fetch tools, persistent library storage, sharing, and deployment remain open. This is architecture brainstorming, not authorization to start production implementation.

[Living Excalidraw sketch](./oauth-guide-design.excalidraw) · [PNG preview](./oauth-guide-design.png)

Living sketch records the current web direction and proposed guide reuse/research flow. It is a discussion artifact, not an approved architecture or final user flow.

## Decisions recorded 2026-10-28 (mock build)

- **Evidence model:** guides are generated live from official sources and gated by a validator that re-fetches every cited page and requires the quoted text. A sample is tested hands-on (GitHub, two end-to-end runs). Testing every app before publishing was considered and rejected: the brief asks to attempt setup "as practical" and to watch unfamiliar apps generate live, which human-only gates (Confirm access, 2FA, terms) make impossible.
- **Time:** every guide shows OAuth setup time (console to first sign-in; measured where tested, labeled estimate otherwise) and a separate build-into-your-app estimate with stated assumptions.
- **Approval wait:** only approvals that gate other users from connecting. Optional marketplace or directory listings (Slack, Atlassian) are not OAuth setup and are excluded.
- **Handoffs and difficulty:** every step says whether an agent can do it or the developer must take over, and why; every guide carries an easy/moderate/hard rating with a reason.
- **Mock status:** the research agent is Claude in a Claude Code session watching a request queue. The production research service (visitor-supplied model key, server-side pipeline, deployment) is not built.

## Implementation plan

Pending: plan the production web app (model connection, server-side research pipeline reusing the validator, deployment).

## UI exploration request

Earlier web exploration produced an HTML mockup in the mockup chat's worktree. Codex authored it and Claude reviewed it. It uses simulated research and browser-local storage; provider guidance is generic and unverified. Retain as a design reference for the restored web direction. It does not yet satisfy live research or shared persistence requirements.
