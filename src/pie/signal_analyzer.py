"""
Signal Analyzer
Handles mathematical and rule-based analysis of product signals.
Extracted from DecisionSynthesizer to reduce complexity.
"""
from typing import Optional
from src.models.product import ProductSpecs, UsageContextScores
from src.config import get_settings

settings = get_settings()

class SignalAnalyzer:
    """Analyzes product signals based on configuration rules."""

    def determine_best_for(self, scores: UsageContextScores) -> list[str]:
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
        
        # Filter contexts with score > threshold
        best = [ctx for ctx, score in context_dict.items() if score >= settings.score_threshold_best]
        # Sort by score
        best.sort(key=lambda x: context_dict[x], reverse=True)
        return best[:3]

    def determine_avoid_for(self, scores: UsageContextScores) -> list[str]:
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
        
        # Filter contexts with score < threshold
        avoid = [ctx for ctx, score in context_dict.items() if score < settings.score_threshold_avoid]
        return avoid[:3]

    def generate_who_should_buy(
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

    def generate_who_should_avoid(
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
        
        if specs.weight_grams and specs.weight_grams > settings.weight_heavy:
            recommendations.append("Kompakt telefon arayanlar")
        
        if price_info and price_info.get("average", 0) > settings.price_medium_threshold:
            recommendations.append("Uygun fiyat arayanlar")
        
        if "gaming" in avoid_for:
            recommendations.append("Ağır oyun oynayan kullanıcılar")
        
        return recommendations[:4]

    def calculate_verdict_score(
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
        if specs.camera_mp and specs.camera_mp >= settings.camera_mp_high:
            base_score += 0.7
        elif specs.camera_mp and specs.camera_mp >= settings.camera_mp_mid:
            base_score += 0.3
        
        # Add based on display
        if specs.screen_type in ["AMOLED", "SUPER_AMOLED"]:
            base_score += 0.5
        
        # Subtract based on price (if expensive)
        if price_info:
            avg_price = price_info.get("average", 0)
            if avg_price > settings.price_high_threshold:
                base_score -= 0.5
            elif avg_price > settings.price_medium_threshold:
                base_score -= 0.2
        
        # Context diversity bonus
        best_contexts = sum(1 for v in [
            scores.gaming, scores.photography, scores.business,
            scores.creator, scores.long_term
        ] if v >= settings.score_threshold_best)
        
        base_score += best_contexts * 0.2
        
        return round(min(max(base_score, 1.0), 10.0), 1)

    def extract_strengths(self, specs: ProductSpecs, scores: UsageContextScores) -> list[dict]:
        """Extract key strengths from specs."""
        strengths = []
        
        if specs.camera_mp and specs.camera_mp >= settings.camera_mp_high:
            strengths.append({"point": f"{specs.camera_mp}MP ana kamera", "impact": "high"})
        
        if specs.chipset_tier == "flagship":
            strengths.append({"point": "Flagship işlemci", "impact": "high"})
        
        if specs.battery_mah and specs.battery_mah >= settings.battery_mah_large:
            strengths.append({"point": f"{specs.battery_mah}mAh büyük batarya", "impact": "medium"})
        
        if specs.screen_type in ["AMOLED", "SUPER_AMOLED"]:
            strengths.append({"point": f"{specs.screen_type} ekran", "impact": "medium"})
        
        if specs.ram_gb and specs.ram_gb >= 12:
            strengths.append({"point": f"{specs.ram_gb}GB yüksek RAM", "impact": "medium"})
        
        return strengths[:5]

    def extract_weaknesses(self, specs: ProductSpecs, price_info: Optional[dict]) -> list[dict]:
        """Extract key weaknesses from specs."""
        weaknesses = []
        
        if specs.weight_grams and specs.weight_grams > settings.weight_heavy:
            weaknesses.append({"point": f"Ağır ({specs.weight_grams}g)", "impact": "medium"})
        
        if price_info and price_info.get("average", 0) > settings.price_medium_threshold:
            weaknesses.append({"point": "Yüksek fiyat", "impact": "high"})
        
        if specs.battery_mah and specs.battery_mah < settings.battery_mah_small:
            weaknesses.append({"point": "Küçük batarya", "impact": "medium"})
        
        if specs.storage_gb and specs.storage_gb < settings.storage_min:
            weaknesses.append({"point": "Sınırlı depolama", "impact": "medium"})
        
        return weaknesses[:4]
