"""
Decision Synthesizer Service
Tüm sinyalleri birleştirerek final karar özetini üretir.
"""
from typing import Optional
from src.models.product import ProductSpecs, UsageContextScores
from src.llm import LLMProvider


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
        best_for = self._determine_best_for(context_scores)
        avoid_for = self._determine_avoid_for(context_scores)
        
        # Generate who should buy/avoid
        who_should_buy = self._generate_who_should_buy(specs, context_scores, best_for)
        who_should_avoid = self._generate_who_should_avoid(specs, context_scores, avoid_for, price_info)
        
        # Extract strengths and weaknesses
        key_strengths = self._extract_strengths(specs, context_scores)
        key_weaknesses = self._extract_weaknesses(specs, price_info)
        
        # Calculate verdict score
        verdict_score = self._calculate_verdict_score(specs, context_scores, price_info)
        
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
            "verdict_text": verdict_text,
        }
    
    def _determine_best_for(self, scores: UsageContextScores) -> list[str]:
        """Determine which contexts the product is best for."""
        context_dict = {
            "gaming": scores.gaming,
            "photography": scores.photography,
            "student": scores.student,
            "business": scores.business,
            "budget": scores.budget,
            "long_term": scores.long_term,
            "creator": scores.creator,
        }
        
        # Filter contexts with score > 0.7
        best = [ctx for ctx, score in context_dict.items() if score >= 0.7]
        
        # Sort by score
        best.sort(key=lambda x: context_dict[x], reverse=True)
        
        return best[:3]  # Top 3
    
    def _determine_avoid_for(self, scores: UsageContextScores) -> list[str]:
        """Determine which contexts the product should be avoided for."""
        context_dict = {
            "gaming": scores.gaming,
            "photography": scores.photography,
            "student": scores.student,
            "business": scores.business,
            "budget": scores.budget,
            "long_term": scores.long_term,
            "creator": scores.creator,
        }
        
        # Filter contexts with score < 0.4
        avoid = [ctx for ctx, score in context_dict.items() if score < 0.4]
        
        return avoid[:3]
    
    def _generate_who_should_buy(
        self,
        specs: ProductSpecs,
        scores: UsageContextScores,
        best_for: list[str],
    ) -> list[str]:
        """Generate who should buy recommendations."""
        recommendations = []
        
        if "photography" in best_for:
            recommendations.append("Mobil fotoğrafçılık tutkunları")
        
        if "gaming" in best_for:
            recommendations.append("Mobil oyun tutkunları")
        
        if "long_term" in best_for:
            recommendations.append("Uzun vadeli kullanım isteyenler")
        
        if "business" in best_for:
            recommendations.append("İş amacıyla kullananlar")
        
        if "creator" in best_for:
            recommendations.append("İçerik üreticileri")
        
        if specs.chipset_tier == "flagship":
            recommendations.append("Premium deneyim arayanlar")
        
        # Deduplicate and limit
        seen = set()
        unique = []
        for r in recommendations:
            if r not in seen:
                seen.add(r)
                unique.append(r)
        
        return unique[:4]
    
    def _generate_who_should_avoid(
        self,
        specs: ProductSpecs,
        scores: UsageContextScores,
        avoid_for: list[str],
        price_info: Optional[dict],
    ) -> list[str]:
        """Generate who should avoid recommendations."""
        recommendations = []
        
        if "budget" in avoid_for:
            recommendations.append("Bütçe bilincli alıcılar")
        
        if "student" in avoid_for:
            recommendations.append("Öğrenciler")
        
        if specs.weight_grams and specs.weight_grams > 220:
            recommendations.append("Kompakt telefon arayanlar")
        
        if price_info and price_info.get("average", 0) > 80000:
            recommendations.append("Uygun fiyat arayanlar")
        
        if "gaming" in avoid_for:
            recommendations.append("Ağır oyun oynayan kullanıcılar")
        
        return recommendations[:4]
    
    def _extract_strengths(self, specs: ProductSpecs, scores: UsageContextScores) -> list[dict]:
        """Extract key strengths from specs."""
        strengths = []
        
        if specs.camera_mp and specs.camera_mp >= 108:
            strengths.append({
                "point": f"{specs.camera_mp}MP ana kamera",
                "impact": "high"
            })
        
        if specs.chipset_tier == "flagship":
            strengths.append({
                "point": "Flagship işlemci",
                "impact": "high"
            })
        
        if specs.battery_mah and specs.battery_mah >= 5000:
            strengths.append({
                "point": f"{specs.battery_mah}mAh büyük batarya",
                "impact": "medium"
            })
        
        if specs.screen_type in ["AMOLED", "SUPER_AMOLED"]:
            strengths.append({
                "point": f"{specs.screen_type} ekran",
                "impact": "medium"
            })
        
        if specs.ram_gb and specs.ram_gb >= 12:
            strengths.append({
                "point": f"{specs.ram_gb}GB yüksek RAM",
                "impact": "medium"
            })
        
        return strengths[:5]
    
    def _extract_weaknesses(self, specs: ProductSpecs, price_info: Optional[dict]) -> list[dict]:
        """Extract key weaknesses from specs."""
        weaknesses = []
        
        if specs.weight_grams and specs.weight_grams > 220:
            weaknesses.append({
                "point": f"Ağır ({specs.weight_grams}g)",
                "impact": "medium"
            })
        
        if price_info and price_info.get("average", 0) > 70000:
            weaknesses.append({
                "point": "Yüksek fiyat",
                "impact": "high"
            })
        
        if specs.battery_mah and specs.battery_mah < 4000:
            weaknesses.append({
                "point": "Küçük batarya",
                "impact": "medium"
            })
        
        if specs.storage_gb and specs.storage_gb < 128:
            weaknesses.append({
                "point": "Sınırlı depolama",
                "impact": "medium"
            })
        
        return weaknesses[:4]
    
    def _calculate_verdict_score(
        self,
        specs: ProductSpecs,
        scores: UsageContextScores,
        price_info: Optional[dict],
    ) -> float:
        """Calculate overall verdict score (0-10)."""
        base_score = 5.0
        
        # Add based on chipset
        if specs.chipset_tier == "flagship":
            base_score += 1.5
        elif specs.chipset_tier == "upper_mid":
            base_score += 0.8
        
        # Add based on camera
        if specs.camera_mp and specs.camera_mp >= 108:
            base_score += 0.7
        elif specs.camera_mp and specs.camera_mp >= 50:
            base_score += 0.3
        
        # Add based on display
        if specs.screen_type in ["AMOLED", "SUPER_AMOLED"]:
            base_score += 0.5
        
        # Subtract based on price (if expensive)
        if price_info:
            avg_price = price_info.get("average", 0)
            if avg_price > 90000:
                base_score -= 0.5
            elif avg_price > 70000:
                base_score -= 0.2
        
        # Context diversity bonus
        best_contexts = sum(1 for v in [
            scores.gaming, scores.photography, scores.business,
            scores.creator, scores.long_term
        ] if v >= 0.7)
        
        base_score += best_contexts * 0.2
        
        return round(min(max(base_score, 1.0), 10.0), 1)
    
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
