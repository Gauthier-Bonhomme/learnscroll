"""
Catalogue de contenu LearnScroll — SQLite via la stdlib (zéro dépendance).

Le catalogue est l'actif du projet : il accumule les cartes générées par les
batchs successifs (idempotence par external_id) et sert de source à
export_site.py, qui produit les JSON statiques déployés. Aucun serveur ne lit
cette base au runtime.
"""

from __future__ import annotations

import json
import os
import sqlite3

DB_PATH = os.getenv(
    "LEARNSCROLL_DB",
    os.path.join(os.path.dirname(__file__), "..", "data", "catalog.sqlite"),
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    id           INTEGER PRIMARY KEY,
    external_id  TEXT UNIQUE NOT NULL,
    hook         TEXT NOT NULL,
    category     TEXT NOT NULL,
    mode         TEXT NOT NULL,
    reading_time TEXT NOT NULL,
    teaser       TEXT NOT NULL,
    body         TEXT NOT NULL,
    why_layers   TEXT NOT NULL DEFAULT '[]',
    sources      TEXT NOT NULL DEFAULT '[]',
    tags         TEXT NOT NULL DEFAULT '[]',
    series       TEXT NOT NULL DEFAULT '',
    series_index INTEGER,
    series_total INTEGER,
    model_used   TEXT NOT NULL DEFAULT '',
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS news_seen (
    url        TEXT PRIMARY KEY,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_JSON_FIELDS = ("why_layers", "sources", "tags")


def connect(path: str | None = None) -> sqlite3.Connection:
    path = path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def upsert_card(conn: sqlite3.Connection, card: dict) -> bool:
    """Insère une carte ; renvoie False si l'external_id existe déjà (skip)."""
    if conn.execute(
        "SELECT 1 FROM cards WHERE external_id = ?", (card["external_id"],)
    ).fetchone():
        return False
    row = dict(card)
    for f in _JSON_FIELDS:
        row[f] = json.dumps(row.get(f) or [], ensure_ascii=False)
    conn.execute(
        """INSERT INTO cards (external_id, hook, category, mode, reading_time,
               teaser, body, why_layers, sources, tags, series, series_index,
               series_total, model_used)
           VALUES (:external_id, :hook, :category, :mode, :reading_time,
               :teaser, :body, :why_layers, :sources, :tags, :series,
               :series_index, :series_total, :model_used)""",
        {
            "series": "", "series_index": None, "series_total": None,
            "model_used": "", **row,
        },
    )
    return True


def all_cards(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM cards ORDER BY id").fetchall()
    out = []
    for r in rows:
        card = dict(r)
        for f in _JSON_FIELDS:
            card[f] = json.loads(card[f] or "[]")
        out.append(card)
    return out


def is_news_seen(conn: sqlite3.Connection, url: str) -> bool:
    return conn.execute("SELECT 1 FROM news_seen WHERE url = ?", (url,)).fetchone() is not None


def mark_news_seen(conn: sqlite3.Connection, url: str) -> None:
    conn.execute("INSERT OR IGNORE INTO news_seen (url) VALUES (?)", (url,))


def stats(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    by_cat = dict(
        conn.execute("SELECT category, COUNT(*) FROM cards GROUP BY category").fetchall()
    )
    by_mode = dict(
        conn.execute("SELECT mode, COUNT(*) FROM cards GROUP BY mode").fetchall()
    )
    return {"total": total, "by_category": by_cat, "by_mode": by_mode}
