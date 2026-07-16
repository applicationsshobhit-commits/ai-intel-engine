import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.item import is_this_week
from storage.db import get_connection


MIN_RELEVANCE = 0.5


def _this_week(rows):
    return [r for r in rows if is_this_week(r)]


def get_feed(limit: int = 50):
    conn = get_connection()
    rows = conn.execute(
        """SELECT r.id, r.title, r.url, r.source, r.published_at,
                  e.name AS entity, m.relevance_score, m.summary
           FROM mentions m
           JOIN raw_items r ON r.id = m.item_id
           JOIN entities e ON e.id = m.entity_id
           WHERE m.relevance_score >= ?
           ORDER BY m.relevance_score DESC, r.published_at DESC
           LIMIT ?""",
        (MIN_RELEVANCE, limit * 3),  # over-fetch since some get dropped by the recency filter
    ).fetchall()
    conn.close()
    return _this_week([dict(r) for r in rows])[:limit]


def get_entities():
    conn = get_connection()
    rows = conn.execute("SELECT id, name FROM entities ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_entity_timeline(entity_name: str, limit: int = 100):
    conn = get_connection()
    rows = conn.execute(
        """SELECT r.id, r.title, r.url, r.source, r.published_at,
                  m.relevance_score, m.summary
           FROM mentions m
           JOIN raw_items r ON r.id = m.item_id
           JOIN entities e ON e.id = m.entity_id
           WHERE e.name = ? AND m.relevance_score >= ?
           ORDER BY r.published_at DESC
           LIMIT ?""",
        (entity_name, MIN_RELEVANCE, limit * 3),
    ).fetchall()
    conn.close()
    return _this_week([dict(r) for r in rows])[:limit]
