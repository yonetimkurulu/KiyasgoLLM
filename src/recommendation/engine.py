"""
Recommendation Engine
Context-based ürün öneri motoru.
"""
from typing import Optional
import structlog

from src.models.product import RecommendedProduct
from src.pie import ProductIntelligenceEngine

logger = structlog.get_logger()


class RecommendationEngine:
    """
    Product recommendation engine.
    
    Generates context-aware recommendations based on:
    - Usage context (gaming, photography, etc.)
    - Budget constraints
    - Product intelligence scores
    """
    
    def __init__(self):
        self.pie = ProductIntelligenceEngine()
    
    async def get_best_for(
        self,
        context: str,
        category: str,
        budget: Optional[int] = None,
        limit: int = 5,
    ) -> list[RecommendedProduct]:
        """
        Get best products for a specific use case.
        
        Args:
            context: Usage context (gaming, photography, etc.)
            category: Product category
            budget: Optional maximum budget in TRY
            limit: Maximum number of recommendations
            
        Returns:
            List of RecommendedProduct sorted by fit score
        """
        logger.info(
            "Generating recommendations",
            context=context,
            category=category,
            budget=budget,
        )
        
        # Get candidate products
        candidates = await self._get_candidates(category, budget)
        
        # Score each candidate for the context
        scored = []
        for candidate in candidates:
            # Get product intelligence
            intel = await self.pie.analyze_product(candidate["id"], context=context)
            
            # Get context-specific score
            fit_score = getattr(intel.context_scores, context, 0.5)
            
            # Apply budget bonus (if under budget, gets small boost)
            if budget and intel.pricing:
                if intel.pricing.average <= budget * 0.8:
                    fit_score = min(fit_score + 0.05, 1.0)
            
            # Generate why text
            why = self._generate_why(intel, context, budget)
            
            scored.append(RecommendedProduct(
                rank=0,  # Will be set after sorting
                product_id=intel.product_id,
                name=intel.name,
                price=intel.pricing.average if intel.pricing else 0,
                fit_score=round(fit_score, 2),
                why=why,
            ))
        
        # Sort by fit score
        scored.sort(key=lambda x: x.fit_score, reverse=True)
        
        # Assign ranks
        recommendations = []
        for i, item in enumerate(scored[:limit], 1):
            item.rank = i
            recommendations.append(item)
        
        logger.info("Recommendations generated", count=len(recommendations))
        return recommendations
    
    async def _get_candidates(
        self,
        category: str,
        budget: Optional[int],
    ) -> list[dict]:
        """Get candidate products for recommendation."""
        # Mock implementation - would query database
        category_products = {
            "smartphone": [
                {"id": "samsung-galaxy-s24-ultra"},
                {"id": "iphone-16-pro"},
                {"id": "google-pixel-9-pro"},
                {"id": "xiaomi-14-ultra"},
                {"id": "oneplus-12"},
            ],
            "laptop": [
                {"id": "macbook-pro-16"},
                {"id": "asus-rog-zephyrus"},
                {"id": "dell-xps-15"},
                {"id": "lenovo-thinkpad-x1"},
                {"id": "hp-spectre-x360"},
            ],
            "tablet": [
                {"id": "ipad-pro-13"},
                {"id": "samsung-galaxy-tab-s9"},
                {"id": "ipad-air"},
            ],
            "phone": [  # Alias for smartphone
                {"id": "samsung-galaxy-s24-ultra"},
                {"id": "iphone-16-pro"},
                {"id": "google-pixel-9-pro"},
            ],
        }
        
        return category_products.get(category.lower(), category_products["smartphone"])
    
    def _generate_why(
        self,
        intel,
        context: str,
        budget: Optional[int],
    ) -> str:
        """Generate explanation for why this product is recommended."""
        reasons = []
        
        # Context-specific reasons
        context_reasons = {
            "gaming": [
                ("chipset_tier", "flagship", "En güçlü işlemciye sahip"),
                ("chipset_tier", "upper_mid", "Güçlü oyun performansı"),
            ],
            "photography": [
                ("camera_mp", 200, "200MP kamera ile en iyi çekim kalitesi"),
                ("camera_mp", 108, "108MP profesyonel kamera"),
                ("camera_mp", 50, "Yüksek çözünürlüklü kamera"),
            ],
            "student": [
                ("budget_score", 0.7, "Uygun fiyat/performans oranı"),
                ("battery_mah", 5000, "Uzun batarya ömrü"),
            ],
            "business": [
                ("chipset_tier", "flagship", "Profesyonel performans"),
            ],
            "budget": [
                ("budget_score", 0.8, "En iyi fiyat/performans"),
            ],
            "long_term": [
                ("chipset_tier", "flagship", "Uzun süre güncel kalacak"),
            ],
            "creator": [
                ("camera_mp", 50, "Yüksek kaliteli içerik üretimi için ideal"),
            ],
        }
        
        # Check for matching reasons
        for attr, threshold, reason in context_reasons.get(context, []):
            if hasattr(intel.specs, attr):
                value = getattr(intel.specs, attr)
                if isinstance(threshold, (int, float)):
                    if value and value >= threshold:
                        reasons.append(reason)
                        break
                elif value == threshold:
                    reasons.append(reason)
                    break
        
        # Default reasons based on context scores
        if not reasons:
            score = getattr(intel.context_scores, context, 0.5)
            if score >= 0.8:
                reasons.append(f"{context.title()} için mükemmel uyum")
            elif score >= 0.6:
                reasons.append(f"{context.title()} için iyi seçenek")
            else:
                reasons.append("Dengeli performans")
        
        # Add budget reason if applicable
        if budget and intel.pricing:
            if intel.pricing.average <= budget:
                price_margin = (budget - intel.pricing.average) / budget * 100
                if price_margin > 20:
                    reasons.append("bütçenin altında kalıyor")
        
        return reasons[0] if reasons else "Genel kullanım için uygun"
    
    async def get_similar_products(
        self,
        product_id: str,
        limit: int = 5,
    ) -> list[RecommendedProduct]:
        """Get similar products to a given product."""
        # Get the base product
        base_intel = await self.pie.analyze_product(product_id)
        
        # Find products with similar context scores
        # This is a simplified implementation
        candidates = await self._get_candidates(base_intel.category, None)
        
        similar = []
        for candidate in candidates:
            if candidate["id"] == product_id:
                continue
            
            intel = await self.pie.analyze_product(candidate["id"])
            
            # Calculate similarity based on context scores
            similarity = self._calculate_similarity(base_intel, intel)
            
            similar.append(RecommendedProduct(
                rank=0,
                product_id=intel.product_id,
                name=intel.name,
                price=intel.pricing.average if intel.pricing else 0,
                fit_score=round(similarity, 2),
                why=f"{base_intel.name} ile benzer özellikler",
            ))
        
        similar.sort(key=lambda x: x.fit_score, reverse=True)
        
        for i, item in enumerate(similar[:limit], 1):
            item.rank = i
        
        return similar[:limit]
    
    def _calculate_similarity(self, base, candidate) -> float:
        """Calculate similarity between two products."""
        # Compare context scores
        contexts = ["gaming", "photography", "student", "business", "budget", "long_term", "creator"]
        
        total_diff = 0
        for ctx in contexts:
            base_score = getattr(base.context_scores, ctx, 0.5)
            cand_score = getattr(candidate.context_scores, ctx, 0.5)
            total_diff += abs(base_score - cand_score)
        
        # Convert to similarity (0-1)
        avg_diff = total_diff / len(contexts)
        similarity = 1 - avg_diff
        
        return similarity
