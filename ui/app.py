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
    --bg: #f6f5f2; --surface: #ffffff; --border: #e8e6e0; --border-soft: #efeee9;
    --text: #171614; --text-dim: #5c5a54; --text-faint: #918f87;
    --shadow: 0 1px 2px rgba(20,18,14,0.04), 0 1px 1px rgba(20,18,14,0.03);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #121110; --surface: #1c1b19; --border: #302e2a; --border-soft: #262421;
      --text: #f3f2ee; --text-dim: #b3b0a8; --text-faint: #6f6d66;
      --shadow: 0 1px 2px rgba(0,0,0,0.3);
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 720px; margin: 0 auto; padding: 32px 18px 60px;
    background: var(--bg); color: var(--text); line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }}
  header {{ margin-bottom: 20px; }}
  .brand {{ display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px; }}
  h1 {{ font-size: 1.3rem; font-weight: 700; margin: 0; letter-spacing: -0.02em; }}
  .tagline {{ font-size: 0.78rem; color: var(--text-faint); margin: 0 0 16px; }}
  nav {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  nav a {{
    text-decoration: none; font-size: 0.78rem; font-weight: 500; padding: 5px 12px;
    border-radius: 999px; border: 1px solid var(--border); color: var(--text-dim);
    white-space: nowrap; background: var(--surface); transition: border-color 0.15s;
  }}
  nav a.active {{ background: var(--text); color: var(--bg); border-color: var(--text); }}
  h2.page-title {{ font-size: 1.05rem; font-weight: 700; margin: 22px 0 12px; letter-spacing: -0.01em; }}
  .card {{
    background: var(--surface); border: 1px solid var(--border-soft); border-radius: 10px;
    padding: 12px 16px; margin-bottom: 8px; box-shadow: var(--shadow);
    border-left: 3px solid var(--accent, var(--border));
  }}
  .card-top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }}
  .card h3 {{ font-size: 0.92rem; font-weight: 600; margin: 0; line-height: 1.35; letter-spacing: -0.005em; }}
  .card h3 a {{ color: var(--text); text-decoration: none; }}
  .card h3 a:hover {{ text-decoration: underline; }}
  .tag {{
    display: inline-block; padding: 2px 9px; border-radius: 999px;
    font-size: 0.68rem; font-weight: 700; flex-shrink: 0; white-space: nowrap;
  }}
  .summary {{
    font-size: 0.82rem; color: var(--text-dim); margin-top: 4px;
    overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
    -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  }}
  .meta {{ display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
           font-size: 0.7rem; color: var(--text-faint); margin-top: 6px; }}
  .score-bar {{ width: 34px; height: 4px; border-radius: 2px; background: var(--border-soft); overflow: hidden; }}
  .score-bar span {{ display: block; height: 100%; background: var(--accent, var(--text-faint)); }}
  .empty {{ color: var(--text-faint); padding: 40px 0; text-align: center; font-size: 0.9rem; }}
</style>
</head>
<body>
<header>
  <div class="brand"><h1>AI Intel Engine</h1></div>
  <p class="tagline">What's moving this week, ranked by relevance</p>
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
    score_pct = round(score * 100) if score is not None else None
    accent = "var(--text-faint)"
    entity_html = ""
    if show_entity and item.get("entity"):
        stroke, text_dark, fill = entity_color(item["entity"])
        accent = stroke
        entity_html = (
            f'<span class="tag" style="background:{fill};color:{text_dark}">'
            f'{escape(item["entity"])}</span>'
        )

    score_html = ""
    if score_pct is not None:
        score_html = (
            f'<div class="score-bar"><span style="width:{score_pct}%"></span></div>'
            f'<span>{score_pct}%</span>'
        )

    return f"""<div class="card" style="--accent:{accent}">
  <div class="card-top">
    <h3><a href="{escape(item['url'])}" target="_blank" rel="noopener">{escape(item['title'])}</a></h3>
    {entity_html}
  </div>
  <div class="summary">{escape(item.get('summary') or '')}</div>
  <div class="meta">
    <span>{escape(item['source'])}</span>
    <span>·</span>
    <span>{escape(item.get('published_at') or '')}</span>
    {score_html}
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
