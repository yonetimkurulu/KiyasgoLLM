"""
Usage Inference Service
Ürünün hangi kullanım senaryolarına uygun olduğunu belirler.
"""
from src.models.product import ProductSpecs, UsageContextScores
from src.config import get_settings


class UsageInferenceService:
    """
    Infer usage context fit scores based on specs and price.
    
    Contexts:
    - gaming: GPU tier, refresh rate, cooling
    - photography: Camera specs, OIS, sensor size
    - student: Price, battery, portability
    - business: Build quality, security, durability
    - budget: Price/performance ratio
    - long_term: Update policy, repairability
    - creator: Display accuracy, performance, ports
    """
    
    def __init__(self):
        self._settings = None

    @property
    def settings(self):
        """Lazy-load settings to avoid import-time side effects."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings
    
    def infer_contexts(self, specs: ProductSpecs, price: int) -> UsageContextScores:
        """
        Infer context scores from specs and price.
        
        Args:
            specs: Normalized product specifications
            price: Current average price in TRY
            
        Returns:
            UsageContextScores with fit scores for each context
        """
        scores = UsageContextScores()
        
        # Gaming score
        scores.gaming = self._calculate_gaming_score(specs)
        
        # Photography score
        scores.photography = self._calculate_photography_score(specs)
        
        # Student score
        scores.student = self._calculate_student_score(specs, price)
        
        # Business score
        scores.business = self._calculate_business_score(specs)
        
        # Budget score
        scores.budget = self._calculate_budget_score(specs, price)
        
        # Long-term score
        scores.long_term = self._calculate_long_term_score(specs)
        
        # Creator score
        scores.creator = self._calculate_creator_score(specs)
        
        return scores
    
    def _calculate_gaming_score(self, specs: ProductSpecs) -> float:
        """Calculate gaming fitness score."""
        score = 0.5
        
        # Chipset tier is most important
        if specs.chipset_tier == "flagship":
            score += 0.3
        elif specs.chipset_tier == "upper_mid":
            score += 0.15
        
        # RAM matters
        if specs.ram_gb:
            if specs.ram_gb >= 12:
                score += 0.1
            elif specs.ram_gb >= 8:
                score += 0.05
        
        # Battery for long gaming sessions
        if specs.battery_mah:
            if specs.battery_mah >= 5000:
                score += 0.05
        
        # Screen type for visuals
        if specs.screen_type in ["AMOLED", "SUPER_AMOLED"]:
            score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_photography_score(self, specs: ProductSpecs) -> float:
        """Calculate photography fitness score."""
        score = 0.5
        
        # Camera is critical
        if specs.camera_mp:
            if specs.camera_mp >= 200:
                score += 0.3
            elif specs.camera_mp >= 108:
                score += 0.2
            elif specs.camera_mp >= 50:
                score += 0.1
        
        # Good display for reviewing photos
        if specs.screen_type in ["AMOLED", "SUPER_AMOLED", "OLED"]:
            score += 0.1
        
        # Storage for photos
        if specs.storage_gb:
            if specs.storage_gb >= 256:
                score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_student_score(self, specs: ProductSpecs, price: int) -> float:
        """Calculate student fitness score."""
        score = 0.5
        
        # Price is crucial for students
        if price:
            if price < 15000:
                score += 0.3
            elif price < 25000:
                score += 0.2
            elif price < 40000:
                score += 0.1
            elif price > 60000:
                score -= 0.2
        
        # Battery for all-day use
        if specs.battery_mah:
            if specs.battery_mah >= 5000:
                score += 0.1
            elif specs.battery_mah >= 4500:
                score += 0.05
        
        # Portability (lighter is better)
        if specs.weight_grams:
            if specs.weight_grams < 180:
                score += 0.1
            elif specs.weight_grams > 220:
                score -= 0.05
        
        return max(min(score, 1.0), 0.1)
    
    def _calculate_business_score(self, specs: ProductSpecs) -> float:
        """Calculate business fitness score."""
        score = 0.5
        
        # Flagship chips = reliable
        if specs.chipset_tier == "flagship":
            score += 0.2
        
        # Good storage for work files
        if specs.storage_gb:
            if specs.storage_gb >= 256:
                score += 0.1
        
        # Reasonable weight for portability
        if specs.weight_grams:
            if specs.weight_grams < 200:
                score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_budget_score(self, specs: ProductSpecs, price: int) -> float:
        """Calculate budget fitness score (price/performance)."""
        score = 0.5
        
        if not price:
            return score
        
        # Lower price = higher budget score
        if price < 10000:
            score += 0.4
        elif price < 20000:
            score += 0.3
        elif price < 30000:
            score += 0.2
        elif price < 50000:
            score += 0.1
        elif price > 70000:
            score -= 0.3
        
        # Bonus for good specs at low price
        if specs.chipset_tier in ["flagship", "upper_mid"] and price < 40000:
            score += 0.1
        
        return max(min(score, 1.0), 0.1)
    
    def _calculate_long_term_score(self, specs: ProductSpecs) -> float:
        """Calculate long-term usage fitness score."""
        score = 0.5
        
        # Flagship chips get longer support
        if specs.chipset_tier == "flagship":
            score += 0.25
        elif specs.chipset_tier == "upper_mid":
            score += 0.1
        
        # More RAM = longer useful life
        if specs.ram_gb:
            if specs.ram_gb >= 12:
                score += 0.1
            elif specs.ram_gb >= 8:
                score += 0.05
        
        # More storage = future-proof
        if specs.storage_gb:
            if specs.storage_gb >= 256:
                score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_creator_score(self, specs: ProductSpecs) -> float:
        """Calculate content creator fitness score."""
        score = 0.5
        
        # High-res camera for content
        if specs.camera_mp:
            if specs.camera_mp >= 108:
                score += 0.2
            elif specs.camera_mp >= 50:
                score += 0.1
        
        # OLED display for color accuracy
        if specs.screen_type in ["AMOLED", "SUPER_AMOLED", "OLED"]:
            score += 0.1
        
        # Storage for media files
        if specs.storage_gb:
            if specs.storage_gb >= 256:
                score += 0.1
        
        # Powerful chipset for editing
        if specs.chipset_tier == "flagship":
            score += 0.1
        
        return min(score, 1.0)
