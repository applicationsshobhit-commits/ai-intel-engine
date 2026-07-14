import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "intel.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def insert_item(conn: sqlite3.Connection, item: dict) -> bool:
    """Insert a raw item. Returns False if it already exists (by url)."""
    try:
        conn.execute(
            """INSERT INTO raw_items (source, url, title, content, published_at, fetched_at)
               VALUES (:source, :url, :title, :content, :published_at, :fetched_at)""",
            item,
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def ensure_entity(conn: sqlite3.Connection, name: str, kind: str = "company") -> int:
    conn.execute(
        "INSERT OR IGNORE INTO entities (name, kind) VALUES (?, ?)", (name, kind)
    )
    conn.commit()
    row = conn.execute("SELECT id FROM entities WHERE name = ?", (name,)).fetchone()
    return row["id"]


def get_entities(conn: sqlite3.Connection) -> list:
    return conn.execute("SELECT id, name FROM entities").fetchall()


def get_unscored_items(conn: sqlite3.Connection) -> list:
    return conn.execute(
        "SELECT * FROM raw_items WHERE reasoned_at IS NULL"
    ).fetchall()


def insert_mention(conn: sqlite3.Connection, item_id: int, entity_id: int,
                    relevance_score: float, summary: str, created_at: str) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO mentions (item_id, entity_id, relevance_score, summary, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (item_id, entity_id, relevance_score, summary, created_at),
    )
    conn.commit()


def mark_item_reasoned(conn: sqlite3.Connection, item_id: int, reasoned_at: str) -> None:
    conn.execute("UPDATE raw_items SET reasoned_at = ? WHERE id = ?", (reasoned_at, item_id))
    conn.commit()
