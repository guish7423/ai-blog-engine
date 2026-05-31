"""AI Blog Engine — configuration."""

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Auto-detect LLM backend."""

    llm_api_key: str = ""
    llm_api_base_url: str = ""
    llm_model: str = ""
    supports_json_mode: bool = False

    def __post_init__(self):
        key = os.getenv("LLM_API_KEY", "")
        if key:
            self.llm_api_key = key
            self.llm_api_base_url = os.getenv("LLM_API_BASE_URL", "https://api.deepseek.com/v1")
            self.llm_model = os.getenv("LLM_MODEL", "deepseek-chat")
            self.supports_json_mode = True
            return

        nvidia = os.getenv("NVIDIA_API_KEY", "")
        if nvidia:
            self.llm_api_key = nvidia
            self.llm_api_base_url = "https://integrate.api.nvidia.com/v1"
            self.llm_model = "meta/llama-3.1-8b-instruct"
            self.supports_json_mode = False
            return

        volc = os.getenv("VOLC_ENGINE_API_KEY", "")
        if volc:
            self.llm_api_key = volc
            self.llm_api_base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
            self.llm_model = "doubao-seed-2.0-code"
            self.supports_json_mode = False
            return

        # No API key configured → auto-enable mock mode
        self.llm_api_mock = True

    # LLM
    llm_api_mock: bool = field(default_factory=lambda: os.getenv("LLM_API_MOCK", "false").lower() in ("true", "1"))
    llm_mock_response: str = field(default_factory=lambda: os.getenv("LLM_MOCK_RESPONSE", '{"title":"Complete Guide to {keyword}","slug":"{keyword}","meta_description":"Learn everything about {keyword} in this comprehensive guide.","headings":["Introduction","Key Benefits","How It Works","Best Practices","Case Studies"],"faq_questions":["What is {keyword}?","How does {keyword} work?","Why is {keyword} important?"],"tags":["{keyword}","AI","guide"],"sections":[{"heading":"Introduction","content_html":"<p>'+'x'*500+'</p>"},{"heading":"Key Benefits","content_html":"<p>'+'x'*500+'</p>"},{"heading":"How It Works","content_html":"<p>'+'x'*500+'</p>"},{"heading":"Best Practices","content_html":"<p>'+'x'*500+'</p>"}],"faq":[{"question":"What is this topic?","answer":"This is a comprehensive guide covering all aspects."}],"word_count":2000}'))

    # Pricing
    price_per_post: float = 1.99  # $ per generated post (pay-as-you-go)
    monthly_sub: float = 29.99     # $ per month (20 posts included)
    annual_sub: float = 249.99     # $ per year (240 posts)


settings = Settings()
