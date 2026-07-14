import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from html import escape

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.queries import get_feed, get_entities, get_entity_timeline

PORT = 8765

PAGE_SHELL = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Intel Engine</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 720px;
          margin: 0 auto; padding: 16px; line-height: 1.4; }}
  header {{ display: flex; gap: 16px; align-items: baseline; margin-bottom: 20px;
            flex-wrap: wrap; }}
  h1 {{ font-size: 1.3rem; margin: 0; }}
  nav a {{ margin-right: 12px; font-size: 0.9rem; }}
  .card {{ border: 1px solid #8883; border-radius: 10px; padding: 14px 16px;
           margin-bottom: 12px; }}
  .card h2 {{ font-size: 1.05rem; margin: 0 0 6px; }}
  .card h2 a {{ text-decoration: none; }}
  .meta {{ font-size: 0.8rem; opacity: 0.65; margin-bottom: 6px; }}
  .score {{ display: inline-block; padding: 1px 8px; border-radius: 999px;
            background: #4a90e233; font-size: 0.75rem; }}
  .summary {{ font-size: 0.92rem; }}
  .empty {{ opacity: 0.6; padding: 20px 0; }}
</style>
</head>
<body>
<header>
  <h1>AI Intel Engine</h1>
  <nav>{nav}</nav>
</header>
{body}
</body>
</html>"""


def render_nav(entities, active=None):
    links = ['<a href="/"{sel}>Feed</a>'.format(sel=' style="font-weight:bold"' if active is None else '')]
    for e in entities:
        sel = ' style="font-weight:bold"' if active == e["name"] else ""
        links.append(f'<a href="/entity?name={escape(e["name"])}"{sel}>{escape(e["name"])}</a>')
    return "".join(links)


def render_card(item):
    score = item.get("relevance_score")
    score_html = f'<span class="score">{score:.1f}</span>' if score is not None else ""
    entity_html = f' · {escape(item["entity"])}' if "entity" in item else ""
    return f"""<div class="card">
  <h2><a href="{escape(item['url'])}" target="_blank">{escape(item['title'])}</a></h2>
  <div class="meta">{escape(item['source'])}{entity_html} · {escape(item.get('published_at') or '')} {score_html}</div>
  <div class="summary">{escape(item.get('summary') or '')}</div>
</div>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # keep console quiet

    def do_GET(self):
        parsed = urlparse(self.path)
        entities = get_entities()

        if parsed.path == "/":
            items = get_feed()
            body = "".join(render_card(i) for i in items) or '<p class="empty">No scored items yet.</p>'
            nav = render_nav(entities, active=None)
            html = PAGE_SHELL.format(nav=nav, body=body)

        elif parsed.path == "/entity":
            name = parse_qs(parsed.query).get("name", [""])[0]
            items = get_entity_timeline(name)
            body = f"<h2>{escape(name)}</h2>" + (
                "".join(render_card(i) for i in items) or '<p class="empty">No mentions yet.</p>'
            )
            nav = render_nav(entities, active=name)
            html = PAGE_SHELL.format(nav=nav, body=body)

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())


def main():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Serving on http://localhost:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
