import sys
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.sources import hackernews
from ingestion.sources.rss import fetch_rss
from storage.db import init_db, get_connection, insert_item

SOURCES = [
    ("openai.com/news", partial(fetch_rss, "https://openai.com/news/rss.xml", "openai.com/news")),
    ("techcrunch.com", partial(fetch_rss, "https://techcrunch.com/feed/", "techcrunch.com")),
    ("theverge.com", partial(fetch_rss, "https://www.theverge.com/rss/index.xml", "theverge.com")),
    ("arstechnica.com", partial(fetch_rss, "https://feeds.arstechnica.com/arstechnica/index", "arstechnica.com")),
    ("hackernews", hackernews.fetch),
]


def main():
    init_db()
    conn = get_connection()

    total_new = 0
    for name, fetch in SOURCES:
        try:
            items = fetch()
        except Exception as e:
            print(f"[{name}] fetch failed: {e}")
            continue

        new_count = sum(1 for item in items if insert_item(conn, item))
        total_new += new_count
        print(f"[{name}] fetched {len(items)}, {new_count} new")

    conn.close()
    print(f"Done. {total_new} new items total.")


if __name__ == "__main__":
    main()
