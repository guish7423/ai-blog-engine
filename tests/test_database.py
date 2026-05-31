"""Tests for the SQLite persistence layer."""

import os
import tempfile
from pathlib import Path

import pytest

from app.database import (
    DB_PATH,
    get_connection,
    get_all_posts,
    get_post_by_slug,
    get_post_count,
    init_db,
    save_post,
)
from app.generator import BlogPost

SAMPLE = BlogPost(
    title="Test Post",
    slug="test-post",
    meta_description="A test post.",
    content_html="<p>Hello world</p>",
    headings=["Intro"],
    word_count=50,
    estimated_read_minutes=1,
    tags=["test"],
    faq=[],
    usage={},
)


@pytest.fixture(autouse=True)
def _patch_db_path(monkeypatch, tmp_path):
    """Use a temporary DB file for each test."""
    test_db = tmp_path / "test.db"
    monkeypatch.setattr("app.database.DB_PATH", test_db)
    init_db()


def test_init_db_creates_table():
    conn = get_connection()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    conn.close()
    assert "blog_posts" in [t["name"] for t in tables]


def test_save_and_retrieve():
    pid = save_post(SAMPLE)
    assert pid > 0

    post = get_post_by_slug("test-post")
    assert post is not None
    assert post["title"] == "Test Post"
    assert post["word_count"] == 50
    assert post["read_time"] == 1
    assert post["tags"] == ["test"]


def test_get_all_posts_ordering():
    p2 = BlogPost(
        title="Second",
        slug="second",
        meta_description="",
        content_html="<p>2</p>",
        headings=[],
        word_count=10,
        estimated_read_minutes=1,
        tags=[],
        faq=[],
        usage={},
    )
    save_post(SAMPLE)
    save_post(p2)

    posts = get_all_posts()
    assert len(posts) == 2
    # Most recent first
    assert posts[0]["slug"] == "second"


def test_get_post_not_found():
    assert get_post_by_slug("nonexistent") is None


def test_get_post_count():
    save_post(SAMPLE)
    assert get_post_count() == 1
    save_post(SAMPLE)  # same slug → replace
    assert get_post_count() == 1


def test_get_all_posts_limit():
    for i in range(5):
        p = BlogPost(
            title=f"Post {i}",
            slug=f"post-{i}",
            meta_description="",
            content_html="<p>test</p>",
            headings=[],
            word_count=10,
            estimated_read_minutes=1,
            tags=[],
            faq=[],
            usage={},
        )
        save_post(p)

    posts = get_all_posts(limit=3)
    assert len(posts) == 3
