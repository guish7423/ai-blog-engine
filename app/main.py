"""AI Blog Engine — API + web interface for SEO blog generation."""

from contextlib import asynccontextmanager
from pathlib import Path

from html import escape

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.database import (
    get_all_posts,
    get_all_posts_for_feed,
    get_all_tags,
    get_popular_posts,
    get_post_by_slug,
    get_post_count,
    get_posts_by_author,
    get_posts_by_tag,
    get_related_posts,
    increment_view_count,
    init_db,
    init_newsletter,
    save_post,
    save_subscriber,
    search_posts,
)
from app.generator import generate, usage

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_newsletter()
    yield


app = FastAPI(
    title="AI Blog Engine",
    description="Generate SEO-optimized blog posts with AI",
    version="1.0.0",
    lifespan=lifespan,
)

try:
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
except RuntimeError:
    pass

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class GenerateRequest(BaseModel):
    keyword: str
    topic: str = ""
    word_count: int = 1500


@app.get("/health")
async def health():
    return {"status": "ok", "app": "AI Blog Engine", "posts": get_post_count()}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/generate")
async def generate_post(req: GenerateRequest):
    if not req.keyword.strip():
        raise HTTPException(400, "keyword is required")
    post = generate(req.keyword, req.topic, max(500, min(5000, req.word_count)))
    save_post(post)  # persist to SQLite
    return {
        "id": post.slug,
        "title": post.title,
        "slug": post.slug,
        "meta_description": post.meta_description,
        "content_html": post.content_html,
        "headings": post.headings,
        "word_count": post.word_count,
        "read_time": post.estimated_read_minutes,
        "tags": post.tags,
        "faq": post.faq,
        "usage": post.usage,
    }


@app.get("/blog", response_class=HTMLResponse)
async def blog_list(request: Request, page: int = 1, tag: str = "", q: str = ""):
    all_tags = get_all_tags()
    active_tag = tag.strip()
    keyword = q.strip()

    if active_tag:
        posts = get_posts_by_tag(active_tag, limit=20)
        total = len(posts)
    elif keyword:
        posts = search_posts(keyword, limit=20)
        total = len(posts)
    else:
        posts = get_all_posts(limit=20, offset=(page - 1) * 20)
        total = get_post_count()

    return templates.TemplateResponse(request, "blog.html", {
        "posts": posts,
        "page": page,
        "total": total,
        "pages": max(1, (total + 19) // 20),
        "all_tags": all_tags,
        "active_tag": active_tag,
        "keyword": keyword,
    })


@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_detail(slug: str, request: Request):
    post = get_post_by_slug(slug)
    if not post:
        raise HTTPException(404, "Post not found")
    increment_view_count(slug)
    related = get_related_posts(slug, post["tags"], limit=3)
    all_tags = get_all_tags()
    popular = get_popular_posts(limit=5)
    return templates.TemplateResponse(request, "blog_post.html", {
        "post": post,
        "related": related,
        "all_tags": all_tags,
        "popular": popular,
    })


@app.get("/topic/{tag}", response_class=HTMLResponse)
async def topic_cluster(tag: str, request: Request):
    """Topic cluster page — all posts for a tag with tag info."""
    posts = get_posts_by_tag(tag, limit=50)
    all_tags = get_all_tags()
    popular = get_popular_posts(limit=5)
    return templates.TemplateResponse(request, "topic.html", {
        "tag": tag,
        "posts": posts,
        "total": len(posts),
        "all_tags": all_tags,
        "popular": popular,
    })


@app.get("/api/posts/popular")
async def api_popular():
    posts = get_popular_posts(limit=6)
    return [{
        "title": p["title"],
        "slug": p["slug"],
        "meta_description": p.get("meta_description", ""),
        "tags": p.get("tags", []),
        "estimated_read_minutes": p.get("estimated_read_minutes", 3),
        "view_count": p.get("view_count", 0),
    } for p in posts]


@app.get("/popular", response_class=HTMLResponse)
async def popular_posts(request: Request):
    popular = get_popular_posts(limit=10)
    all_tags = get_all_tags()
    return templates.TemplateResponse(request, "blog.html", {
        "posts": popular,
        "page": 1,
        "total": len(popular),
        "pages": 1,
        "all_tags": all_tags,
        "active_tag": "",
        "keyword": "",
        "title": "Popular Posts",
    })


@app.get("/author/{name}", response_class=HTMLResponse)
async def author_page(name: str, request: Request):
    posts = get_posts_by_author(name)
    all_tags = get_all_tags()
    popular = get_popular_posts(limit=5)
    return templates.TemplateResponse(request, "author.html", {
        "author_name": name,
        "posts": posts,
        "all_tags": all_tags,
        "popular": popular,
    })


@app.get("/usage")
async def usage_endpoint():
    return usage.summary()


@app.get("/sitemap.xml")
async def sitemap():
    posts = get_all_posts_for_feed(limit=500)
    urls = '<url><loc>https://blog.crosswave.app/</loc><priority>1.0</priority></url>'
    urls += '<url><loc>https://blog.crosswave.app/blog</loc><priority>0.9</priority></url>'
    for p in posts:
        urls += f'<url><loc>https://blog.crosswave.app/blog/{escape(p["slug"])}</loc><lastmod>{p["created_at"][:10]}</lastmod><priority>0.8</priority></url>'
    return Response(
        content=f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        media_type="application/xml",
    )


@app.get("/feed.xml")
async def rss_feed():
    posts = get_all_posts_for_feed(limit=20)
    items = ""
    for p in posts:
        items += f"""
    <item>
      <title>{escape(p["title"])}</title>
      <link>https://blog.crosswave.app/blog/{escape(p["slug"])}</link>
      <description>{escape(p["meta_description"])}</description>
      <pubDate>{p["created_at"]}</pubDate>
      <guid>https://blog.crosswave.app/blog/{escape(p["slug"])}</guid>
    </item>"""
    return Response(
        content=f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>CrossWave Blog</title>
    <link>https://blog.crosswave.app</link>
    <description>AI-powered insights on content marketing, SaaS, and technology</description>
    <language>en-us</language>
    <atom:link href="https://blog.crosswave.app/feed.xml" rel="self" type="application/rss+xml"/>
    {items}
  </channel>
</rss>""",
        media_type="application/rss+xml",
    )


@app.post("/subscribe")
async def subscribe(email: str = Form(...)):
    if not email or "@" not in email:
        raise HTTPException(400, "Valid email is required")
    ok = save_subscriber(email.strip().lower())
    if ok:
        return {"ok": True, "message": "Subscribed!"}
    return {"ok": True, "message": "Already subscribed"}


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse(request, "pricing.html", {})
