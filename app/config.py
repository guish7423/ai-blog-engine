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
    llm_mock_response: str = field(default_factory=lambda: os.getenv("LLM_MOCK_RESPONSE", '{"meta_description":"Learn everything about this topic in this comprehensive guide.","headings":["Introduction","Key Benefits","How It Works","Best Practices","Case Studies"],"faq_questions":["What is this?","How does it work?","Why is it important?"],"tags":["guide","AI","technology"],"sections":[{"heading":"Introduction","content_html":"<p>This comprehensive guide covers everything you need to know about leveraging this technology for your business growth, from fundamental concepts to advanced implementation strategies. Modern businesses are increasingly adopting these approaches to stay competitive.</p>"},{"heading":"Key Benefits","content_html":"<p>There are numerous benefits to adopting this approach: automated operations, data-driven decision making, personalized experiences, cost reduction, and scalable growth. Organizations implementing these strategies see significant improvements in operational efficiency and customer satisfaction.</p>"},{"heading":"How It Works","content_html":"<p>The system works by processing data through sophisticated algorithms and machine learning models. These systems learn patterns, make predictions, and continuously improve over time. Modern implementations can handle a wide range of tasks efficiently and reliably.</p>"},{"heading":"Best Practices","content_html":"<p>To successfully implement this approach, start with clear objectives, choose the right tools, ensure quality data, monitor performance metrics, and iterate based on results. It is crucial to maintain human oversight while leveraging automated capabilities for optimal outcomes.</p>"}],"faq":[{"question":"What is this topic about?","answer":"This is a comprehensive guide covering all essential aspects of the subject, from fundamentals to advanced concepts."}],"word_count":2000}'))

    # Pricing
    price_per_post: float = 1.99  # $ per generated post (pay-as-you-go)
    monthly_sub: float = 29.99     # $ per month (20 posts included)
    annual_sub: float = 249.99     # $ per year (240 posts)


settings = Settings()
