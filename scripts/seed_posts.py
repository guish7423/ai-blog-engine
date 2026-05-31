"""Seed blog posts with rich demo content.

Usage:
    python scripts/seed_posts.py              # append (static posts)
    python scripts/seed_posts.py --fresh       # drop & recreate (static)
    python scripts/seed_posts.py --llm         # generate 20 posts via real LLM
    python scripts/seed_posts.py --llm N       # generate N posts via real LLM
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_connection, init_db, get_post_by_slug, save_post
from app.generator import BlogPost, generate as generate_post


POSTS = [
    # ── 1 ─────────────────────────────────────────────────────────────
    BlogPost(
        title="AI Content Marketing: The Complete Guide for 2026",
        slug="ai-content-marketing-guide-2026",
        meta_description="Learn how to leverage AI for content marketing in 2026. From strategy to execution, this guide covers tools, techniques, and best practices for modern marketers.",
        content_html="""<p>The landscape of content marketing has transformed dramatically. AI-powered tools now enable marketers to produce high-quality content at unprecedented scale, while maintaining personalization and relevance.</p>
<p>This guide covers everything you need to know about leveraging AI for your content marketing strategy in 2026.</p>
<h2>Why AI Content Marketing Matters</h2>
<p>Businesses using AI for content creation report 3x faster production cycles and 40% lower costs compared to traditional methods. AI doesn't replace writers—it amplifies their capabilities.</p>
<p>Key benefits include: consistent quality at scale, data-driven topic optimization, multilingual content generation, and real-time performance tracking.</p>
<h2>Top AI Tools for Content Creation</h2>
<p>The AI content tool ecosystem has matured significantly. Leading platforms now offer end-to-end solutions from ideation to publication, with built-in SEO optimization and performance analytics.</p>
<h2>Building Your AI Content Strategy</h2>
<p>A successful AI content strategy starts with clear goals. Define your target audience, identify content gaps through keyword research, and establish a consistent publishing cadence.</p>
<h2>Measuring Success</h2>
<p>Track metrics that matter: organic traffic growth, engagement rates, conversion attribution, and content ROI. AI tools can automate much of this analysis, providing actionable insights in real-time.</p>
<h2>Future Trends</h2>
<p>Looking ahead, AI content marketing will become increasingly personalized, with real-time content adaptation based on user behavior. Voice search optimization and AI-generated video content are the next frontiers.</p>""",
        headings=["Introduction", "Why AI Content Marketing Matters", "Top AI Tools for Content Creation",
                  "Building Your AI Content Strategy", "Measuring Success", "Future Trends"],
        word_count=1250,
        estimated_read_minutes=5,
        tags=["AI", "Content Marketing", "SEO", "Digital Marketing", "2026 Trends"],
        faq=[
            {"question": "What is AI content marketing?", "answer": "AI content marketing uses artificial intelligence tools to create, optimize, and distribute content at scale."},
            {"question": "Is AI-generated content SEO-friendly?", "answer": "Yes, when properly optimized. Modern AI tools generate content with proper keyword placement and structured headings."},
        ],
        usage={},
    ),
    # ── 2 ─────────────────────────────────────────────────────────────
    BlogPost(
        title="10 Proven SEO Strategies to Boost Organic Traffic in 2026",
        slug="seo-strategies-boost-organic-traffic-2026",
        meta_description="Discover 10 actionable SEO strategies that will drive organic traffic to your website in 2026. From AI-powered content optimization to technical SEO best practices.",
        content_html="""<p>Search engine optimization continues to evolve at a rapid pace. What worked in 2024 may harm your rankings today. This guide outlines 10 proven strategies that are driving results in 2026.</p>
