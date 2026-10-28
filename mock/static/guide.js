// Renders /guides/<slug>.json. All guide text is inserted as text, never as HTML.
const EVIDENCE = {
  "documented": ["Documented", "info", "Supported by official documentation; not exercised by us."],
  "console-observed": ["Console observed", "warn", "Seen in the provider console during our research."],
  "auth-tested": ["Authorization tested", "ok", "Exercised end to end in a real test; see the test record."],
};

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v; else node.setAttribute(k, v);
  }
  for (const c of children.flat()) if (c != null) node.append(c);
  return node;
}

function sourceLink(source) {
  if (!source || !source.url) return el("span", { class: "fail" }, "No source");
  const host = new URL(source.url).hostname;
  return el("details", { class: "source" },
    el("summary", {}, "Source: ", el("a", { href: source.url, target: "_blank", rel: "noopener" }, host)),
    el("blockquote", {}, source.quote || ""));
}

function checkNote(result) {
  if (!result) return el("p", { class: "check fail" }, "Not yet checked against its source — treat as unverified.");
  if (result.ok) return null;
  return el("p", { class: "check fail" }, `Source check failed: ${result.reason}. Treat this step as unverified.`);
}

function fmtMinutes(m) {
  if (m < 1) return `${Math.round(m * 60)} s`;
  if (m < 90) return `${Math.round(m)} min`;
  return `${Math.round(m / 30) / 2} h`;
}

function fmtRange(lo, hi) {
  return lo === hi ? fmtMinutes(lo) : `${fmtMinutes(lo)}–${fmtMinutes(hi)}`;
}

function timeNote(t) {
  if (!t) return null;
  const label = t.kind === "measured" ? `Measured ${t.measured_on}` : "Estimate, not measured";
  return el("p", { class: "time" },
    el("span", { class: `badge ${t.kind === "measured" ? "ok" : "neutral"}` }, `⏱ ${fmtRange(t.min_minutes, t.max_minutes)}`),
    ` ${label} — ${t.basis}`);
}

function phaseCard(g, phase, label) {
  const times = g.steps.map(s => s.time).filter(t => t?.phase === phase);
  if (!times.length) return null;
  const sum = (kind, key) => times.filter(t => !kind || t.kind === kind).reduce((n, t) => n + t[key], 0);
  const measured = times.filter(t => t.kind === "measured");
  const note = !measured.length ? "Estimate, not measured."
    : measured.length === times.length ? "Measured in a timed run."
    : `${fmtRange(sum("measured", "min_minutes"), sum("measured", "max_minutes"))} measured in a timed run; the rest is an estimate.`;
  return el("div", { class: "card" },
    el("div", { class: "label" }, label),
    el("div", { class: "value" }, fmtRange(sum(null, "min_minutes"), sum(null, "max_minutes"))),
    el("p", { class: "hint" }, note));
}

function timeCards(g) {
  const cards = [phaseCard(g, "setup", "OAuth setup: console to first sign-in"), phaseCard(g, "build", "Building it into your app")].filter(Boolean);
  if (!cards.length) cards.push(effortCard("Your active effort", g.effort?.active));
  return cards;
}

function effortCard(label, item) {
  return el("div", { class: "card" },
    el("div", { class: "label" }, label),
    el("div", { class: "value" }, item?.estimate || "Unknown"),
    el("p", { class: "hint" }, item?.basis || "No supported estimate."),
    item?.source ? sourceLink(item.source) : null);
}

function handoffSection(g) {
  const agent = g.steps.filter(s => s.who === "agent" || s.who === "agent + you");
  const you = g.steps.filter(s => s.who === "you" || s.who === "agent + you");
  if (!agent.length && !you.length) return null;
  const list = (steps, why) => el("ul", { class: "plain" }, steps.map(s => el("li", {}, s.title, why && s.handoff ? el("span", { class: "hint" }, ` — ${s.handoff}`) : null)));
  return el("section", { class: "cards" },
    el("div", { class: "card" }, el("div", { class: "label" }, "What an agent can do for you"), list(agent, false)),
    el("div", { class: "card" }, el("div", { class: "label" }, "Where you take over"), list(you, true)));
}

