"""SQLite persistence for blog posts — zero extra dependencies."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "blog.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if not exist. Call once on startup."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS blog_posts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            slug        TEXT UNIQUE NOT NULL,
            meta_description TEXT DEFAULT '',
            content_html TEXT NOT NULL,
            headings    TEXT DEFAULT '[]',
            tags        TEXT DEFAULT '[]',
            word_count  INTEGER DEFAULT 0,
            read_time   INTEGER DEFAULT 1,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def save_post(post) -> int:
    """Insert or replace a blog post by slug. Returns row id."""
    conn = get_connection()
    cur = conn.execute(
        """INSERT OR REPLACE INTO blog_posts
           (title, slug, meta_description, content_html, headings, tags, word_count, read_time)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            post.title,
            post.slug,
            post.meta_description,
            post.content_html,
            json.dumps(post.headings),
            json.dumps(post.tags),
            post.word_count,
            post.estimated_read_minutes,
        ),
    )
    conn.commit()
    conn.close()
    return cur.lastrowid or 0


def get_all_posts(limit: int = 20, offset: int = 0) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM blog_posts ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    conn.close()
    for r in rows:
        d = dict(r)
        d["headings"] = json.loads(d.get("headings", "[]"))
        d["tags"] = json.loads(d.get("tags", "[]"))
    return [dict(r) for r in rows]


def get_post_by_slug(slug: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM blog_posts WHERE slug = ?", (slug,)
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["headings"] = json.loads(d.get("headings", "[]"))
        d["tags"] = json.loads(d.get("tags", "[]"))
        return d
    return None


def get_post_count() -> int:
    conn = get_connection()
    (count,) = conn.execute("SELECT COUNT(*) FROM blog_posts").fetchone()
    conn.close()
    return count
