"""OAuth Guide mock: stdlib web server for demonstrating the planned guide flow.

Usage: python3 mock/server.py               serve on 127.0.0.1:8780
       python3 mock/server.py --self-check
"""
import datetime, http.server, json, re, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
GUIDES = STATIC / "guides"
QUEUE = ROOT / "queue"
PORT = 8780
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
HOST_PREFIXES = ("www.", "docs.", "developer.", "developers.", "api.", "app.")


def load_guides():
    guides = []
    for path in sorted(GUIDES.glob("*.json")):
        try:
            guides.append(json.loads(path.read_text()))
        except (OSError, ValueError):
            continue  # a half-written guide must not break the library listing
    return guides


def parse_query(query):
    """Return (key, host, docs_url): key is the lowercased name or host used for matching."""
    q = query.strip().lower()
    if "://" not in q and re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}(/\S*)?", q):
        q = "https://" + q
    if q.startswith(("http://", "https://")):
        parts = urllib.parse.urlsplit(q)
        host = (parts.hostname or "").removeprefix("www.")
        docs_url = query.strip() if parts.path.strip("/") else None
        return host, host, docs_url
    return re.sub(r"\s+", " ", q), None, None


def find_guide(query, guides):
    key, host, _ = parse_query(query)
    for g in guides:
        aliases = {a.lower() for a in g.get("aliases", [])} | set(g.get("domains", []))
        if key in aliases or (host and any(host.endswith("." + a) for a in aliases if "." in a)):
            return g
    return None


def new_slug(query):
    key, host, _ = parse_query(query)
    if host:
        while host.startswith(HOST_PREFIXES):
            host = host.split(".", 1)[1]
        key = host.split(".")[0]
    return re.sub(r"[^a-z0-9]+", "-", key).strip("-")[:63]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def end_headers(self):
        # Guides change while the demo runs; never let the browser show a stale page.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/guides":
            return self.send_json(200, [{
                "slug": g["slug"], "name": g["name"], "summary": g.get("summary", ""),
                "status": g.get("verification", {}).get("status", "unchecked"),
                "checked_at": g.get("verification", {}).get("checked_at"),
            } for g in load_guides()])
        if self.path.startswith("/api/status/"):
            slug = self.path.removeprefix("/api/status/")
            if not SLUG.match(slug):
                return self.send_json(400, {"error": "bad slug"})
            if (GUIDES / f"{slug}.json").exists():
                return self.send_json(200, {"state": "ready"})
            try:
                return self.send_json(200, json.loads((QUEUE / f"{slug}.json").read_text()))
            except (OSError, ValueError):
                return self.send_json(404, {"state": "unknown"})
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/lookup":
            return self.send_json(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= 2048:
            return self.send_json(400, {"error": "Enter an app name, website, or documentation URL."})
        try:
            query = str(json.loads(self.rfile.read(length)).get("query", "")).strip()
        except (ValueError, AttributeError):
            query = ""
        if not query or len(query) > 200:
            return self.send_json(400, {"error": "Enter an app name, website, or documentation URL (up to 200 characters)."})
        guide = find_guide(query, load_guides())
        if guide:
            return self.send_json(200, {"found": True, "slug": guide["slug"]})
        slug = new_slug(query)
        if not SLUG.match(slug):
            return self.send_json(400, {"error": "Could not read an app name from that input."})
        QUEUE.mkdir(exist_ok=True)
        request = QUEUE / f"{slug}.json"
        if not request.exists():  # repeat searches join the existing request instead of resetting it
            request.write_text(json.dumps({
                "slug": slug, "query": query, "docs_url": parse_query(query)[2], "state": "queued",
                "note": "Waiting for the research agent to pick this up.",
                "requested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            }, indent=2))
        return self.send_json(202, {"found": False, "slug": slug})


def self_check():
    guides = [{"slug": "github", "aliases": ["github", "github.com"], "domains": ["docs.github.com"]},
              {"slug": "jira", "aliases": ["jira", "atlassian.net"], "domains": ["developer.atlassian.com"]}]
    for q in ["GitHub", " github ", "github.com", "https://www.github.com/", "https://docs.github.com/en/apps/oauth-apps"]:
        assert (find_guide(q, guides) or {}).get("slug") == "github", q
    assert find_guide("acme.atlassian.net", guides)["slug"] == "jira"
    assert find_guide("Linear", guides) is None
    assert find_guide("notgithub.com", guides) is None, "suffix match must respect the dot"
    assert new_slug("Linear") == "linear"
    assert new_slug("https://developers.linear.app/docs/oauth/authentication") == "linear"
    assert new_slug("Google Calendar") == "google-calendar"
    assert parse_query("https://developers.linear.app/docs/oauth")[2] == "https://developers.linear.app/docs/oauth"
    assert parse_query("linear.app")[2] is None
    assert not SLUG.match("../etc") and not SLUG.match("")
    print("SELF_CHECK_PASSED")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        self_check()
    else:
        print(f"OAuth Guide mock on http://127.0.0.1:{PORT}", flush=True)
        http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
