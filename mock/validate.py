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
    return re.sub(r"\s+", "", text)


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


def verify(guide, get_page):
    results = []
    for claim_id, item in claims(guide):
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
    print(f"STATUS {result['status']}")
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        self_check()
    elif len(sys.argv) == 2:
        sys.exit(main(sys.argv[1]))
    else:
        sys.exit(__doc__)
