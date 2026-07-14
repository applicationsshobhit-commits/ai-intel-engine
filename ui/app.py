import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from html import escape

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.queries import get_feed, get_entities, get_entity_timeline

PORT = 8765

ENTITY_COLORS = [
    ("#7F77DD", "#26215C", "#EEEDFE"),  # purple
    ("#1D9E75", "#04342C", "#E1F5EE"),  # teal
    ("#D85A30", "#4A1B0C", "#FAECE7"),  # coral
    ("#D4537E", "#4B1528", "#FBEAF0"),  # pink
    ("#378ADD", "#042C53", "#E6F1FB"),  # blue
    ("#639922", "#173404", "#EAF3DE"),  # green
    ("#BA7517", "#412402", "#FAEEDA"),  # amber
]


def entity_color(name):
    idx = sum(ord(c) for c in name) % len(ENTITY_COLORS)
    return ENTITY_COLORS[idx]


PAGE_SHELL = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Intel Engine</title>
<style>
  :root {{
    color-scheme: light dark;
    --bg: #fafaf9; --surface: #ffffff; --border: #e5e3dd;
    --text: #1c1b19; --text-dim: #6b6a64; --text-faint: #98968e;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #161513; --surface: #201f1c; --border: #34322d;
      --text: #f0efec; --text-dim: #a8a69f; --text-faint: #75736c;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 760px; margin: 0 auto; padding: 24px 16px 60px;
    background: var(--bg); color: var(--text); line-height: 1.5;
  }}
  header {{ margin-bottom: 18px; }}
  h1 {{ font-size: 1.25rem; font-weight: 600; margin: 0 0 10px; letter-spacing: -0.01em; }}
  nav {{ display: flex; flex-wrap: wrap; gap: 5px; }}
  nav a {{
    text-decoration: none; font-size: 0.78rem; padding: 4px 10px;
    border-radius: 999px; border: 1px solid var(--border); color: var(--text-dim);
    white-space: nowrap;
  }}
  nav a.active {{ background: var(--text); color: var(--bg); border-color: var(--text); }}
  h2.page-title {{ font-size: 1rem; font-weight: 600; margin: 4px 0 12px; }}
  .card {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 10px 14px; margin-bottom: 6px;
    display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap;
  }}
  .card h3 {{ font-size: 0.88rem; font-weight: 600; margin: 0; line-height: 1.3; flex: 1 1 auto; min-width: 200px; }}
  .card h3 a {{ color: var(--text); text-decoration: none; }}
  .card h3 a:hover {{ text-decoration: underline; }}
  .card-body {{ width: 100%; }}
  .meta {{ display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
           font-size: 0.7rem; color: var(--text-faint); margin-top: 2px; }}
  .tag {{
    display: inline-block; padding: 1px 8px; border-radius: 999px;
    font-size: 0.68rem; font-weight: 600; flex-shrink: 0;
  }}
  .summary {{
    font-size: 0.8rem; color: var(--text-dim); margin-top: 3px;
    overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
    -webkit-line-clamp: 1; -webkit-box-orient: vertical;
  }}
  .empty {{ color: var(--text-faint); padding: 30px 0; text-align: center; font-size: 0.9rem; }}
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
    links = [f'<a href="/" class="{"active" if active is None else ""}">Feed</a>']
    for e in entities:
        cls = "active" if active == e["name"] else ""
        links.append(f'<a href="/entity?name={escape(e["name"])}" class="{cls}">{escape(e["name"])}</a>')
    return "".join(links)


def render_card(item, show_entity=True):
    score = item.get("relevance_score")
    score_pct = f"{round(score * 100)}%" if score is not None else ""
    entity_html = ""
    if show_entity and item.get("entity"):
        stroke, text_dark, fill = entity_color(item["entity"])
        entity_html = (
            f'<span class="tag" style="background:{fill};color:{text_dark}">'
            f'{escape(item["entity"])}</span>'
        )
    return f"""<div class="card">
  <h3><a href="{escape(item['url'])}" target="_blank" rel="noopener">{escape(item['title'])}</a></h3>
  {entity_html}
  <div class="card-body">
    <div class="summary">{escape(item.get('summary') or '')}</div>
    <div class="meta">
      <span>{escape(item['source'])}</span>
      <span>·</span>
      <span>{escape(item.get('published_at') or '')}</span>
      {f'<span>· {score_pct}</span>' if score_pct else ''}
    </div>
  </div>
</div>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        entities = get_entities()

        if parsed.path == "/":
            items = get_feed()
            body = "".join(render_card(i) for i in items) or '<p class="empty">No scored items yet.</p>'
            html = PAGE_SHELL.format(nav=render_nav(entities), body=body)

        elif parsed.path == "/entity":
            name = parse_qs(parsed.query).get("name", [""])[0]
            items = get_entity_timeline(name)
            cards = "".join(render_card(i, show_entity=False) for i in items) or '<p class="empty">No mentions yet.</p>'
            body = f'<h2 class="page-title">{escape(name)}</h2>{cards}'
            html = PAGE_SHELL.format(nav=render_nav(entities, active=name), body=body)

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
