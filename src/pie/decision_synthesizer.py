"""
Decision Synthesizer Service
Tüm sinyalleri birleştirerek final karar özetini üretir.
"""
from typing import Optional
import json
import structlog
from src.models.product import ProductSpecs, UsageContextScores
from src.llm import LLMProvider
from src.security.sanitizer import sanitize_user_input
from src.config import get_settings
from src.pie.signal_analyzer import SignalAnalyzer

logger = structlog.get_logger()
settings = get_settings()


class DecisionSynthesizer:
    """
    Synthesize all signals into final decision summary.
    
    Generates:
    - Headline
    - Who should buy / avoid
    - Key strengths / weaknesses
    - Verdict score and text
    """
    
    def __init__(self):
        self.llm = LLMProvider()
        self.analyzer = SignalAnalyzer()
    
    async def synthesize(
        self,
        product_id: str,
        name: str,
        specs: ProductSpecs,
        context_scores: UsageContextScores,
        price_info: Optional[dict] = None,
        reviews: list = None,
    ) -> dict:
        """
        Synthesize all data into decision summary using LLM with fallback.
        """
        try:
            return await self._synthesize_with_llm(
                name=name,
                specs=specs,
                context_scores=context_scores,
                price_info=price_info,
                reviews=reviews
            )
        except Exception as e:
            logger.error("LLM synthesis failed, falling back to rules", error=str(e))
            return await self._synthesize_rules(
                product_id, name, specs, context_scores, price_info, reviews
            )

    async def _synthesize_rules(
        self,
        product_id: str,
        name: str,
        specs: ProductSpecs,
        context_scores: UsageContextScores,
        price_info: Optional[dict] = None,
        reviews: list = None,
    ) -> dict:
        """
        Synthesize all data into decision summary.
        
        Args:
            product_id: Product identifier
            name: Product name
            specs: Normalized specifications
            context_scores: Usage context fit scores
            price_info: Pricing information
            reviews: User reviews (if available)
            
        Returns:
            Decision summary dictionary
        """
        # Determine best and avoid contexts
        best_for = self.analyzer.determine_best_for(context_scores)
        avoid_for = self.analyzer.determine_avoid_for(context_scores)
        
        # Generate who should buy/avoid
        who_should_buy = self.analyzer.generate_who_should_buy(specs, context_scores, best_for)
        who_should_avoid = self.analyzer.generate_who_should_avoid(specs, context_scores, avoid_for, price_info)
        
        # Extract strengths and weaknesses
        key_strengths = self.analyzer.extract_strengths(specs, context_scores)
        key_weaknesses = self.analyzer.extract_weaknesses(specs, price_info)
        
        # Calculate verdict score
        verdict_score = self.analyzer.calculate_verdict_score(specs, context_scores, price_info)
        
        # Generate headline and verdict text
        headline = await self._generate_headline(name, best_for, specs)
        verdict_text = self._generate_verdict_text(verdict_score, best_for)
        
        # Analyze sentiment from reviews
        sentiment, sentiment_score = self._analyze_reviews(reviews)
        
        return {
            "headline": headline,
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "best_for": best_for,
            "avoid_for": avoid_for,
            "who_should_buy": who_should_buy,
            "who_should_avoid": who_should_avoid,
            "key_strengths": key_strengths,
            "key_weaknesses": key_weaknesses,
            "verdict_score": verdict_score,
            "verdict_score": verdict_score,
            "verdict_text": verdict_text,
            "analysis_type": "rule_based",
        }
    
    
    # Methods _determine_best_for, _determine_avoid_for, _extract_strengths, 
    # _extract_weaknesses, _calculate_verdict_score have been moved to SignalAnalyzer.

    
    async def _generate_headline(self, name: str, best_for: list[str], specs: ProductSpecs) -> str:
        """Generate a catchy headline for the product."""
        # Simple rule-based headline (can be enhanced with LLM)
        
        if "photography" in best_for:
            return f"{name} - Mobil fotoğrafçılık için üst düzey seçim"
        elif "gaming" in best_for:
            return f"{name} - Oyun performansında sınır tanımaz"
        elif "business" in best_for:
            return f"{name} - İş profesyonelleri için güvenilir"
        elif "creator" in best_for:
            return f"{name} - İçerik üreticileri için ideal"
        elif "long_term" in best_for:
            return f"{name} - Uzun vadeli kullanım için akıllı tercih"
        elif "budget" in best_for:
            return f"{name} - Bütçe dostu en iyi fiyat/performans"
        
        return f"{name} - Genel kullanım için dengeli seçim"
    
    def _generate_verdict_text(self, score: float, best_for: list[str]) -> str:
        """Generate verdict summary text."""
        if score >= 8.5:
            return "Kategori lideri, neredeyse mükemmel."
        elif score >= 7.5:
            return "Çok iyi seçim, önerilir."
        elif score >= 6.5:
            return "İyi ürün, bazı eksiklikler var."
        elif score >= 5.5:
            return "Ortalama performans, alternatiflere bakın."
        else:
            return "Dikkatli olun, daha iyi seçenekler var."
    
    def _analyze_reviews(self, reviews: list) -> tuple[str, float]:
        """Analyze reviews for sentiment."""
        if not reviews:
            return "neutral", 0.5
        
        positive = sum(1 for r in reviews if r.get("sentiment") == "positive")
        negative = sum(1 for r in reviews if r.get("sentiment") == "negative")
        total = len(reviews)
        
        if total == 0:
            return "neutral", 0.5
        
        score = (positive - negative) / total * 0.5 + 0.5
        
        if score >= 0.7:
            sentiment = "positive"
        elif score <= 0.3:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return sentiment, round(score, 2)

    async def _synthesize_with_llm(
        self,
        name: str,
        specs: ProductSpecs,
        context_scores: UsageContextScores,
        price_info: Optional[dict],
        reviews: list,
    ) -> dict:
        """Synthesize using LLM."""
        # Prepare data for prompt
        specs_dict = specs.model_dump(exclude_none=True)
        scores_dict = context_scores.model_dump()
        
        # Sanitize potentially unsafe inputs from DB/Scraper
        safe_name = sanitize_user_input(name)
        safe_reviews = []
        if reviews:
            for r in reviews:
                if isinstance(r, dict):
                    # Create a safe copy
                    safe_r = r.copy()
                    if "text" in safe_r:
                        safe_r["text"] = sanitize_user_input(safe_r["text"])
                    safe_reviews.append(safe_r)
                else:
                    safe_reviews.append(r)

        prompt = self.llm.prompts.decision_synthesis_prompt(
            name=safe_name,
            specs=specs_dict,
            context_scores=scores_dict,
            reviews=safe_reviews
        )
        
        # Generate JSON
        response_json = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.llm.prompts.system_prompt_turkish(),
            temperature=0.7
        )
        
        # Parse JSON (naive parsing, ensuring it's valid)
        # Clean potential markdown code blocks if the LLM adds them
        cleaned_json = response_json.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned_json)
        
        # Calculate calculated fields that LLM might miss or we want to enforce
        # We still run determine_best_for/avoid_for for structure consistency if needed, 
        # but the LLM output is preferred for the text parts.
        
        # Backfill any missing fields from rules if necessary, or just trust LLM.
        # For 'best_for' and 'avoid_for', we trust our mathematical scoring for the *list*, 
        # but we can use LLM's text.
        # Actually, let's mix them. We use the LLM's rich text but maybe validate with scores?
        # For this implementation, let's fully trust the LLM's high-level output 
        # but ensure required fields exist.
        
        # Add sentiment analysis (hybrid: use code for sentiment score consistency)
        sentiment, sentiment_score = self._analyze_reviews(reviews)
        
        return {
            "headline": data.get("headline", f"{name} İncelemesi"),
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "best_for": data.get("who_should_buy", []), # Note: Mapping issue? No, 'best_for' is context keys (gaming, etc). 
                                                        # 'who_should_buy' is user personas.
                                                        # The LLM prompt asks for 'who_should_buy'. 
                                                        # The Pydantic model 'ProductIntelligence' has 'best_for' (list of strings, context IDs) AND 'who_should_buy' (list of strings).
                                                        # We need to compute 'best_for' (contexts) mathematically because it relies on the fixed context keys.
            "best_for": self.analyzer.determine_best_for(context_scores),  # Keep mathematical rigor for tags
            "avoid_for": self.analyzer.determine_avoid_for(context_scores), # Keep mathematical rigor for tags
            "who_should_buy": data.get("who_should_buy", []),
            "who_should_avoid": data.get("who_should_avoid", []),
            "key_strengths": data.get("key_strengths", []),
            "key_weaknesses": data.get("key_weaknesses", []),
            "verdict_score": float(data.get("verdict_score", 0.0)),
            "verdict_score": float(data.get("verdict_score", 0.0)),
            "verdict_text": data.get("verdict_text", ""),
            "analysis_type": "llm_generated",
        }
