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

function effortCard(label, item) {
  return el("div", { class: "card" },
    el("div", { class: "label" }, label),
    el("div", { class: "value" }, item?.estimate || "Unknown"),
    el("p", { class: "hint" }, item?.basis || "No supported estimate."));
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
        s.actor ? el("span", { class: "badge neutral" }, s.actor) : null),
      el("p", {}, s.detail), settings, test, checkNote(results[s.id]), sourceLink(s.source));
  });

  const prereqs = (g.prerequisites || []).map((p, i) =>
    el("li", {}, p.text, checkNote(results[`prerequisite-${i + 1}`]), sourceLink(p.source)));

  const gaps = (g.gaps || []).map(gap => el("li", {},
    gap.critical ? el("span", { class: "badge gap" }, "Blocks completion") : null, " ", gap.text,
    gap.next_action ? el("p", { class: "hint" }, "Next action: " + gap.next_action) : null));

  const sources = [...new Set([...(g.prerequisites || []), ...g.steps].map(x => x.source?.url).filter(Boolean))];

  document.getElementById("guide").replaceChildren(
    el("p", { class: "eyebrow" }, "OAuth setup roadmap"),
    el("h1", {}, g.name),
    el("div", { class: "status-row" },
      el("span", { class: `badge ${status === "complete" ? "ok" : "gap"}` }, status === "complete" ? "All steps source-checked" : status === "incomplete" ? "Incomplete" : "Not checked"),
      el("span", { class: "hint" }, v ? `Checked ${v.checked_at} · ${v.method}` : "No evidence check recorded.")),
    el("p", { class: "lede" }, g.summary),
    el("section", { class: "cards" }, effortCard("Your active effort", g.effort?.active), effortCard("Provider waiting time", g.effort?.wait)),
    prereqs.length ? el("section", {}, el("h2", {}, "Before you start"), el("ul", { class: "plain" }, prereqs)) : null,
    el("section", {}, el("h2", {}, "Steps"), el("ol", { class: "steps" }, steps)),
    el("section", {}, el("h2", {}, "Gaps and open questions"),
      gaps.length ? el("ul", { class: "plain" }, gaps) : el("p", { class: "hint" }, "None recorded.")),
    el("section", {}, el("h2", {}, "Sources"),
      el("ul", {}, sources.map(u => el("li", {}, el("a", { href: u, target: "_blank", rel: "noopener" }, u))))));
}

const slug = new URLSearchParams(location.search).get("slug") || "";
fetch(`/guides/${encodeURIComponent(slug)}.json`, { cache: "no-store" })
  .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
  .then(render)
  .catch(() => document.getElementById("guide").replaceChildren(
    el("h1", {}, "Guide not found"), el("p", {}, el("a", { href: "/" }, "Search for an app"))));
