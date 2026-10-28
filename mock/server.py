"""OAuth Guide mock: stdlib web server for demonstrating the planned guide flow."""
import http.server, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
GUIDES = STATIC / "guides"
PORT = 8780


def load_guides():
    guides = []
    for path in sorted(GUIDES.glob("*.json")):
        try:
            guides.append(json.loads(path.read_text()))
        except (OSError, ValueError):
            continue  # a half-written guide must not break the library listing
    return guides


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

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
        return super().do_GET()


if __name__ == "__main__":
    print(f"OAuth Guide mock on http://127.0.0.1:{PORT}", flush=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