<h2>1. AI-Powered Keyword Research</h2>
<p>Traditional keyword research tools are being augmented by AI that can predict search intent and content gaps with remarkable accuracy. Use AI to identify questions your audience is asking.</p>
<h2>2. Content Experience Optimization</h2>
<p>It's not just about keywords anymore. Search engines evaluate how users interact with your content. Focus on readability, visual elements, and structured data.</p>
<h2>3. Technical SEO Foundation</h2>
<p>A solid technical foundation is non-negotiable. Ensure your site has clean URL structures, proper canonical tags, XML sitemaps, and fast server response times.</p>
<h2>4. Topic Clusters & Pillar Pages</h2>
<p>Organize your content into topic clusters around pillar pages. This signals authority to search engines and provides a better user experience.</p>
<h2>5. Continuous Monitoring & Iteration</h2>
<p>SEO is not a set-it-and-forget-it discipline. Monitor your rankings, traffic patterns, and competitor movements regularly. Use data to inform strategy.</p>""",
        headings=["Introduction", "AI-Powered Keyword Research", "Content Experience Optimization",
                  "Technical SEO Foundation", "Topic Clusters & Pillar Pages", "Continuous Monitoring"],
        word_count=980,
        estimated_read_minutes=4,
        tags=["SEO", "Organic Traffic", "Digital Marketing", "Search Engine Optimization", "2026"],
        faq=[
            {"question": "How long does SEO take to show results?", "answer": "Most SEO efforts start showing meaningful results within 3-6 months."},
            {"question": "What's the most important SEO factor in 2026?", "answer": "Content relevance and user engagement metrics are increasingly important."},
        ],
        usage={},
    ),
    # ── 3 ─────────────────────────────────────────────────────────────
    BlogPost(
        title="The Future of SaaS: AI Agents Are Taking Over Operations",
        slug="future-saas-ai-agents-operations",
        meta_description="How AI agents are transforming SaaS operations—from customer support to content generation. Learn how to integrate AI agents into your SaaS business.",
        content_html="""<p>The SaaS landscape is undergoing a fundamental shift. AI agents—autonomous software that can perceive, reason, and act—are moving from experimental to essential in business operations.</p>
<h2>The Rise of AI Agents</h2>
<p>Unlike traditional automation tools that follow rigid rules, AI agents use language models to understand context, make decisions, and execute complex workflows. They're being deployed across every department.</p>
<p>The market for AI agents in SaaS is projected to reach $47 billion by 2027, with early adopters reporting 60% reduction in operational costs.</p>
<h2>Customer Support Automation</h2>
<p>AI agents handle tier-1 and tier-2 support tickets with human-level accuracy, escalating only complex issues to human agents. They operate 24/7 across multiple languages and channels.</p>
<h2>Content & Marketing Operations</h2>
<p>Content generation agents can research, outline, draft, and optimize blog posts, social media content, and email campaigns. They analyze performance data to continuously improve content strategy.</p>
<h2>Implementation Best Practices</h2>
<p>Start with a single workflow, measure results, then expand. Maintain human oversight for quality control. The key is augmenting human capabilities, not replacing them.</p>""",
        headings=["Introduction", "The Rise of AI Agents", "Customer Support Automation",
                  "Content & Marketing Operations", "Implementation Best Practices"],
        word_count=1100,
        estimated_read_minutes=4,
        tags=["SaaS", "AI Agents", "Automation", "Business Operations", "Future Tech"],
        faq=[
            {"question": "Will AI agents replace human workers?", "answer": "AI agents will transform roles rather than eliminate them. Tasks shift from execution to strategy and oversight."},
            {"question": "How much do AI agents cost?", "answer": "Simple agents cost $50-200/month, while enterprise-grade systems range from $1,000-10,000/month."},
        ],
        usage={},
    ),
    # ── 4 ─────────────────────────────────────────────────────────────
    BlogPost(
        title="How to Build a Blog That Generates Leads (Not Just Traffic)",
        slug="build-blog-generates-leads",
        meta_description="Stop chasing vanity traffic. Learn how to build a B2B blog that actually generates qualified leads and converts readers into customers.",
        content_html="""<p>Most business blogs are content graveyards—published with hope, visited by few, converting none. The difference comes down to strategy, not luck.</p>
