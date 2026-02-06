"""
Product Intelligence Engine (PIE)
Ham veriyi karar sinyaline dönüştüren ana motor.
"""
from typing import Optional
import structlog

from src.models.product import (
    ProductIntelligence,
    ProductSpecs,
    PricingInfo,
    UsageContextScores,
)
from src.pie.normalizer import SpecNormalizer
from src.pie.usage_inference import UsageInferenceService
from src.pie.decision_synthesizer import DecisionSynthesizer
from src.llm import LLMProvider

logger = structlog.get_logger()


class ProductIntelligenceEngine:
    """
    Main PIE class that orchestrates all sub-services.
    
    Pipeline:
    1. Normalization: Raw specs → Structured specs
    2. Usage Inference: Specs → Context scores
    3. Decision Synthesis: All data → Final intelligence
    """
    
    def __init__(self):
        self.normalizer = SpecNormalizer()
        self.usage_inference = UsageInferenceService()
        self.decision_synthesizer = DecisionSynthesizer()
        self.llm = LLMProvider()
    
    async def analyze_product(
        self,
        product_id: str,
        context: Optional[str] = None,
    ) -> ProductIntelligence:
        """
        Analyze a product and generate full intelligence.
        
        Args:
            product_id: Product identifier
            context: Optional usage context for focused analysis
            
        Returns:
            ProductIntelligence with all analysis results
        """
        logger.info("Analyzing product", product_id=product_id, context=context)
        
        # Step 1: Get raw product data (mock for now)
        raw_data = await self._fetch_product_data(product_id)
        
        # Step 2: Normalize specifications
        specs = self.normalizer.normalize(raw_data.get("specs", {}))
        
        # Step 3: Infer usage contexts
        context_scores = self.usage_inference.infer_contexts(specs, raw_data.get("price", 0))
        
        # Step 4: Synthesize decision
        decision = await self.decision_synthesizer.synthesize(
            product_id=product_id,
            name=raw_data.get("name", product_id),
            specs=specs,
            context_scores=context_scores,
            price_info=raw_data.get("pricing"),
            reviews=raw_data.get("reviews", []),
        )
        
        # Build final intelligence
        intelligence = ProductIntelligence(
            product_id=product_id,
            name=raw_data.get("name", product_id),
            category=raw_data.get("category", "unknown"),
            brand=raw_data.get("brand", "unknown"),
            release_date=raw_data.get("release_date"),
            
            headline=decision["headline"],
            sentiment=decision["sentiment"],
            sentiment_score=decision["sentiment_score"],
            
            specs=specs,
            pricing=PricingInfo(**raw_data["pricing"]) if raw_data.get("pricing") else None,
            
            best_for=decision["best_for"],
            avoid_for=decision["avoid_for"],
            context_scores=context_scores,
            
            who_should_buy=decision["who_should_buy"],
            who_should_avoid=decision["who_should_avoid"],
            key_strengths=decision["key_strengths"],
            key_weaknesses=decision["key_weaknesses"],
            
            verdict_score=decision["verdict_score"],
            verdict_text=decision["verdict_text"],
        )
        
        logger.info("Analysis complete", product_id=product_id, verdict_score=intelligence.verdict_score)
        return intelligence
    
    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Search and analyze products.
        
        Returns list of products with basic intelligence.
        """
        logger.info("Searching products", query=query, category=category)
        
        # Mock search results (would connect to database/search engine)
        mock_results = await self._mock_search(query, category, limit)
        
        results = []
        for item in mock_results:
            intel = await self.analyze_product(item["id"])
            results.append({
                "id": item["id"],
                "name": intel.name,
                "headline": intel.headline,
                "verdict_score": intel.verdict_score,
                "best_for": intel.best_for[:2],
            })
        
        return results
    
    async def get_top_products(
        self,
        category: str,
        budget: Optional[int] = None,
        context: Optional[str] = None,
        limit: int = 5,
    ) -> list[ProductIntelligence]:
        """Get top products for a category."""
        logger.info("Getting top products", category=category, budget=budget, context=context)
        
        # Mock implementation
        mock_products = await self._mock_category_products(category, budget, limit)
        
        results = []
        for product in mock_products:
            intel = await self.analyze_product(product["id"], context=context)
            results.append(intel)
        
        # Sort by context score if context provided, else by verdict
        if context and hasattr(results[0].context_scores, context):
            results.sort(key=lambda x: getattr(x.context_scores, context, 0), reverse=True)
        else:
            results.sort(key=lambda x: x.verdict_score, reverse=True)
        
        return results[:limit]
    
    async def _fetch_product_data(self, product_id: str) -> dict:
        """
        Fetch raw product data from database/API.
        Currently returns mock data.
        """
        # Mock data for demonstration
        mock_products = {
            "samsung-galaxy-s24-ultra": {
                "name": "Samsung Galaxy S24 Ultra",
                "brand": "Samsung",
                "category": "flagship_smartphone",
                "release_date": "2024-01",
                "specs": {
                    "screen_size": "6.8 inch",
                    "screen_type": "Dynamic AMOLED 2X",
                    "chipset": "Snapdragon 8 Gen 3",
                    "ram": "12GB",
                    "storage": "256GB / 512GB / 1TB",
                    "battery": "5000mAh",
                    "camera": "200MP + 12MP + 50MP + 10MP",
                    "weight": "232g",
                },
                "pricing": {
                    "current_low": 85000,
                    "current_high": 95000,
                    "average": 89999,
                    "currency": "TRY",
                    "trend": "declining",
                    "buy_signal": "wait",
                },
                "reviews": [
                    {"text": "Kamera mükemmel!", "sentiment": "positive"},
                    {"text": "Biraz ağır ama kaliteli", "sentiment": "neutral"},
                ],
            },
            "iphone-16-pro": {
                "name": "iPhone 16 Pro",
                "brand": "Apple",
                "category": "flagship_smartphone",
                "release_date": "2024-09",
                "specs": {
                    "screen_size": "6.3 inch",
                    "screen_type": "Super Retina XDR OLED",
                    "chipset": "A18 Pro",
                    "ram": "8GB",
                    "storage": "128GB / 256GB / 512GB / 1TB",
                    "battery": "3582mAh",
                    "camera": "48MP + 48MP + 12MP",
                    "weight": "199g",
                },
                "pricing": {
                    "current_low": 74000,
                    "current_high": 82000,
                    "average": 78000,
                    "currency": "TRY",
                    "trend": "stable",
                    "buy_signal": "neutral",
                },
                "reviews": [
                    {"text": "iOS ekosistemi harika", "sentiment": "positive"},
                    {"text": "Performans üst düzey", "sentiment": "positive"},
                ],
            },
        }
        
        # Return mock data or generate default
        if product_id in mock_products:
            return mock_products[product_id]
        
        # Generate mock for unknown products
        return {
            "name": product_id.replace("-", " ").title(),
            "brand": "Unknown",
            "category": "smartphone",
            "specs": {
                "screen_size": "6.5 inch",
                "ram": "8GB",
                "storage": "128GB",
                "battery": "4500mAh",
                "camera": "50MP",
                "weight": "180g",
            },
            "pricing": {
                "current_low": 20000,
                "current_high": 25000,
                "average": 22500,
                "currency": "TRY",
                "trend": "stable",
                "buy_signal": "neutral",
            },
            "reviews": [],
        }
    
    async def _mock_search(self, query: str, category: Optional[str], limit: int) -> list[dict]:
        """Mock search implementation."""
        # Return some mock results based on query
        base_products = [
            {"id": "samsung-galaxy-s24-ultra"},
            {"id": "iphone-16-pro"},
            {"id": "google-pixel-9-pro"},
            {"id": "xiaomi-14-ultra"},
            {"id": "oneplus-12"},
        ]
        return base_products[:limit]
    
    async def _mock_category_products(self, category: str, budget: Optional[int], limit: int) -> list[dict]:
        """Mock category products."""
        return [
            {"id": "samsung-galaxy-s24-ultra"},
            {"id": "iphone-16-pro"},
            {"id": "google-pixel-9-pro"},
        ][:limit]
