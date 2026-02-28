"""
KıyasGO AI Intelligence Service - Configuration
"""
from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Provider
    llm_provider: Literal["groq", "ollama", "openai"] = "groq"
    groq_api_key: str = ""
    openai_api_key: str = ""
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    
    # Groq default model
    groq_model: str = "llama-3.3-70b-versatile"
    
    # OpenAI default model
    openai_model: str = "gpt-4o-mini"
    
    # Cache
    redis_url: str = "redis://localhost:6379"
    cache_ttl_products: int = 86400  # 24 hours
    cache_ttl_signals: int = 7200     # 2 hours
    cache_ttl_comparison: int = 3600  # 1 hour
    cache_enabled: bool = True
    
    # SerpApi (Google Shopping)
    serpapi_api_key: str = ""
    serpapi_gl: str = "tr"
    serpapi_hl: str = "tr"
    cache_ttl_shopping: int = 21600  # 6 hours
    shopping_sync_on_startup: bool = False
    
    # Database
    database_url: str = ""
    
    # API
    api_version: str = "v1"
    debug: bool = True
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60
    
    # Scoring Thresholds (Architecture Rule #2)
    price_high_threshold: int = 90000
    price_medium_threshold: int = 70000
    camera_mp_high: int = 108
    camera_mp_mid: int = 50
    battery_mah_large: int = 5000
    battery_mah_small: int = 4000
    weight_heavy: int = 220
    storage_min: int = 128
    
    score_threshold_best: float = 0.7
    score_threshold_avoid: float = 0.4
    
    # Review Analysis
    review_min_snippet_length: int = 15
    review_max_batch_size: int = 20
    review_hollow_patterns: str = r"çok iyi|harika|mükemmel|kötü|berbat|güzel|süper|fena değil"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
