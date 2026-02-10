"""
Database utilities for storing and retrieving items.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path("items.sqlite")

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS items (
  id TEXT PRIMARY KEY,
  url TEXT NOT NULL,
  title TEXT,
  source TEXT,
  kind TEXT,
  published TEXT,
  fetched_at TEXT,
  content_text TEXT,
  content_hash TEXT,
  bucket TEXT,
  score REAL,
  summary TEXT,
  why_it_matters TEXT,
  actions TEXT
);

CREATE INDEX IF NOT EXISTS idx_items_published ON items(published);
CREATE INDEX IF NOT EXISTS idx_items_bucket ON items(bucket);
"""

def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.executescript(SCHEMA)
    return conn

def upsert_item(conn: sqlite3.Connection, item: dict[str, Any]) -> None:
    cols = [
        "id","url","title","source","kind","published","fetched_at",
        "content_text","content_hash","bucket","score","summary","why_it_matters","actions"
    ]
    data = {c: item.get(c) for c in cols}
    placeholders = ",".join(["?"] * len(cols))
    updates = ",".join([f"{c}=excluded.{c}" for c in cols if c != "id"])
    conn.execute(
        f"""INSERT INTO items ({",".join(cols)}) VALUES ({placeholders})
            ON CONFLICT(id) DO UPDATE SET {updates}""",
        [data[c] for c in cols],
    )
    conn.commit()

def get_item(conn: sqlite3.Connection, item_id: str) -> Optional[dict[str, Any]]:
    cur = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cur.fetchone()
    if not row:
        return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))

def list_items_for_week(conn: sqlite3.Connection, year: int, week: int) -> list[dict[str, Any]]:
    # We store published as ISO-ish string; filtering precisely by ISO week requires parsing.
    # For simplicity we include items fetched in the last ~10 days and then the digest builder
    # writes into ISO week file.
    cur = conn.execute(
        "SELECT * FROM items ORDER BY COALESCE(published,'') DESC LIMIT 500"
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]
