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
