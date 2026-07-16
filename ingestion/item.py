from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime


def make_item(source: str, url: str, title: str, content: str, published_at: str | None) -> dict:
    return {
        "source": source,
        "url": url,
        "title": title.strip(),
        "content": (content or "").strip(),
        "published_at": published_at,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def parse_published_at(published_at: str | None):
    if not published_at:
        return None
    try:
        return parsedate_to_datetime(published_at)  # RFC822, e.g. RSS pubDate
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(published_at.replace("Z", "+00:00"))  # ISO 8601, e.g. Atom/HN
    except ValueError:
        return None


def is_this_week(item: dict, days: int = 7) -> bool:
    published = parse_published_at(item.get("published_at"))
    if published is None:
        return True  # keep items with no/unparseable date rather than silently dropping them
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    return published >= datetime.now(timezone.utc) - timedelta(days=days)
