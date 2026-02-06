"""
Advanced LLM Provider with Streaming and Structured Output
Gelişmiş LLM entegrasyonu - streaming, JSON mode, fallback chain.
"""
import json
import asyncio
from typing import Optional, AsyncGenerator, Any
from dataclasses import dataclass
import structlog

from src.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class LLMResponse:
    """Structured LLM response."""
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    cached: bool = False


class AdvancedLLMProvider:
    """
    Advanced LLM provider with:
    - Streaming responses
    - Structured JSON output
    - Multi-provider fallback
    - Response caching
    - Turkish language optimization
    """
    
    FALLBACK_CHAIN = ["groq", "ollama", "openai"]
    
    def __init__(self):
        self.primary = settings.llm_provider
        self._clients = {}
    
    def _get_client(self, provider: str):
        """Get or create client for provider."""
        if provider not in self._clients:
            self._clients[provider] = self._init_client(provider)
        return self._clients[provider]
    
    def _init_client(self, provider: str):
        """Initialize provider client."""
        if provider == "groq":
            try:
                from groq import Groq
                return Groq(api_key=settings.groq_api_key)
            except:
                return None
        elif provider == "openai":
            try:
                from openai import OpenAI
                return OpenAI(api_key=settings.openai_api_key)
            except:
                return None
        elif provider == "ollama":
            return {"base_url": settings.ollama_base_url, "model": settings.ollama_model}
        return None
    
    async def generate_structured(
        self,
        prompt: str,
        schema: dict,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """
        Generate structured JSON output.
        
        Args:
            prompt: User prompt
            schema: Expected JSON schema
            system_prompt: System instructions
            
        Returns:
            Parsed JSON matching schema
        """
        # Build schema-aware prompt
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
        enhanced_prompt = f"""{prompt}

Yanıtını aşağıdaki JSON formatında ver:
```json
{schema_str}
```

Sadece JSON döndür, başka açıklama ekleme."""

        response = await self.generate(
            prompt=enhanced_prompt,
            system_prompt=system_prompt or self._turkish_system_prompt(),
            temperature=0.3,  # Lower for structured output
        )
        
        # Parse JSON from response
        return self._extract_json(response.content)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate with automatic fallback."""
        last_error = None
        
        for provider in self._get_fallback_chain():
            try:
                result = await self._generate_with_provider(
                    provider=provider,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Provider {provider} failed", error=str(e))
                last_error = e
                continue
        
        # All providers failed, return mock
        logger.error("All LLM providers failed", error=str(last_error))
        return LLMResponse(
            content="LLM sağlayıcılarına ulaşılamadı.",
            model="mock",
            provider="mock",
        )
    
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Stream response tokens.
        
        Yields:
            Token strings as they arrive
        """
        client = self._get_client(self.primary)
        
        if self.primary == "groq" and client:
            async for chunk in self._stream_groq(client, prompt, system_prompt, temperature):
                yield chunk
        elif self.primary == "ollama":
            async for chunk in self._stream_ollama(client, prompt, system_prompt, temperature):
                yield chunk
        else:
            # Fallback: yield all at once
            response = await self.generate(prompt, system_prompt, temperature)
            yield response.content
    
    async def _stream_groq(
        self,
        client,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        """Stream from Groq."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error("Groq stream failed", error=str(e))
            yield f"Hata: {str(e)}"
    
    async def _stream_ollama(
        self,
        config: dict,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        """Stream from Ollama."""
        import httpx
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{config['base_url']}/api/generate",
                    json={
                        "model": config["model"],
                        "prompt": full_prompt,
                        "stream": True,
                        "options": {"temperature": temperature},
                    },
                    timeout=60.0,
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
        except Exception as e:
            logger.error("Ollama stream failed", error=str(e))
            yield f"Hata: {str(e)}"
    
    async def _generate_with_provider(
        self,
        provider: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Optional[LLMResponse]:
        """Generate with specific provider."""
        client = self._get_client(provider)
        
        if provider == "groq" and client:
            return await self._generate_groq(client, prompt, system_prompt, temperature, max_tokens)
        elif provider == "ollama" and client:
            return await self._generate_ollama(client, prompt, system_prompt, temperature, max_tokens)
        elif provider == "openai" and client:
            return await self._generate_openai(client, prompt, system_prompt, temperature, max_tokens)
        
        return None
    
    async def _generate_groq(self, client, prompt, system_prompt, temperature, max_tokens) -> LLMResponse:
        """Generate with Groq."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=settings.groq_model,
            provider="groq",
            tokens_used=response.usage.total_tokens if response.usage else 0,
        )
    
    async def _generate_ollama(self, config, prompt, system_prompt, temperature, max_tokens) -> LLMResponse:
        """Generate with Ollama."""
        import httpx
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config['base_url']}/api/generate",
                json={
                    "model": config["model"],
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
                timeout=60.0,
            )
            result = response.json()
            
            return LLMResponse(
                content=result.get("response", ""),
                model=config["model"],
                provider="ollama",
            )
    
    async def _generate_openai(self, client, prompt, system_prompt, temperature, max_tokens) -> LLMResponse:
        """Generate with OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=settings.openai_model,
            provider="openai",
            tokens_used=response.usage.total_tokens if response.usage else 0,
        )
    
    def _get_fallback_chain(self) -> list[str]:
        """Get fallback chain starting with primary."""
        chain = [self.primary]
        for p in self.FALLBACK_CHAIN:
            if p not in chain:
                chain.append(p)
        return chain
    
    def _turkish_system_prompt(self) -> str:
        """Default Turkish system prompt."""
        return """Sen KıyasGO için çalışan bir Türk e-ticaret zekası asistanısın.

Kurallar:
- Her zaman Türkçe yanıt ver
- Fiyatları ₺ ile göster
- Objektif ve veriye dayalı ol
- Kısa ve öz yanıtlar ver
- JSON istendiğinde sadece JSON döndür"""
    
    def _extract_json(self, text: str) -> dict:
        """Extract JSON from text response."""
        # Try to find JSON block
        import re
        
        # Look for ```json ... ``` block
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        
        # Try parsing the whole text
        try:
            return json.loads(text)
        except:
            pass
        
        # Try to find { ... } block
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        
        # Return empty dict if all fails
        return {}


# Singleton instance
_advanced_llm = None

def get_advanced_llm() -> AdvancedLLMProvider:
    """Get singleton advanced LLM provider."""
    global _advanced_llm
    if _advanced_llm is None:
        _advanced_llm = AdvancedLLMProvider()
    return _advanced_llm
