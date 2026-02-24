"""
LLM Provider Abstraction
Çoklu LLM sağlayıcısını destekleyen abstraction layer.
"""
from typing import Optional
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings
from src.llm.prompts import PromptTemplates
from src.llm.mock_provider import MockLLMProvider

logger = structlog.get_logger()
settings = get_settings()


class LLMProvider:
    """
    Abstraction layer for multiple LLM providers.
    
    Supports:
    - Groq (default, free tier)
    - Ollama (local, privacy-first)
    - OpenAI (fallback)
    """
    
    def __init__(self):
        self.provider = settings.llm_provider
        self.prompts = PromptTemplates()
        self._client = None
    
    @property
    def client(self):
        """Lazy-load LLM client."""
        if self._client is None:
            self._client = self._initialize_client()
        return self._client
    
    def _initialize_client(self):
        """Initialize appropriate LLM client."""
        if self.provider == "groq":
            return self._init_groq()
        elif self.provider == "ollama":
            return self._init_ollama()
        elif self.provider == "openai":
            return self._init_openai()
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")
    
    def _init_groq(self):
        """Initialize Groq client."""
        try:
            from groq import Groq
            if not settings.groq_api_key:
                logger.warning("Groq API key not configured, using mock fallback")
                return None
            return Groq(api_key=settings.groq_api_key)
        except ImportError:
            logger.warning("Groq package not installed, using mock fallback")
            return None
        except Exception as e:
            logger.error("Groq client initialization failed", error=str(e))
            return None
    
    def _init_ollama(self):
        """Initialize Ollama client."""
        # Ollama uses HTTP API
        return {
            "base_url": settings.ollama_base_url,
            "model": settings.ollama_model,
        }
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not configured, using mock fallback")
                return None
            return OpenAI(api_key=settings.openai_api_key)
        except ImportError:
            logger.warning("OpenAI package not installed, using mock fallback")
            return None
        except Exception as e:
            logger.error("OpenAI client initialization failed", error=str(e))
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text using configured LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Creativity (0-1)
            
        Returns:
            Generated text
        """
        logger.info("Generating with LLM", provider=self.provider)
        
        if self.provider == "groq":
            return await self._generate_groq(prompt, system_prompt, max_tokens, temperature)
        elif self.provider == "ollama":
            return await self._generate_ollama(prompt, system_prompt, max_tokens, temperature)
        elif self.provider == "openai":
            return await self._generate_openai(prompt, system_prompt, max_tokens, temperature)
        
        # Fallback to mock response
        return self._mock_response(prompt)
    
    async def _generate_groq(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using Groq."""
        if not self.client:
            return self._mock_response(prompt)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Groq generation failed", error=str(e), model=settings.groq_model)
            return self._mock_response(prompt)
    
    async def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using Ollama."""
        import httpx
        
        config = self.client
        base_url = config["base_url"]
        model = config["model"]
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": temperature,
                        }
                    },
                    timeout=60.0,
                )
                result = response.json()
                return result.get("response", "")
        except Exception as e:
            logger.error("Ollama generation failed", error=str(e), base_url=config["base_url"])
            return self._mock_response(prompt)
    
    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using OpenAI."""
        if not self.client:
            return self._mock_response(prompt)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI generation failed", error=str(e), model=settings.openai_model)
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """Generate mock response for testing."""
        return MockLLMProvider.get_mock_response(prompt)
    
    async def generate_product_analysis(self, product_data: dict) -> dict:
        """Generate product analysis using LLM."""
        prompt = self.prompts.product_analysis(product_data)
        response = await self.generate(
            prompt=prompt,
            system_prompt=self.prompts.system_prompt_turkish(),
            temperature=0.5,
        )
        return {"analysis": response}
    
    async def generate_comparison(self, products: list[dict]) -> dict:
        """Generate product comparison using LLM."""
        prompt = self.prompts.product_comparison(products)
        response = await self.generate(
            prompt=prompt,
            system_prompt=self.prompts.system_prompt_turkish(),
            temperature=0.5,
        )
        return {"comparison": response}
    
    async def generate_recommendation(
        self,
        context: str,
        category: str,
        budget: Optional[int],
        products: list[dict],
    ) -> dict:
        """Generate product recommendation using LLM."""
        prompt = self.prompts.product_recommendation(context, category, budget, products)
        response = await self.generate(
            prompt=prompt,
            system_prompt=self.prompts.system_prompt_turkish(),
            temperature=0.6,
        )
        return {"recommendation": response}
