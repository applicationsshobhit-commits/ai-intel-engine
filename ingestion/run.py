import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.sources import openai_rss, hackernews
from storage.db import init_db, get_connection, insert_item

SOURCES = [openai_rss, hackernews]


def main():
    init_db()
    conn = get_connection()

    total_new = 0
    for source in SOURCES:
        name = source.__name__.split(".")[-1]
        try:
            items = source.fetch()
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
