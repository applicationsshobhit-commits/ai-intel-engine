import json
import urllib.request
from datetime import datetime, timezone

from ingestion.item import make_item

SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date?query=AI&tags=story&hitsPerPage=20"


def fetch():
    req = urllib.request.Request(SEARCH_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)

    items = []
    for hit in data.get("hits", []):
        title = hit.get("title") or ""
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        created_at = hit.get("created_at")
        if not title:
            continue
        items.append(make_item(
            source="hackernews",
            url=url,
            title=title,
            content=f"{hit.get('points', 0)} points, {hit.get('num_comments', 0)} comments",
            published_at=created_at,
        ))
    return items
