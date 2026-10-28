"""OAuth Guide mock: stdlib web server for demonstrating the planned guide flow.

Usage: python3 mock/server.py               serve on 127.0.0.1:8780
       python3 mock/server.py --self-check
"""
import datetime, http.server, json, os, re, secrets, sys, threading, time, urllib.parse
from pathlib import Path

import providers, research, validate

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
SEEDS = ROOT / "seed-guides"
DATA = Path(os.environ.get("DATA_DIR", ROOT / "data"))  # a persistent volume in production
GUIDES = DATA / "guides"
QUEUE = DATA / "queue"
PORT = 8780
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
HOST_PREFIXES = ("www.", "docs.", "developer.", "developers.", "api.", "app.")
# With no model connected, local development can still hand requests to a Claude Code session watching mock/queue.
LOCAL_AGENT = os.environ.get("LOCAL_AGENT", "1") == "1"
MAX_JOBS = 3
JOBS = set()
JOBS_LOCK = threading.Lock()
SESSION_TTL = 2 * 3600
MAX_SESSIONS = 1000
SESSIONS = {}  # sid -> {"conn": {...}, "seen": t}; memory only, so keys vanish on restart
SESSIONS_LOCK = threading.Lock()


def session_get(sid):
    with SESSIONS_LOCK:
        now = time.monotonic()
        for k in [k for k, v in SESSIONS.items() if now - v["seen"] > SESSION_TTL]:
            del SESSIONS[k]
        entry = SESSIONS.get(sid)
        if entry:
            entry["seen"] = now
        return entry["conn"] if entry else None


def session_put(sid, conn):
    with SESSIONS_LOCK:
        if sid not in SESSIONS and len(SESSIONS) >= MAX_SESSIONS:
            del SESSIONS[min(SESSIONS, key=lambda k: SESSIONS[k]["seen"])]
        SESSIONS[sid] = {"conn": conn, "seen": time.monotonic()}


def session_drop(sid):
    with SESSIONS_LOCK:
        SESSIONS.pop(sid, None)


def update_request(slug, **fields):
    path = QUEUE / f"{slug}.json"
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return
    data.update(fields)
    write_atomic(path, data)


def write_atomic(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)  # readers never see a half-written file


def review_problems(guide, fetch):
    v = validate.verify(guide, fetch)
    return [f"{r['id']}: {r['reason']} ({r['url']})" for r in v["results"] if not r["ok"]] + validate.time_errors(guide)


def run_job(request, conn):
    """Research, gate with validate.py, save. conn holds the visitor's key only for this thread's lifetime."""
    slug = request["slug"]
    try:
        label = {"anthropic": "Claude", "openai": "OpenAI", "portkey": "Portkey"}[conn["provider"]]
        update_request(slug, state="researching", note=f"{label} ({conn['model']}) is searching official documentation.")
        fetch = validate.cached_fetcher()
        def review(g, fetched):
            validate.anchor_domains(g, fetched, request.get("docs_url"))
            return review_problems(g, fetch)
        guide, fetched = research.RESEARCHERS[conn["provider"]](conn, request, review)
        validate.anchor_domains(guide, fetched, request.get("docs_url"))
        update_request(slug, state="validating", note="Re-fetching every cited page to confirm each quote.")
        review_problems(guide, fetch)  # records verification; failed quotes save as Incomplete, not as errors
        if validate.time_errors(guide):
            raise research.ResearchFailed("The guide was malformed after one repair round.")
        write_atomic(GUIDES / f"{slug}.json", guide)
        (QUEUE / f"{slug}.json").unlink(missing_ok=True)
    except research.ResearchFailed as exc:
        update_request(slug, state="failed", note=str(exc))
    except Exception as exc:  # never leave a request stuck in "researching"
        update_request(slug, state="failed", note=f"Research stopped unexpectedly ({type(exc).__name__}).")
    finally:
        with JOBS_LOCK:
            JOBS.discard(slug)


def start_job(request, conn):
    with JOBS_LOCK:
        if request["slug"] in JOBS:
            return True
        if len(JOBS) >= MAX_JOBS:
            return False
        JOBS.add(request["slug"])
    threading.Thread(target=run_job, args=(request, dict(conn)), daemon=True).start()
    return True


def public_conn(conn):
    """What the page may see about a connection: never the key."""
    return {"connected": bool(conn), "provider": conn and conn["provider"], "model": conn and conn["model"]}


