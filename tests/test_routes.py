"""Tests for CrossBlog API routes."""

import os

import pytest
from fastapi.testclient import TestClient

# Force mock mode before importing app
os.environ["LLM_API_MOCK"] = "true"
os.environ["LLM_MOCK_RESPONSE"] = '{"result":"mock"}'

from app.database import init_db, save_post  # noqa: E402
from app.generator import BlogPost  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _patch_db(monkeypatch, tmp_path):
    test_db = tmp_path / "test.db"
    monkeypatch.setattr("app.database.DB_PATH", test_db)
    init_db()


@pytest.fixture
def seeded():
    post = BlogPost(
        title="Seeded Post",
        slug="seeded-post",
        meta_description="A seeded test post for listing tests.",
        content_html="<p>Content</p>",
        headings=["Intro"],
        word_count=150,
        estimated_read_minutes=1,
        tags=["test"],
        faq=[{"question": "Q?", "answer": "A."}],
        usage={},
    )
    save_post(post)
    return post


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "posts" in data


def test_landing_page():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Blog Engine" in resp.text


def test_pricing_page():
    resp = client.get("/pricing")
    assert resp.status_code == 200
    assert "Pay As You Go" in resp.text


def test_blog_list_empty():
    resp = client.get("/blog")
    assert resp.status_code == 200
    assert "No posts yet" in resp.text


def test_blog_list_with_posts(seeded):
    resp = client.get("/blog")
    assert resp.status_code == 200
    assert "Seeded Post" in resp.text


def test_blog_detail_found(seeded):
    resp = client.get("/blog/seeded-post")
    assert resp.status_code == 200
    assert "Seeded Post" in resp.text
    assert "<p>Content</p>" in resp.text


def test_blog_detail_not_found():
    resp = client.get("/blog/nonexistent")
    assert resp.status_code == 404


def test_generate_success():
    resp = client.post("/generate", json={
        "keyword": "test keyword",
        "topic": "Test Topic",
        "word_count": 500,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "title" in data
    assert data["slug"] == "test-keyword"
    assert "content_html" in data


def test_generate_missing_keyword():
    resp = client.post("/generate", json={"keyword": "", "topic": ""})
    assert resp.status_code == 400


def test_generate_min_word_count():
    resp = client.post("/generate", json={
        "keyword": "test",
        "word_count": 100,
    })
    assert resp.status_code == 200
    # should be clamped to min 500
    data = resp.json()
    assert data["word_count"] >= 10


def test_generate_auto_saves():
    # Generate a post, then check it appears on the blog list
    client.post("/generate", json={"keyword": "auto-save test"})
    resp = client.get("/health")
    assert resp.json()["posts"] >= 1


def test_usage_endpoint():
    resp = client.get("/usage")
    assert resp.status_code == 200
    data = resp.json()
    assert "calls" in data
