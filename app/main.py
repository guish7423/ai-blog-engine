"""AI Blog Engine — API + web interface for SEO blog generation."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.generator import generate, usage

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="AI Blog Engine",
    description="Generate SEO-optimized blog posts with AI",
    version="1.0.0",
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
    return {"status": "ok", "app": "AI Blog Engine"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/generate")
async def generate_post(req: GenerateRequest):
    if not req.keyword.strip():
        raise HTTPException(400, "keyword is required")
    post = generate(req.keyword, req.topic, max(500, min(5000, req.word_count)))
    return {
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


@app.get("/usage")
async def usage_endpoint():
    return usage.summary()


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse(request, "pricing.html", {})