function render(g) {
  const v = g.verification;
  const results = Object.fromEntries((v?.results || []).map(r => [r.id, r]));
  const status = v?.status || "unchecked";
  document.title = `${g.name} OAuth setup — OAuth Guide`;

  const steps = g.steps.map((s, i) => {
    const [label, tone, why] = EVIDENCE[s.evidence] || ["Unknown evidence", "gap", ""];
    const settings = s.settings?.length ? el("table", { class: "settings" },
      el("thead", {}, el("tr", {}, el("th", {}, "Field"), el("th", {}, "Value"), el("th", {}, "What it does / when to change"))),
      el("tbody", {}, s.settings.map(f => el("tr", {}, el("td", {}, f.field), el("td", {}, el("code", {}, f.value)), el("td", {}, f.explain))))) : null;
    const test = s.test_record ? el("div", { class: "test" },
      el("strong", {}, `Test record (${s.test_record.date}): `), s.test_record.result,
      s.test_record.limits ? el("p", { class: "hint" }, "Limits: " + s.test_record.limits) : null) : null;
    return el("li", { class: "step" + (results[s.id]?.ok === false ? " failed" : "") },
      el("div", { class: "step-head" },
        el("h3", {}, `${i + 1}. ${s.title}`),
        el("span", { class: `badge ${tone}`, title: why }, label),
        s.actor ? el("span", { class: "badge neutral" }, s.actor) : null,
        s.who ? el("span", { class: `badge ${s.who === "agent" ? "info" : "warn"}` }, s.who === "agent" ? "Agent can do" : s.who === "you" ? "You take over" : "Agent + you") : null),
      s.handoff ? el("p", { class: "handoff" }, "You take over: " + s.handoff) : null,
      el("p", {}, s.detail), timeNote(s.time), settings, test, checkNote(results[s.id]), sourceLink(s.source));
  });

  const prereqs = (g.prerequisites || []).map((p, i) =>
    el("li", {}, p.text, checkNote(results[`prerequisite-${i + 1}`]), sourceLink(p.source)));

  const gaps = (g.gaps || []).map(gap => el("li", {},
    gap.critical ? el("span", { class: "badge gap" }, "Blocks completion") : null, " ", gap.text,
    gap.next_action ? el("p", { class: "hint" }, "Next action: " + gap.next_action) : null));

  const sources = [...new Set([...(g.prerequisites || []), ...g.steps].map(x => x.source?.url).filter(Boolean))];

  document.getElementById("guide").replaceChildren(...[
    el("p", { class: "eyebrow" }, "OAuth setup roadmap"),
    el("h1", {}, g.name),
    el("div", { class: "status-row" },
      el("span", { class: `badge ${status === "complete" ? "ok" : "gap"}` }, status === "complete" ? "All steps source-checked" : status === "incomplete" ? "Incomplete" : "Not checked"),
      el("span", { class: "hint" }, v ? `Checked ${v.checked_at} · ${v.method}` : "No evidence check recorded.")),
    g.difficulty ? el("p", { class: "difficulty" },
      el("span", { class: `badge ${{ easy: "ok", moderate: "warn", hard: "gap" }[g.difficulty.level]}` }, `Difficulty: ${g.difficulty.level}`),
      " ", g.difficulty.reason) : null,
    el("p", { class: "lede" }, g.summary),
    handoffSection(g),
    el("section", { class: "cards" }, timeCards(g),
      el("div", {}, effortCard("Approval wait before other users can connect", g.effort?.wait), g.effort?.wait?.source ? checkNote(results["provider-wait"]) : null)),
    g.effort?.assumptions ? el("p", { class: "hint" }, `Times assume ${g.effort.assumptions}.`) : null,
    prereqs.length ? el("section", {}, el("h2", {}, "Before you start"), el("ul", { class: "plain" }, prereqs)) : null,
    el("section", {}, el("h2", {}, "Steps"), el("ol", { class: "steps" }, steps)),
    el("section", {}, el("h2", {}, "Gaps and open questions"),
      gaps.length ? el("ul", { class: "plain" }, gaps) : el("p", { class: "hint" }, "None recorded.")),
    el("section", {}, el("h2", {}, "Sources"),
      el("ul", {}, sources.map(u => el("li", {}, el("a", { href: u, target: "_blank", rel: "noopener" }, u)))))].filter(Boolean));
}

const slug = new URLSearchParams(location.search).get("slug") || "";
fetch(`/guides/${encodeURIComponent(slug)}.json`, { cache: "no-store" })
  .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
  .then(render)
  .catch(() => document.getElementById("guide").replaceChildren(
    el("h1", {}, "Guide not found"), el("p", {}, el("a", { href: "/" }, "Search for an app"))));
