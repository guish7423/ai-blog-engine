"""AI Blog Engine — API + web interface for SEO blog generation."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.database import get_all_posts, get_post_by_slug, get_post_count, init_db, save_post
from app.generator import generate, usage

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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
async def blog_list(request: Request, page: int = 1):
    posts = get_all_posts(limit=20, offset=(page - 1) * 20)
    total = get_post_count()
    return templates.TemplateResponse(request, "blog.html", {
        "posts": posts,
        "page": page,
        "total": total,
        "pages": max(1, (total + 19) // 20),
    })


@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_detail(slug: str, request: Request):
    post = get_post_by_slug(slug)
    if not post:
        raise HTTPException(404, "Post not found")
    return templates.TemplateResponse(request, "blog_post.html", {"post": post})


@app.get("/usage")
async def usage_endpoint():
    return usage.summary()


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse(request, "pricing.html", {})
