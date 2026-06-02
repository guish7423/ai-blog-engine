"""Tests for the SQLite persistence layer."""

import os
import tempfile
from pathlib import Path

import pytest

from app.database import (
    DB_PATH,
    get_all_posts,
    get_all_tags,
    get_connection,
    get_popular_posts,
    get_post_by_slug,
    get_post_count,
    get_posts_by_author,
    get_posts_by_tag,
    get_related_posts,
    increment_view_count,
    init_db,
    save_post,
    search_posts,
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


def test_search_posts():
    p2 = BlogPost(
        title="Second Article",
        slug="second-article",
        meta_description="",
        content_html="<p>2</p>",
        headings=[],
        word_count=10,
        estimated_read_minutes=1,
        tags=["ai", "marketing"],
        faq=[],
        usage={},
    )
    save_post(SAMPLE)
    save_post(p2)

    results = search_posts("Second")
    assert len(results) == 1
    assert results[0]["slug"] == "second-article"

    results = search_posts("test")
    assert len(results) == 1
    assert results[0]["slug"] == "test-post"


def test_get_posts_by_tag():
    p2 = BlogPost(
        title="Tagged Post",
        slug="tagged-post",
        meta_description="",
        content_html="<p>tagged</p>",
        headings=[],
        word_count=10,
        estimated_read_minutes=1,
        tags=["ai", "ml"],
        faq=[],
        usage={},
    )
    save_post(SAMPLE)  # tags=["test"]
    save_post(p2)

    results = get_posts_by_tag("ai")
    assert len(results) == 1
    assert results[0]["slug"] == "tagged-post"

    results = get_posts_by_tag("test")
    assert len(results) == 1


def test_get_related_posts():
    p1 = BlogPost(title="A", slug="a", meta_description="", content_html="<p>a</p>",
                  headings=[], word_count=10, estimated_read_minutes=1, tags=["tag1"], faq=[], usage={})
    p2 = BlogPost(title="B", slug="b", meta_description="", content_html="<p>b</p>",
                  headings=[], word_count=10, estimated_read_minutes=1, tags=["tag1", "tag2"], faq=[], usage={})
    p3 = BlogPost(title="C", slug="c", meta_description="", content_html="<p>c</p>",
                  headings=[], word_count=10, estimated_read_minutes=1, tags=["tag2"], faq=[], usage={})
    save_post(p1)
    save_post(p2)
    save_post(p3)

    related = get_related_posts("a", ["tag1", "tag2"])
    assert len(related) == 2
    slugs = [r["slug"] for r in related]
    assert "b" in slugs
    assert "c" in slugs
    assert "a" not in slugs


def test_get_all_tags():
    p1 = BlogPost(title="A", slug="a", meta_description="", content_html="<p>a</p>",
                  headings=[], word_count=10, estimated_read_minutes=1, tags=["ai", "ml"], faq=[], usage={})
    p2 = BlogPost(title="B", slug="b", meta_description="", content_html="<p>b</p>",
                  headings=[], word_count=10, estimated_read_minutes=1, tags=["ml", "nlp"], faq=[], usage={})
    save_post(p1)
    save_post(p2)

    tags = get_all_tags()
    assert "ai" in tags
    assert "ml" in tags
    assert "nlp" in tags
    assert len(tags) == 3


def test_get_posts_by_author():
    p1 = BlogPost(title="By Alice", slug="alice-1", meta_description="", content_html="<p>a</p>",
                  headings=[], word_count=10, estimated_read_minutes=1, tags=[], faq=[], usage={}, author="Alice")
    p2 = BlogPost(title="By Bob", slug="bob-1", meta_description="", content_html="<p>b</p>",
                  headings=[], word_count=10, estimated_read_minutes=1, tags=[], faq=[], usage={}, author="Bob")
    save_post(p1)
    save_post(p2)
    alice_posts = get_posts_by_author("Alice")
    assert len(alice_posts) == 1
    assert alice_posts[0]["slug"] == "alice-1"
    assert get_posts_by_author("Nobody") == []


def test_increment_view_count():
    save_post(SAMPLE)

    # Detail page should increment
    from app.database import increment_view_count, get_post_by_slug
    post = get_post_by_slug("test-post")
    assert post["view_count"] == 0

    increment_view_count("test-post")
    post = get_post_by_slug("test-post")
    assert post["view_count"] >= 1

    increment_view_count("test-post")
    post = get_post_by_slug("test-post")
    assert post["view_count"] >= 2


def test_get_popular_posts():
    p1 = BlogPost(title="Most Viewed", slug="most-viewed", meta_description="", content_html="<p>a</p>",
                  headings=[], word_count=10, estimated_read_minutes=1, tags=[], faq=[], usage={})
    save_post(p1)

    from app.database import increment_view_count
    increment_view_count("most-viewed")
    increment_view_count("most-viewed")

    popular = get_popular_posts(limit=3)
    assert len(popular) >= 1
    assert popular[0]["slug"] == "most-viewed"
    assert popular[0]["view_count"] >= 2


def test_faq_persistence():
    """FAQ data should be saved to DB and returned correctly."""
    post = BlogPost(
        title="FAQ Post",
        slug="faq-post",
        meta_description="",
        content_html="<p>faq</p>",
        headings=[],
        word_count=50,
        estimated_read_minutes=1,
        tags=["faq"],
        faq=[{"question": "What is X?", "answer": "X is Y."}, {"question": "How does it work?", "answer": "It works like Z."}],
        usage={},
    )
    pid = save_post(post)
    assert pid > 0

    retrieved = get_post_by_slug("faq-post")
    assert retrieved is not None
    assert len(retrieved["faq"]) == 2
    assert retrieved["faq"][0]["question"] == "What is X?"
    assert retrieved["faq"][1]["answer"] == "It works like Z."


def test_topic_page_data():
    """Posts by tag should return posts with correct tag."""
    p1 = BlogPost(title="AI Post", slug="ai-post", meta_description="", content_html="<p>ai</p>",
                  headings=[], word_count=10, estimated_read_minutes=1, tags=["ai", "ml"], faq=[], usage={})
    p2 = BlogPost(title="Web Post", slug="web-post", meta_description="", content_html="<p>web</p>",
                  headings=[], word_count=10, estimated_read_minutes=1, tags=["web"], faq=[], usage={})
    save_post(p1)
    save_post(p2)

    ai_posts = get_posts_by_tag("ai")
    assert len(ai_posts) == 1
    assert ai_posts[0]["slug"] == "ai-post"

    web_posts = get_posts_by_tag("web")
    assert len(web_posts) == 1
    assert web_posts[0]["slug"] == "web-post"

    ml_posts = get_posts_by_tag("ml")
    assert len(ml_posts) == 1
