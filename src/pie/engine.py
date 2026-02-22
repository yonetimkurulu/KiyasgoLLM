"""
Product Intelligence Engine (PIE)
Ham veriyi karar sinyaline dönüştüren ana motor.

Database-backed: Tries repository first, falls back to mock if DB is empty.
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
from src.db.session import SessionLocal
from src.db.repository import ProductRepository

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
    
    def _get_repo(self):
        """Create a short-lived repository with its own session."""
        db = SessionLocal()
        return ProductRepository(db), db

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
        
        # Step 1: Get raw product data (DB first, mock fallback)
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
        
        # Try DB first
        repo, db = self._get_repo()
        try:
            db_results = repo.search(query, category=category, limit=limit)
            if db_results:
                results = []
                for p in db_results:
                    results.append({
                        "id": p.id,
                        "name": p.name,
                        "headline": p.headline or f"{p.name} - AI Analizi",
                        "verdict_score": p.verdict_score,
                        "best_for": (p.best_for or [])[:2],
                    })
                return results
        finally:
            db.close()
        
        # Fallback: mock search → analyze
        mock_results = self._mock_search(query, category, limit)
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
        
        # Try DB first
        repo, db = self._get_repo()
        try:
            if context:
                db_products = repo.get_top_for_context(category, context, budget=budget, limit=limit)
            else:
                db_products = repo.get_by_category(category, budget=budget, limit=limit)
            
            if db_products:
                product_ids = [p.id for p in db_products]
            else:
                product_ids = [p["id"] for p in self._mock_category_products(category, budget, limit)]
        finally:
            db.close()
        
        results = []
        for pid in product_ids:
            intel = await self.analyze_product(pid, context=context)
            results.append(intel)
        
        # Sort by context score if context provided, else by verdict
        if context and results and hasattr(results[0].context_scores, context):
            results.sort(key=lambda x: getattr(x.context_scores, context, 0), reverse=True)
        else:
            results.sort(key=lambda x: x.verdict_score, reverse=True)
        
        return results[:limit]
    
    async def _fetch_product_data(self, product_id: str) -> dict:
        """
        Fetch raw product data.
        Tries database first, falls back to mock data.
        """
        # Try DB
        repo, db = self._get_repo()
        try:
            product = repo.get_by_id(product_id)
            if product:
                return self._db_product_to_dict(product)
        finally:
            db.close()
        
        # Fallback to mock data
        return self._mock_product_data(product_id)
    
    def _db_product_to_dict(self, p) -> dict:
        """Convert a DB Product row into the raw_data dict format the pipeline expects."""
        specs = p.specs or {}
        # If specs are stored as structured JSON, format them as strings for normalizer
        raw_specs = {}
        if specs.get("screen_size"):
            raw_specs["screen_size"] = f"{specs['screen_size']} inch"
        if specs.get("screen_type"):
            raw_specs["screen_type"] = specs["screen_type"]
        if specs.get("chipset"):
            raw_specs["chipset"] = specs["chipset"]
        if specs.get("ram_gb"):
            raw_specs["ram"] = f"{specs['ram_gb']}GB"
        if specs.get("storage_gb"):
            raw_specs["storage"] = f"{specs['storage_gb']}GB"
        if specs.get("battery_mah"):
            raw_specs["battery"] = f"{specs['battery_mah']}mAh"
        if specs.get("camera_mp"):
            raw_specs["camera"] = f"{specs['camera_mp']}MP"
        if specs.get("weight_grams"):
            raw_specs["weight"] = f"{specs['weight_grams']}g"

        pricing = None
        if p.price_avg:
            pricing = {
                "current_low": p.price_low or p.price_avg,
                "current_high": p.price_high or p.price_avg,
                "average": p.price_avg,
                "currency": p.currency or "TRY",
                "trend": "stable",
                "buy_signal": "neutral",
            }

        return {
            "name": p.name,
            "brand": p.brand,
            "category": p.category,
            "release_date": p.release_date,
            "specs": raw_specs,
            "pricing": pricing,
            "price": p.price_avg or 0,
            "reviews": [],
        }

    # ---- Mock data fallbacks ----

    def _mock_product_data(self, product_id: str) -> dict:
        """Mock data for products not in the database."""
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
                    {"text": "Kamera mukemmel!", "sentiment": "positive"},
                    {"text": "Biraz agir ama kaliteli", "sentiment": "neutral"},
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
                    {"text": "Performans ust duzey", "sentiment": "positive"},
                ],
            },
        }
        
        if product_id in mock_products:
            return mock_products[product_id]
        
        # Generic fallback
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

    def _mock_search(self, query: str, category: Optional[str], limit: int) -> list[dict]:
        """Mock search fallback."""
        base_products = [
            {"id": "samsung-galaxy-s24-ultra"},
            {"id": "iphone-16-pro"},
            {"id": "google-pixel-9-pro"},
            {"id": "xiaomi-14-ultra"},
            {"id": "oneplus-12"},
        ]
        return base_products[:limit]
    
    def _mock_category_products(self, category: str, budget: Optional[int], limit: int) -> list[dict]:
        """Mock category products fallback."""
        return [
            {"id": "samsung-galaxy-s24-ultra"},
            {"id": "iphone-16-pro"},
            {"id": "google-pixel-9-pro"},
        ][:limit]