def init_data():
    """Create the data folders and copy in seed guides that are not there yet; never overwrite saved guides."""
    GUIDES.mkdir(parents=True, exist_ok=True)
    QUEUE.mkdir(parents=True, exist_ok=True)
    for seed in SEEDS.glob("*.json"):
        if not (GUIDES / seed.name).exists():
            (GUIDES / seed.name).write_text(seed.read_text())


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

    def sid(self):
        for part in (self.headers.get("Cookie") or "").split(";"):
            name, _, value = part.strip().partition("=")
            if name == "sid" and re.fullmatch(r"[A-Za-z0-9_-]{20,64}", value):
                return value
        return None

    def send_json(self, status, body, cookie=None):
        data = json.dumps(body).encode()
        self.send_response(status)
        if cookie:
            secure = "; Secure" if self.headers.get("X-Forwarded-Proto") == "https" else ""
            self.send_header("Set-Cookie", f"sid={cookie}; HttpOnly; SameSite=Strict; Path=/{secure}")
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
        if self.path.startswith("/guides/"):
            name = self.path[len("/guides/"):].split("?")[0]
            if not name.endswith(".json") or not SLUG.match(name[:-5]) or not (GUIDES / name).exists():
                return self.send_json(404, {"error": "not found"})
            data = (GUIDES / name).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        if self.path == "/api/connection":
            return self.send_json(200, public_conn(session_get(self.sid())))
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

    def read_json(self, limit=2048):
        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= limit or self.headers.get("Content-Type") != "application/json":
            return None
        try:
            body = json.loads(self.rfile.read(length))
        except ValueError:
            return None
        return body if isinstance(body, dict) else None

    def do_POST(self):
        if self.path == "/api/connect":
            return self.connect()
        if self.path == "/api/disconnect":
            session_drop(self.sid())
            return self.send_json(200, public_conn(None))
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
        conn = session_get(self.sid())
        if not conn and not LOCAL_AGENT:
            return self.send_json(409, {"error": "No saved guide yet. Connect a model to generate one.", "needs_model": True})
        QUEUE.mkdir(exist_ok=True)
        path = QUEUE / f"{slug}.json"
        try:
            existing = json.loads(path.read_text())
        except (OSError, ValueError):
            existing = None
        request = {"slug": slug, "query": query, "docs_url": parse_query(query)[2], "state": "queued",
                   "note": "Waiting for the research agent to pick this up.",
                   "requested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
        if existing is None or existing.get("state") == "failed":  # repeat searches join a live request; failed ones restart
            write_atomic(path, request)
        else:
            request = existing
        if conn and not start_job(request, conn):
            return self.send_json(503, {"error": "The research agent is busy. Try again in a minute."})
        return self.send_json(202, {"found": False, "slug": slug})


    def connect(self):
        body = self.read_json() or {}
        provider = body.get("provider")
        conn = {"provider": provider, "api_key": str(body.get("api_key") or "").strip(),
                "model": str(body.get("model") or "").strip() or providers.DEFAULT_MODELS.get(provider, ""),
                "portkey_provider": str(body.get("portkey_provider") or "").strip()}
        if provider not in providers.PROVIDERS or not conn["api_key"] or not conn["model"] or len(conn["api_key"]) > 512:
            return self.send_json(400, {"error": "Choose a provider and enter a key and model."})
        try:
            providers.check(conn)
        except providers.ConnectionFailed as exc:
            return self.send_json(400, {"error": str(exc)})
        sid = self.sid() or secrets.token_urlsafe(32)
        session_put(sid, conn)
        return self.send_json(200, public_conn(conn), cookie=sid)


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
    check_connect_endpoint()
    check_pipeline()
    check_data_dir()
    print("SELF_CHECK_PASSED")


def check_data_dir():
    import tempfile
    global DATA, GUIDES, QUEUE
    saved = (DATA, GUIDES, QUEUE)
    DATA = Path(tempfile.mkdtemp()); GUIDES, QUEUE = DATA / "guides", DATA / "queue"
    try:
        init_data()
        seeds = sorted(p.name for p in SEEDS.glob("*.json"))
        assert seeds and sorted(p.name for p in GUIDES.glob("*.json")) == seeds
        (GUIDES / seeds[0]).write_text("{}")
        init_data()
        assert (GUIDES / seeds[0]).read_text() == "{}", "seeds never overwrite saved guides"
    finally:
        DATA, GUIDES, QUEUE = saved


def check_pipeline():
    """run_job with stubbed researchers and pages: pass saves the guide, failure is reported, the key never lands on disk."""
    import tempfile
    global GUIDES, QUEUE
    saved = (GUIDES, QUEUE, dict(research.RESEARCHERS), validate.fetch)
    tmp = Path(tempfile.mkdtemp())
    GUIDES, QUEUE = tmp / "guides", tmp / "queue"
    GUIDES.mkdir(); QUEUE.mkdir()
    page = "<p>Click Register application.</p>"
    validate.fetch = lambda url: page
    guide = {"slug": "acme", "name": "Acme", "domains": ["docs.acme.com"], "summary": "s", "gaps": [],
             "effort": {"assumptions": "a", "wait": {"estimate": "None", "basis": "b"}},
             "steps": [{"id": "x", "title": "t", "detail": "d", "evidence": "documented",
                        "time": {"kind": "estimate", "phase": "setup", "min_minutes": 1, "max_minutes": 2, "basis": "b"},
                        "source": {"url": "https://docs.acme.com/o", "quote": "Click Register application."}}]}
    seen = []
    def fake(conn, request, review):
        seen.append(review(json.loads(json.dumps(guide)), ["https://docs.acme.com/o"]))
        return json.loads(json.dumps(guide)), ["https://docs.acme.com/o"]
    try:
        key = "sk-test-" + secrets.token_hex(6)
        conn = {"provider": "anthropic", "model": "m", "api_key": key}
        research.RESEARCHERS["anthropic"] = fake
        write_atomic(QUEUE / "acme.json", {"slug": "acme", "state": "queued"})
        run_job({"slug": "acme", "query": "Acme"}, conn)
        stored = (GUIDES / "acme.json").read_text()
        assert seen == [[]] and json.loads(stored)["verification"]["status"] == "complete"
        assert not (QUEUE / "acme.json").exists() and key not in stored
        def boom(conn, request, review):
            raise research.ResearchFailed("The model declined this request.")
        research.RESEARCHERS["anthropic"] = boom
        write_atomic(QUEUE / "beta.json", {"slug": "beta", "state": "queued"})
        run_job({"slug": "beta", "query": "Beta"}, conn)
        failed = json.loads((QUEUE / "beta.json").read_text())
        assert failed["state"] == "failed" and "declined" in failed["note"] and key not in json.dumps(failed)
        assert not JOBS
    finally:
        GUIDES, QUEUE = saved[0], saved[1]
        research.RESEARCHERS.clear(); research.RESEARCHERS.update(saved[2])
        validate.fetch = saved[3]


def check_connect_endpoint():
    """Run the real handler on a spare port with a stubbed provider check; the key must never come back."""
    import io, contextlib, urllib.request
    key = "sk-test-NEVER-ECHO-" + secrets.token_hex(8)
    real_check = providers.check
    providers.check = lambda conn: None if conn["api_key"] == key else (_ for _ in ()).throw(providers.ConnectionFailed("The key was rejected."))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    log = io.StringIO()
    def call(path, body=None, cookie=None):
        req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **({"Cookie": cookie} if cookie else {})})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, r.headers.get("Set-Cookie"), r.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, None, e.read().decode()
    try:
        with contextlib.redirect_stderr(log):
            st, _, text = call("/api/connect", {"provider": "anthropic", "api_key": "wrong"})
            assert st == 400 and "rejected" in text
            st, cookie, text = call("/api/connect", {"provider": "anthropic", "api_key": key})
            assert st == 200 and key not in text and "HttpOnly" in cookie and "SameSite=Strict" in cookie
            sid = cookie.split(";")[0]
            st, _, text = call("/api/connection", cookie=sid)
            assert json.loads(text) == {"connected": True, "provider": "anthropic", "model": "claude-opus-5-5"} and key not in text
            st, _, text = call("/api/connect", {"provider": "nope", "api_key": key})
            assert st == 400
            call("/api/disconnect", {}, cookie=sid)
            assert json.loads(call("/api/connection", cookie=sid)[2])["connected"] is False
        assert key not in log.getvalue(), "key must never reach the request log"
    finally:
        srv.shutdown()
        providers.check = real_check


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        self_check()
    else:
        init_data()
        host = os.environ.get("HOST", "127.0.0.1")
        port = int(os.environ.get("PORT", PORT))
        print(f"OAuth Guide on http://{host}:{port} (data in {DATA})", flush=True)
        http.server.ThreadingHTTPServer((host, port), Handler).serve_forever()
