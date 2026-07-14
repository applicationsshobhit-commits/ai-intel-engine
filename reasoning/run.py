import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reasoning.score import score_item
from storage.db import (
    get_connection, ensure_entity, get_entities, get_unscored_items,
    insert_mention, mark_item_reasoned,
)

TRACKED_ENTITIES = [
    "OpenAI", "Anthropic", "Google", "Microsoft", "Meta", "Apple", "Amazon", "Tesla",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="max items to process")
    args = parser.parse_args()

    conn = get_connection()
    for name in TRACKED_ENTITIES:
        ensure_entity(conn, name)
    entity_rows = get_entities(conn)
    entity_by_name = {row["name"]: row["id"] for row in entity_rows}
    entity_names = list(entity_by_name.keys())

    items = get_unscored_items(conn)
    if args.limit:
        items = items[:args.limit]
    print(f"{len(items)} items to process")

    for item in items:
        try:
            results = score_item(dict(item), entity_names)
        except Exception as e:
            print(f"  [item {item['id']}] scoring failed: {e}")
            continue

        for r in results:
            entity_id = entity_by_name.get(r.get("entity"))
            if entity_id is None:
                continue
            insert_mention(conn, item["id"], entity_id, r.get("relevance_score", 0),
                            r.get("summary", ""), r["created_at"])

        mark_item_reasoned(conn, item["id"], datetime.now(timezone.utc).isoformat())
        tag = ", ".join(r["entity"] for r in results) if results else "no match"
        print(f"  [item {item['id']}] {item['title'][:60]!r} -> {tag}")

    conn.close()


if __name__ == "__main__":
    main()