<h2>The Lead-Generating Blog Framework</h2>
<p>Every blog post should serve a specific stage of the buyer's journey. Top-of-funnel content attracts and educates. Middle-of-funnel content presents solutions. Bottom-of-funnel content drives action.</p>
<h2>Content That Converts</h2>
<p>Lead-generating content addresses specific problems with actionable solutions. Use case studies, comparison guides, and how-to content. Include relevant CTAs that match reader intent.</p>
<h2>Conversion Optimization</h2>
<p>Place contextually relevant CTAs within your content, not just at the bottom. Use exit-intent popups, content upgrades, and live chat triggers based on reading behavior.</p>
<h2>Distribution Strategy</h2>
<p>Great content without distribution is a tree falling in an empty forest. Invest equally in creation and promotion. Use email newsletters, social media, and strategic partnerships.</p>
<h2>Measuring What Matters</h2>
<p>Stop optimizing for page views. Track lead attribution, conversion rates by content piece, cost per lead, and revenue influenced.</p>""",
        headings=["Introduction", "The Lead-Generating Blog Framework", "Content That Converts",
                  "Conversion Optimization", "Distribution Strategy", "Measuring What Matters"],
        word_count=1050,
        estimated_read_minutes=4,
        tags=["B2B Marketing", "Lead Generation", "Content Strategy", "Blogging", "Conversion"],
        faq=[
            {"question": "How many blog posts do I need?", "answer": "10 well-researched, optimized posts can outperform 100 generic ones. Aim for 2-4 high-quality posts per month."},
            {"question": "How long until my blog generates leads?", "answer": "With consistent effort, most B2B blogs start generating qualified leads within 3-6 months."},
        ],
        usage={},
    ),
    # ── 5 ─────────────────────────────────────────────────────────────
    BlogPost(
        title="Why Your Small Business Needs an AI Content Strategy",
        slug="small-business-ai-content-strategy",
        meta_description="Small businesses can compete with enterprise marketing budgets using AI. Learn how to create an AI content strategy that drives results on a budget.",
        content_html="""<p>Small businesses often assume AI content tools are for enterprises with big budgets. The reality is quite different. AI democratizes content creation, giving small teams the power to produce enterprise-quality content at a fraction of the cost.</p>
<h2>The Small Business Advantage</h2>
<p>Small businesses have a secret weapon: deep subject matter expertise and authentic voice. AI handles the heavy lifting of research and optimization—while your unique perspective makes the content genuinely valuable.</p>
<h2>Getting Started with AI Content</h2>
<p>Start with one content type (blog posts are easiest) and one channel. Learn the tools, refine your process, then expand. The key is consistent quality, not volume.</p>
<h2>Budget-Friendly Tools</h2>
<p>AI Blog Engine ($1.99/post) is perfect for small businesses. Most tools offer free tiers to experiment before committing.</p>
<h2>Creating Your First AI Content Plan</h2>
<p>1. Identify your top 10 customer questions. 2. Create blog posts answering each. 3. Optimize for SEO. 4. Share on social media. 5. Collect feedback and refine.</p>
<h2>Measuring ROI on a Budget</h2>
<p>Track simple metrics: website traffic from content, email signups, and direct inquiries. Use free tools like Google Analytics and Google Search Console.</p>""",
        headings=["Introduction", "The Small Business Advantage", "Getting Started with AI Content",
                  "Budget-Friendly Tools", "Creating Your First AI Content Plan", "Measuring ROI"],
        word_count=900,
        estimated_read_minutes=4,
        tags=["Small Business", "AI Content", "Content Strategy", "Budget Marketing", "SMB"],
        faq=[
            {"question": "Is AI content good enough for my business?", "answer": "Yes. Modern AI generates content that rivals human writers for most business topics."},
            {"question": "Do I need technical skills?", "answer": "No. Modern AI content tools have simple interfaces. If you can type a topic, you can create AI content."},
        ],
        usage={},
    ),
    # ── 6 ─────────────────────────────────────────────────────────────
    BlogPost(
        title="The Ultimate Guide to Technical SEO in 2026",
        slug="ultimate-guide-technical-seo-2026",
        meta_description="Master technical SEO in 2026 with this comprehensive guide. Covering Core Web Vitals, structured data, site architecture, and AI-powered technical audits.",
        content_html="""<p>Technical SEO is the foundation upon which all other SEO efforts are built. Without a solid technical foundation, even the best content will struggle to rank.</p>
