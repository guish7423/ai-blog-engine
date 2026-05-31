"""AI Blog Engine — core SEO blog generation with LLM."""

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Literal

from app.config import settings


@dataclass
class BlogPost:
    title: str
    slug: str
    meta_description: str
    content_html: str
    headings: list[str]
    word_count: int
    estimated_read_minutes: int
    tags: list[str]
    faq: list[dict[str, str]]
    usage: dict
    author: str = "CrossWave Team"


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    calls: int = 0

    def record(self, pt: int, ct: int, model: str):
        self.prompt_tokens += pt
        self.completion_tokens += ct
        self.total_tokens += pt + ct
        self.calls += 1
        model_l = model.lower()
        if 'llama' in model_l:
            rate = 0.10 / 1_000_000
        elif 'flash' in model_l or 'deepseek' in model_l:
            rate = 0.07 / 1_000_000 + 0.28 / 1_000_000
        else:
            rate = 0.15 / 1_000_000
        self.cost_usd += (pt + ct) * rate

    def summary(self) -> dict:
        return {"calls": self.calls, "tokens": self.total_tokens, "cost_usd": round(self.cost_usd, 4)}


usage = Usage()


def _is_mock() -> bool:
    return os.environ.get("LLM_API_MOCK", str(settings.llm_api_mock)).lower() in ("true", "1")


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {"result": text}


def call_llm(prompt: str, system: str = "", json_mode: bool = True) -> dict:
    if _is_mock():
        return json.loads(os.environ.get("LLM_MOCK_RESPONSE", settings.llm_mock_response))
    import httpx
    body = {
        "model": settings.llm_model,
        "messages": [],
        "temperature": 0.7,
        "max_tokens": 4000,
    }
    if system:
        body["messages"].append({"role": "system", "content": system})
    body["messages"].append({"role": "user", "content": prompt})
    if json_mode and settings.supports_json_mode:
        body["response_format"] = {"type": "json_object"}
    last_err = None
    for attempt in range(3):
        try:
            resp = httpx.post(
                f"{settings.llm_api_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"},
                json=body, timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            usage.record(
                data.get("usage", {}).get("prompt_tokens", 0),
                data.get("usage", {}).get("completion_tokens", 0),
                data.get("model", settings.llm_model),
            )
            content = data["choices"][0]["message"]["content"]
            if json_mode:
                return _parse_json(content)
            return {"result": content}
        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            last_err = e
            if attempt < 2:
                time.sleep(2.0 * (2**attempt))
    # API all failed — fall back to mock mode gracefully
    print(f"WARN: LLM API failed after retries, falling back to mock: {last_err}")
    return json.loads(os.environ.get("LLM_MOCK_RESPONSE", settings.llm_mock_response))


# ── System Prompts ─────────────────────────────────────────────────────────

OUTLINE_SYSTEM = """You are an SEO content strategist. Given a topic and target keywords, create a blog post outline.

Output JSON with:
- title: SEO-optimized title (60-70 chars)
- slug: URL-friendly version
- meta_description: 150-160 chars
- headings: list of H2 headings (4-8)
- faq_questions: 3-5 FAQ questions
- tags: 5-8 relevant tags
- target_keywords: primary and secondary keywords
- search_intent: informational/commercial/transactional"""

CONTENT_SYSTEM = """You are an expert blog writer. Write complete, engaging blog post content.

Rules:
- Professional but conversational tone
- Each H2 section: 150-250 words
- Include specific examples, data points, actionable advice
- Natural keyword integration (no stuffing)
- Engaging opening paragraph (hook)
- Strong conclusion with CTA
- Subheadings (H3) within sections where appropriate

Output JSON with:
- sections: list of {heading, content_html} objects
- faq: list of {question, answer} objects
- word_count: integer"""


def generate(keyword: str, topic: str = "", word_count: int = 1500) -> BlogPost:
    """Generate a complete SEO blog post from a keyword/topic."""
    # Step 1: Generate outline
    prompt = f"Create an SEO blog outline for topic: {topic or keyword}\nPrimary keyword: {keyword}\nTarget word count: ~{word_count} words"
    outline = call_llm(prompt, OUTLINE_SYSTEM)

    title = outline.get("title", f"Complete Guide to {keyword}")
    slug = keyword.lower().replace(" ", "-")[:80]
    meta_desc = outline.get("meta_description", f"Learn everything about {keyword} - complete guide")
    headings = outline.get("headings", ["Introduction", "Key Benefits", "How It Works", "Best Practices", "FAQ"])
    questions = outline.get("faq_questions", [f"What is {keyword}?", f"How does {keyword} work?"])
    tags = outline.get("tags", [keyword, "AI", "guide"])

    # Step 2: Generate content sections
    content_prompt = f"""Write the full blog post content.

Topic: {topic or keyword}
Primary keyword: {keyword}
Title: {title}
Sections (write each): {', '.join(headings)}
FAQ questions to answer: {', '.join(questions)}
Target length: ~{word_count} words"""

    content_result = call_llm(content_prompt, CONTENT_SYSTEM)

    # Assemble
    sections = content_result.get("sections", [])
    faq = content_result.get("faq", [{"question": q, "answer": f"Information about {keyword}."} for q in questions])

    # Build HTML
    intro = sections[0]["content_html"] if sections else f"<p>Complete guide about {keyword}.</p>"
    content_html = f"<article>\n{intro}\n"
    for s in sections[1:]:
        content_html += f"<h2>{s['heading']}</h2>\n{s['content_html']}\n"
    if faq:
        content_html += "<h2>Frequently Asked Questions</h2>\n"
        for item in faq:
            content_html += f"<h3>{item['question']}</h3>\n<p>{item['answer']}</p>\n"
    content_html += "</article>"

    total_words = content_result.get("word_count", len(content_html.split()))

    return BlogPost(
        title=title,
        slug=slug,
        meta_description=meta_desc,
        content_html=content_html,
        headings=headings,
        word_count=total_words,
        estimated_read_minutes=max(1, total_words // 250),
        tags=tags,
        faq=faq,
        usage=usage.summary(),
    )
