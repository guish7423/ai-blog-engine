"""Tests for CrossBlog API routes."""

import os

import pytest
from fastapi.testclient import TestClient

# Force mock mode before importing app
os.environ["LLM_API_MOCK"] = "true"
os.environ["LLM_MOCK_RESPONSE"] = '{"result":"mock"}'

from app.database import get_all_tags, init_db, init_newsletter, save_post  # noqa: E402
from app.generator import BlogPost  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _patch_db(monkeypatch, tmp_path):
    test_db = tmp_path / "test.db"
    monkeypatch.setattr("app.database.DB_PATH", test_db)
    init_db()
    init_newsletter()


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
    assert "No posts found" in resp.text


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


def test_sitemap_xml():
    resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/xml"
    assert "urlset" in resp.text
    assert "blog.crosswave.app" in resp.text


def test_rss_feed():
    resp = client.get("/feed.xml")
    assert resp.status_code == 200
    assert resp.headers["content-type"] in ("application/rss+xml", "text/plain")
    assert "rss" in resp.text
    assert "CrossWave Blog" in resp.text


def test_subscribe_success():
    resp = client.post("/subscribe", data={"email": "test@example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True


def test_subscribe_duplicate():
    client.post("/subscribe", data={"email": "dup@example.com"})
    resp = client.post("/subscribe", data={"email": "dup@example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "Already" in data["message"]


def test_subscribe_invalid_email():
    resp = client.post("/subscribe", data={"email": "not-an-email"})
    assert resp.status_code == 400


def test_blog_list_with_tag_filter(seeded):
    resp = client.get("/blog?tag=test")
    assert resp.status_code == 200
    assert "Seeded Post" in resp.text


def test_blog_list_with_tag_no_match(seeded):
    resp = client.get("/blog?tag=nonexistent")
    assert resp.status_code == 200
    assert "No posts found" in resp.text


def test_blog_list_with_search(seeded):
    resp = client.get("/blog?q=Seeded")
    assert resp.status_code == 200
    assert "Seeded Post" in resp.text


def test_blog_list_with_search_no_match(seeded):
    resp = client.get("/blog?q=xyznonexistent")
    assert resp.status_code == 200
    assert "No posts found" in resp.text


def test_blog_detail_has_related(seeded):
    p2 = BlogPost(
        title="Related Post",
        slug="related-post",
        meta_description="",
        content_html="<p>Related</p>",
        headings=[],
        word_count=10,
        estimated_read_minutes=1,
        tags=["test"],
        faq=[],
        usage={},
    )
    save_post(p2)
    resp = client.get("/blog/seeded-post")
    assert resp.status_code == 200
    assert "Related Post" in resp.text


def test_blog_detail_has_tags_section(seeded):
    resp = client.get("/blog/seeded-post")
    assert resp.status_code == 200


def test_author_page(seeded):
    # seeded post uses default author "CrossWave Team"
    resp = client.get("/author/CrossWave%20Team")
    assert resp.status_code == 200
    assert "Seeded Post" in resp.text


def test_author_page_no_posts():
    resp = client.get("/author/Unknown")
    assert resp.status_code == 200
    assert "No articles" in resp.text


def test_popular_endpoint(seeded):
    # Visit detail 3 times to boost view count
    for _ in range(3):
        client.get("/blog/seeded-post")
    resp = client.get("/popular")
    assert resp.status_code == 200
    assert "Seeded Post" in resp.text


def test_view_count_increments_on_detail(seeded):
    from app.database import get_post_by_slug
    before = get_post_by_slug("seeded-post")["view_count"] or 0
    client.get("/blog/seeded-post")
    after = get_post_by_slug("seeded-post")["view_count"]
    assert after >= before + 1


def test_topic_page_found(seeded):
    resp = client.get("/topic/test")
    assert resp.status_code == 200
    assert "Seeded Post" in resp.text
    assert "1 article" in resp.text.lower()


def test_topic_page_no_match():
    resp = client.get("/topic/nonexistent")
    assert resp.status_code == 200
    assert "No articles" in resp.text


def test_topic_page_has_schema(seeded):
    resp = client.get("/topic/test")
    assert resp.status_code == 200
    assert "CollectionPage" in resp.text


def test_blog_detail_has_article_schema(seeded):
    resp = client.get("/blog/seeded-post")
    assert resp.status_code == 200
    assert "Article" in resp.text
    # seeded post has faq data, so FAQPage schema should be present
    assert "FAQPage" in resp.text


def test_blog_detail_has_faq_schema():
    """Post with FAQ data should render FAQPage schema."""
    from app.generator import BlogPost
    post = BlogPost(
        title="FAQ Post",
        slug="faq-post",
        meta_description="FAQ test",
        content_html="<p>test</p>",
        headings=[],
        word_count=50,
        estimated_read_minutes=1,
        tags=["faq"],
        faq=[{"question": "Q1?", "answer": "A1."}],
        usage={},
    )
    save_post(post)
    resp = client.get("/blog/faq-post")
    assert resp.status_code == 200
    assert "FAQPage" in resp.text
    assert "Q1?" in resp.text
    assert "BreadcrumbList" in resp.text
