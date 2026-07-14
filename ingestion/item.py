from __future__ import annotations

from datetime import datetime, timezone


def make_item(source: str, url: str, title: str, content: str, published_at: str | None) -> dict:
    return {
        "source": source,
        "url": url,
        "title": title.strip(),
        "content": (content or "").strip(),
        "published_at": published_at,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
