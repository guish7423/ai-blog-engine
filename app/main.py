"""AI Blog Engine — API + web interface for SEO blog generation."""

import asyncio
import random
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

# ── Auto Content Generation Topics ──────────────────────────────────────────
# Extended topic list covering CrossWave ecosystem + general AI/SaaS topics
AUTO_TOPICS = [
    # CrossWave Ecosystem (company blog)
    "How CrossWave HQ uses AI agents to run a one-person company",
    "Building a unified HQ dashboard for AI-powered business operations",
    "From inquiry to deployment: automating the full SaaS delivery pipeline",
    "How AI agents can automatically scan and evaluate freelance job listings",
    "Building a sandbox approval system for autonomous AI agent safety",
    "Implementing model routing for cost-effective multi-LLM agent systems",
    "CrossWave introduction: AI-native company building platform",
    "Setting up monitoring and automatic health checks for microservices",
    "Best practices for AI agent system prompts and task delegation",
    "Automating weekly business reports with Celery Beat and LLM generation",
    # AI SaaS & Operations
    "AI agent architecture patterns for SaaS platforms",
    "How to build a self-correcting AI agent system with evolution loops",
    "Multi-tenant vs single-tenant architecture for AI SaaS products",
    "Stripe integration patterns for SaaS platforms with FastAPI",
    "Celery task queue best practices for AI agent workloads",
    "Building a customer-facing proposal portal with real-time status",
    "HTMX patterns for real-time SaaS dashboards",
    "Email notification workflows for automated SaaS pipelines",
    "SQLite database backup strategies for production deployments",
    "Production deployment checklist for Python FastAPI applications",
    # Technical SEO & Marketing
    "Technical SEO guide for AI-powered content management systems",
    "How structured data (JSON-LD) improves search rankings",
    "Building topic clusters for SaaS SEO authority",
    "Sitemap and RSS feed optimization for content websites",
    "International SEO strategy for bilingual content platforms",
    "Automated content generation pipelines with LLM APIs",
    "SEO meta tag optimization for AI-generated content",
    "Content gap analysis using LLM-powered topic research",
    # AI & LLM Technology
    "DeepSeek API integration guide for Python applications",
    "Comparison of open-source vs commercial LLM APIs for production",
    "Prompt engineering patterns for structured JSON output from LLMs",
    "LLM fallback strategies for resilient AI applications",
    "Model routing: intelligent LLM selection by task type",
    "Token usage optimization for cost-effective LLM operations",
    "Async LLM calls: patterns for high-throughput AI applications",
]

# Track used topics across restarts (persisted via DB slug check)
_auto_task_running = False


async def _auto_generate_loop():
    """Background task: generate 1-2 new posts daily."""
    global _auto_task_running
    if _auto_task_running:
        return
    _auto_task_running = True
    try:
        while True:
            # Run once every 24 hours
            await asyncio.sleep(86400)

            # Find unused topics by checking slug existence
            unused = []
            for topic in AUTO_TOPICS:
                slug = topic.lower().replace(" ", "-")[:60]
                if not get_post_by_slug(slug):
                    unused.append(topic)

            if not unused:
                print("[auto-gen] All topics used. Cycling topics...")
                # Rotate: use all topics again with new generation
                unused = list(AUTO_TOPICS)

            # Generate 1-2 posts per cycle
            count = min(2, len(unused))
            selected = random.sample(unused, count)
            for topic in selected:
                try:
                    print(f"[auto-gen] Generating: {topic[:60]}...")
                    post = generate(keyword=topic, word_count=1500)
                    save_post(post)
                    print(f"[auto-gen] ✅ {post.title[:60]} ({get_post_count()} total)")
                except Exception as e:
                    print(f"[auto-gen] ❌ {topic[:50]} — {e}")
    except asyncio.CancelledError:
        pass
    finally:
        _auto_task_running = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_newsletter()
    # Start auto-generation background task
    task = asyncio.create_task(_auto_generate_loop())
    yield
    task.cancel()


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


def _post_to_json(p: dict) -> dict:
    return {
        "title": p["title"],
        "slug": p["slug"],
        "meta_description": p.get("meta_description", ""),
        "tags": p.get("tags", []),
        "estimated_read_minutes": p.get("estimated_read_minutes", 3),
        "view_count": p.get("view_count", 0),
        "created_at": p.get("created_at", ""),
        "author": p.get("author", "CrossWave Team"),
    }


@app.get("/api/posts/popular")
async def api_popular():
    posts = get_popular_posts(limit=6)
    return [_post_to_json(p) for p in posts]


@app.get("/api/posts/recent")
async def api_recent(limit: int = 8, tag: str = ""):
    if tag:
        posts = get_posts_by_tag(tag, limit=limit)
    else:
        from app.database import get_all_posts as _gap
        posts = _gap(limit=limit)
    return [_post_to_json(p) for p in posts]


@app.get("/api/posts/by-tag/{tag}")
async def api_by_tag(tag: str, limit: int = 12):
    posts = get_posts_by_tag(tag, limit=limit)
    return [_post_to_json(p) for p in posts]


@app.get("/api/tags")
async def api_tags():
    from app.database import get_all_tags as _gat
    tags = _gat()
    return {"tags": tags, "total": len(tags)}


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
