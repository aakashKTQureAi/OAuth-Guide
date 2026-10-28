"""Check a guide's evidence against live official pages and record the result in the guide.

Usage: python3 mock/validate.py mock/guides/<slug>.json   (exit 0 complete, 2 incomplete)
       python3 mock/validate.py --self-check
"""
import datetime, html, json, os, re, ssl, sys, unicodedata, urllib.parse, urllib.request

# shortcut: python.org macOS builds ship without a CA bundle; use the system one when the default store is empty.
_CAFILE = "/etc/ssl/cert.pem" if os.path.exists("/etc/ssl/cert.pem") else None
_CTX = ssl.create_default_context(cafile=_CAFILE)
_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", " ": " "})


def normalize(text):
    """Comparable form: entities decoded, NFKC, straight quotes, casefolded, all whitespace removed.

    Whitespace is dropped entirely because removed tags leave unpredictable spacing.
    """
    text = unicodedata.normalize("NFKC", html.unescape(text)).translate(_QUOTES).casefold()
    # Web fetch tools return pages as Markdown, so quotes can carry `code` or **bold** marks the HTML text lacks.
    return re.sub(r"[\s`*]+", "", text)


def page_text(raw_html):
    raw_html = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", raw_html)
    return re.sub(r"<[^>]+>", " ", raw_html)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (OAuth-Guide evidence check)"})
    with urllib.request.urlopen(req, timeout=20, context=_CTX) as resp:
        return resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="replace")


def official(url, domains):
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    return parts.scheme == "https" and any(host == d or host.endswith("." + d) for d in domains)


def anchor_domains(guide, fetched_urls, docs_url=None):
    """Keep only 'official' domains the research actually fetched (or the visitor named); a model can't vouch for unseen sites."""
    hosts = {(urllib.parse.urlsplit(u).hostname or "").lower() for u in fetched_urls + ([docs_url] if docs_url else [])}
    kept, dropped = [], []
    for d in guide.get("domains", []):
        (kept if any(h == d or h.endswith("." + d) for h in hosts) else dropped).append(d)
    guide["domains"] = kept
    for d in dropped:
        guide.setdefault("gaps", []).append({
            "text": f"{d} was proposed as an official source but was never fetched during research, so steps citing it are unverified.",
            "critical": False, "next_action": "Check that page manually."})
    return dropped


def check_claim(source, domains, get_page):
    """Return (ok, reason) for one {url, quote} source."""
    url, quote = source.get("url", ""), source.get("quote", "")
    if not url or not quote.strip():
        return False, "missing source url or quote"
    if not official(url, domains):
        return False, "source is not on an official domain"
    page = get_page(url.split("#")[0])
    if isinstance(page, Exception):
        return False, f"fetch failed: {type(page).__name__}"
    if normalize(quote) not in normalize(page_text(page)):
        return False, "quote not found on fetched page"
    return True, "quote found on official page"


def claims(guide):
    for i, item in enumerate(guide.get("prerequisites", [])):
        yield f"prerequisite-{i + 1}", item
    for step in guide.get("steps", []):
        yield step["id"], step
    wait = guide.get("effort", {}).get("wait", {})
    if wait.get("source"):
        yield "provider-wait", wait


def time_errors(guide):
    """Malformed time, difficulty or handoff data is an authoring error, not evidence: it never changes status."""
    errors = []
    d = guide.get("difficulty")
    if d is not None and (d.get("level") not in ("easy", "moderate", "hard") or not d.get("reason", "").strip()):
        errors.append("difficulty needs level easy/moderate/hard and a reason")
    for step in guide.get("steps", []):
        if step.get("who") not in (None, "agent", "you", "agent + you"):
            errors.append(f"{step['id']}: who must be agent, you, or agent + you")
        elif step.get("who") in ("you", "agent + you") and not step.get("handoff", "").strip():
            errors.append(f"{step['id']}: steps that need you must say why in handoff")
    for step in guide.get("steps", []):
        t = step.get("time")
        if t is None:
            continue
        lo, hi = t.get("min_minutes"), t.get("max_minutes")
        if t.get("kind") not in ("measured", "estimate"):
            errors.append(f"{step['id']}: time.kind must be measured or estimate")
        elif t.get("phase") not in ("setup", "build"):
            errors.append(f"{step['id']}: time.phase must be setup or build")
        elif not (isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and 0 <= lo <= hi):
            errors.append(f"{step['id']}: time needs 0 <= min_minutes <= max_minutes")
        elif not t.get("basis", "").strip():
            errors.append(f"{step['id']}: time needs a basis")
        elif t["kind"] == "measured" and not t.get("measured_on"):
            errors.append(f"{step['id']}: measured time needs measured_on")
    if any(s.get("time", {}).get("kind") == "estimate" for s in guide.get("steps", [])) \
            and not guide.get("effort", {}).get("assumptions", "").strip():
        errors.append("effort.assumptions is required when any step has an estimate")
    return errors


def verify(guide, get_page, progress=None):
    results = []
    todo = list(claims(guide))
    for i, (claim_id, item) in enumerate(todo, 1):
        if progress:
            host = urllib.parse.urlsplit(item.get("source", {}).get("url", "")).hostname or "an unknown site"
            progress(f"Checking quote {i} of {len(todo)} on {host}")
        ok, reason = check_claim(item.get("source", {}), guide["domains"], get_page)
        if ok and item.get("evidence") == "auth-tested" and not item.get("test_record"):
            ok, reason = False, "auth-tested without a test record"
        results.append({"id": claim_id, "ok": ok, "reason": reason, "url": item.get("source", {}).get("url", "")})
    critical_gaps = [g for g in guide.get("gaps", []) if g.get("critical")]
    complete = all(r["ok"] for r in results) and not critical_gaps
    guide["verification"] = {
        "checked_at": datetime.date.today().isoformat(),
        "method": "plain HTTPS fetch, tags stripped, normalized text match",
        "status": "complete" if complete else "incomplete",
        "results": results,
    }
    return guide["verification"]