<h2>Core Web Vitals Deep Dive</h2>
<p>Google's Core Web Vitals—LCP, INP, and CLS—remain critical ranking factors. LCP should be under 2.5 seconds, INP under 200ms, and CLS under 0.1.</p>
<p>Common fixes: optimize images, use CDN, implement lazy loading, reduce JavaScript execution time, and maintain stable layout dimensions.</p>
<h2>Structured Data & Schema Markup</h2>
<p>Schema markup helps search engines understand your content. Article, FAQ, HowTo, and Product schemas are particularly valuable. Use JSON-LD format for implementation.</p>
<h2>Site Architecture Best Practices</h2>
<p>A flat site architecture (any page reachable within 3-4 clicks from homepage) outperforms deep hierarchies. Use breadcrumb navigation and logical URL structures.</p>
<h2>Mobile-First Indexing</h2>
<p>Google now indexes mobile versions of websites first. Ensure your mobile experience is identical or better than desktop with proper viewport configuration.</p>
<h2>Technical Audit Tools & Process</h2>
<p>Conduct technical audits monthly. Check for crawl errors, broken links, duplicate content, missing meta tags, and XML sitemap issues.</p>""",
        headings=["Introduction", "Core Web Vitals Deep Dive", "Structured Data & Schema Markup",
                  "Site Architecture Best Practices", "Mobile-First Indexing", "Technical Audit Tools"],
        word_count=1150,
        estimated_read_minutes=5,
        tags=["Technical SEO", "Core Web Vitals", "Schema Markup", "SEO Audit", "2026 Guide"],
        faq=[
            {"question": "What is technical SEO?", "answer": "Technical SEO involves optimizing your website's infrastructure to help search engines crawl and index your content."},
            {"question": "How often should I do a technical audit?", "answer": "Monthly audits for active sites, quarterly for stable sites."},
        ],
        usage={},
    ),
    # ── 7 ─────────────────────────────────────────────────────────────
    BlogPost(
        title="From Zero to Blog: A Content Marketing Blueprint for Startups",
        slug="content-marketing-blueprint-startups",
        meta_description="A step-by-step content marketing blueprint for startups with zero audience. Build your blog from scratch and start generating traffic in 90 days.",
        content_html="""<p>You've launched your startup. You have zero audience, zero blog traffic, and zero content. This blueprint takes you from zero to a functioning content engine in 90 days.</p>
