"""
Tests for LLM Provider modules.

Tests focus on unit-testable logic (no external API calls).
"""
import pytest
from src.llm.advanced_provider import AdvancedLLMProvider, LLMResponse


class TestAdvancedLLMProviderUnit:
    """Tests for AdvancedLLMProvider internal logic."""

    def test_fallback_chain_starts_with_primary(self):
        provider = AdvancedLLMProvider()
        chain = provider._get_fallback_chain()
        assert chain[0] == provider.primary

    def test_fallback_chain_contains_all_providers(self):
        provider = AdvancedLLMProvider()
        chain = provider._get_fallback_chain()
        for p in ["groq", "ollama", "openai"]:
            assert p in chain

    def test_fallback_chain_no_duplicates(self):
        provider = AdvancedLLMProvider()
        chain = provider._get_fallback_chain()
        assert len(chain) == len(set(chain))

    def test_turkish_system_prompt(self):
        provider = AdvancedLLMProvider()
        prompt = provider._turkish_system_prompt()
        assert "Türkçe" in prompt
        assert "KıyasGO" in prompt
        assert "₺" in prompt

    def test_extract_json_from_code_block(self):
        provider = AdvancedLLMProvider()
        text = '''İşte analiz:
```json
{"puan": 8, "oneri": "Alınmalı"}
```'''
        result = provider._extract_json(text)
        assert result == {"puan": 8, "oneri": "Alınmalı"}

    def test_extract_json_raw(self):
        provider = AdvancedLLMProvider()
        text = '{"puan": 7, "oneri": "Beklenmeli"}'
        result = provider._extract_json(text)
        assert result == {"puan": 7, "oneri": "Beklenmeli"}

    def test_extract_json_embedded(self):
        provider = AdvancedLLMProvider()
        text = 'Sonuç: {"puan": 9} şeklinde.'
        result = provider._extract_json(text)
        assert result == {"puan": 9}

    def test_extract_json_invalid_returns_empty(self):
        provider = AdvancedLLMProvider()
        text = "Bu bir JSON değil, sadece düz metin."
        result = provider._extract_json(text)
        assert result == {}

    def test_extract_json_code_block_without_json_label(self):
        provider = AdvancedLLMProvider()
        text = '''```
{"ozet": "İyi telefon"}
```'''
        result = provider._extract_json(text)
        assert result == {"ozet": "İyi telefon"}

    @pytest.mark.asyncio
    async def test_generate_all_fail_returns_mock(self):
        """When all providers fail, a mock response should be returned."""
        provider = AdvancedLLMProvider()
        # Override _generate_with_provider to always fail
        async def failing_provider(*args, **kwargs):
            raise Exception("Provider unavailable")
        
        provider._generate_with_provider = failing_provider
        
        result = await provider.generate("test prompt")
        assert isinstance(result, LLMResponse)
        assert result.provider == "mock"


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_creation(self):
        response = LLMResponse(
            content="Merhaba",
            model="llama-3.3-70b",
            provider="groq",
            tokens_used=42,
        )
        assert response.content == "Merhaba"
        assert response.model == "llama-3.3-70b"
        assert response.provider == "groq"
        assert response.tokens_used == 42
        assert response.cached is False

    def test_defaults(self):
        response = LLMResponse(content="test", model="m", provider="p")
        assert response.tokens_used == 0
        assert response.cached is False
