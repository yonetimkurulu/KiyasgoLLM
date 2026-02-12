"""
Mock LLM Provider
Standardized mock responses for fallback scenarios and testing.
"""
import json
from src.config import get_settings

settings = get_settings()

class MockLLMProvider:
    """Provides safe, predictable mock responses when LLMs fail."""
    
    @staticmethod
    def get_mock_response(prompt: str) -> str:
        """Return a generic mock response."""
        return "Bu, LLM sağlayıcısı olmadan oluşturulan güvenli bir örnek yanıttır. (Bağlantı Hatası)"

    @staticmethod
    def get_mock_analysis(product_name: str) -> str:
        """Return structured mock analysis."""
        return json.dumps({
            "headline": f"{product_name} - Örnek Analiz (Servis Kullanılamıyor)",
            "verdict_score": 5.0,
            "verdict_text": "Servis geçici olarak devre dışı olduğu için detaylı analiz yapılamadı.",
            "who_should_buy": ["Genel Kullanıcılar"],
            "who_should_avoid": [],
            "key_strengths": [{"point": "Temel Özellikler", "impact": "medium"}],
            "key_weaknesses": [{"point": "Veri Yok", "impact": "high"}]
        }, ensure_ascii=False)