<h2>Month 1: Foundation</h2>
<p>Define your target audience and their top 20 questions. Set up your blog with proper SEO foundation. Create 4 cornerstone content pieces (2,000+ words each). Establish distribution channels.</p>
<h2>Month 2: Content Engine</h2>
<p>Publish 2-3 posts per week using AI tools to maintain quality at scale. Repurpose each post into social media content, email summaries, and discussion prompts. Start building your email list.</p>
<h2>Month 3: Growth & Distribution</h2>
<p>By now you have 25-35 posts. Double down on what's working. Guest post on relevant industry blogs. Experiment with paid promotion on top-performing posts.</p>
<h2>Essential Tools Stack</h2>
<p>AI Blog Engine for content generation, Canva for visuals, Buffer for social scheduling, Google Analytics for tracking. Total monthly cost: under $100.</p>
<h2>Common Startup Content Mistakes</h2>
<p>Mistakes: Writing about yourself instead of helping customers. Inconsistent publishing. Ignoring SEO basics. Not repurposing content. Giving up after 30 days.</p>""",
        headings=["Introduction", "Month 1: Foundation", "Month 2: Content Engine",
                  "Month 3: Growth & Distribution", "Essential Tools Stack", "Common Mistakes"],
        word_count=950,
        estimated_read_minutes=4,
        tags=["Startup Marketing", "Content Marketing", "Blog Blueprint", "Growth", "Beginner Guide"],
        faq=[
            {"question": "Can a startup succeed with content marketing alone?", "answer": "Yes. Many successful startups built their entire growth engine on content marketing."},
            {"question": "How much time does content marketing require?", "answer": "Expect 10-15 hours per week in the first 90 days. AI tools reduce this significantly."},
        ],
        usage={},
    ),
]


def run(fresh: bool = False):
    if fresh:
        conn = get_connection()
        conn.execute("DROP TABLE IF EXISTS blog_posts")
        conn.commit()
        conn.close()
        init_db()
        print("🗑️  Dropped old posts. Fresh start.\n")

    saved = 0
    for post in POSTS:
        slug = post.slug
        existing = get_post_by_slug(slug)
        if existing:
            print(f"  ⏭️  Skipped (exists): {post.title}")
            continue
        save_post(post)
        saved += 1
        print(f"  ✅ Saved: {post.title}")

    from app.database import get_post_count
    total = get_post_count()
    print(f"\n✨ Done! {saved} new posts saved. Total: {total} posts in database.")


LLM_TOPICS = [
    "AI Agent SaaS platform for Chinese entrepreneurs going global",
    "中国 SaaS 出海产品本地化最佳实践",
    "How to use AI content marketing for B2B lead generation",
    "Cross-border payment integration for SaaS platforms",
    "Building multilingual customer support with AI agents",
    "SaaS startup architecture from zero to production",
    "Technical SEO guide for AI-powered content sites",
    "AI translation vs human translation cost analysis",
    "Docker Compose production deployment for Python FastAPI",
    "Machine learning model deployment best practices",
    "Building a blog engine with FastAPI and SQLite",
    "Chart.js dashboard visualization for SaaS metrics",
    "AI-powered social media management automation",
    "HTMX real-time dashboard patterns for admin panels",
    "DeepSeek API integration for Chinese AI applications",
    "从零搭建 AI 内容工厂：完整技术栈",
    "Cross-border ecommerce AI customer service guide",
    "SaaS pricing psychology: freemium to enterprise tiers",
    "LLM fine-tuning vs prompt engineering cost comparison",
    "AI startup remote team management in the AI era",
]


def run_llm(count: int = 20):
    """Generate posts using real LLM."""
    from app.config import settings as cfg
    if not any([cfg.llm_api_key, os.environ.get("DEEPSEEK_API_KEY"),
                os.environ.get("LLM_API_KEY")]):
        print("❌ No LLM API key found. Set DEEPSEEK_API_KEY or LLM_API_KEY.")
        sys.exit(1)

    topics = LLM_TOPICS[:count]
    saved = 0
    for topic in topics:
        slug_part = topic.lower().replace(" ", "-")[:60]
        existing = get_post_by_slug(slug_part)
        if existing:
            print(f"  ⏭️  Exists: {topic[:50]}")
            continue
        try:
            post = generate_post(keyword=topic, word_count=1500)
            save_post(post)
            saved += 1
            print(f"  ✅ ({saved}/{len(topics)}) {post.title[:60]}")
        except Exception as e:
            print(f"  ❌ Failed: {topic[:50]} — {e}")

    from app.database import get_post_count
    total = get_post_count()
    print(f"\n✨ LLM seed done! {saved} new posts. Total: {total}")


if __name__ == "__main__":
    if "--llm" in sys.argv:
        idx = sys.argv.index("--llm")
        n = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit() else 20
        run_llm(n)
    else:
        run(fresh="--fresh" in sys.argv)