def cached_fetcher():
    cache = {}

    def get_page(url):
        if url not in cache:
            try:
                cache[url] = fetch(url)
            except Exception as exc:  # recorded per claim; one bad page must not stop the run
                cache[url] = exc
        return cache[url]
    return get_page


def self_check():
    page = "<html><script>var x='secret';</script><p>Click <b>Register&nbsp;application</b>.</p><p>“Use it”</p></html>"
    get = lambda url: page if "good" in url else OSError("down")
    doms = ["docs.example.com"]
    assert check_claim({"url": "https://docs.example.com/good", "quote": "Click Register application."}, doms, get)[0]
    assert check_claim({"url": "https://docs.example.com/good", "quote": '"Use it"'}, doms, get)[0]
    assert check_claim({"url": "https://docs.example.com/good", "quote": "Click **Register `application`**."}, doms, get)[0], "Markdown marks are ignored"
    assert not check_claim({"url": "https://docs.example.com/good", "quote": "var x"}, doms, get)[0], "script text must not count"
    assert not check_claim({"url": "https://evil-docs.example.com.attacker.io/good", "quote": "Click"}, doms, get)[0]
    assert not check_claim({"url": "http://docs.example.com/good", "quote": "Click"}, doms, get)[0], "https only"
    assert not check_claim({"url": "https://docs.example.com/good", "quote": "Click Delete"}, doms, get)[0]
    assert check_claim({"url": "https://docs.example.com/bad", "quote": "x"}, doms, get)[1].startswith("fetch failed")
    guide = {"domains": doms, "steps": [
        {"id": "a", "source": {"url": "https://docs.example.com/good", "quote": "Click Register application"}},
        {"id": "b", "evidence": "auth-tested", "source": {"url": "https://docs.example.com/good", "quote": "Use it"}}]}
    assert verify(guide, get)["status"] == "incomplete", "auth-tested needs a test record"
    guide["steps"][1]["test_record"] = {"date": "2026-10-28"}
    assert verify(guide, get)["status"] == "complete"
    guide["gaps"] = [{"text": "terms", "critical": True}]
    assert verify(guide, get)["status"] == "incomplete", "critical gap keeps guide incomplete"
    guide["gaps"] = []
    guide["steps"][0]["time"] = {"kind": "estimate", "phase": "build", "min_minutes": 30, "max_minutes": 60, "basis": "judgment"}
    assert time_errors(guide) == ["effort.assumptions is required when any step has an estimate"]
    guide["effort"] = {"assumptions": "experienced developer"}
    guide["steps"][1]["time"] = {"kind": "measured", "min_minutes": 0.6, "max_minutes": 0.6, "basis": "timed run"}
    assert time_errors(guide) == ["b: time.phase must be setup or build"]
    guide["steps"][1]["time"]["phase"] = "setup"
    assert time_errors(guide) == ["b: measured time needs measured_on"]
    guide["steps"][1]["time"]["measured_on"] = "2026-10-28"
    guide["steps"][0]["time"]["min_minutes"] = 90
    assert time_errors(guide) == ["a: time needs 0 <= min_minutes <= max_minutes"]
    guide["steps"][0]["time"]["min_minutes"] = 30
    assert not time_errors(guide) and verify(guide, get)["status"] == "complete", "valid times never change status"
    guide["difficulty"] = {"level": "trivial", "reason": "x"}
    assert time_errors(guide) == ["difficulty needs level easy/moderate/hard and a reason"]
    guide["difficulty"]["level"] = "easy"
    guide["steps"][0]["who"] = "you"
    assert time_errors(guide) == ["a: steps that need you must say why in handoff"]
    guide["steps"][0]["handoff"] = "2FA"
    assert not time_errors(guide)
    guide["effort"]["wait"] = {"estimate": "Days", "source": {"url": "https://docs.example.com/good", "quote": "Click Delete"}}
    assert verify(guide, get)["status"] == "incomplete", "a sourced wait is checked like any claim"
    lines = []
    verify(guide, get, lines.append)
    n = len(list(claims(guide)))
    assert lines[0] == f"Checking quote 1 of {n} on docs.example.com" and len(lines) == n
    g = {"domains": ["docs.acme.com", "acme.com", "evil.example"], "gaps": []}
    assert anchor_domains(g, ["https://docs.acme.com/oauth"]) == ["evil.example"]
    assert g["domains"] == ["docs.acme.com", "acme.com"] and "evil.example" in g["gaps"][0]["text"]
    g = {"domains": ["dev.acme.io"]}
    assert anchor_domains(g, [], "https://dev.acme.io/oauth") == [] and g["domains"] == ["dev.acme.io"]
    print("SELF_CHECK_PASSED")


def main(path):
    with open(path) as f:
        guide = json.load(f)
    result = verify(guide, cached_fetcher())
    with open(path, "w") as f:
        json.dump(guide, f, indent=2, ensure_ascii=False)
        f.write("\n")
    for r in result["results"]:
        print(("PASS " if r["ok"] else "FAIL ") + f"{r['id']}: {r['reason']}")
    errors = time_errors(guide)
    for e in errors:
        print(f"TIME ERROR {e}")
    print(f"STATUS {result['status']}")
    if errors:
        return 1
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        self_check()
    elif len(sys.argv) == 2:
        sys.exit(main(sys.argv[1]))
    else:
        sys.exit(__doc__)
