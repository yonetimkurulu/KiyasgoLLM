"""
Store Reliability Scorer
Satıcı güvenilirliğini ölçer.
"""
from typing import Optional
from src.models.product import StoreReliabilitySignal


class StoreReliabilityScorer:
    """
    Score store/seller reliability.
    
    Factors:
    - User reviews & ratings
    - Order fulfillment rate
    - Refund/return rate
    - Response time
    - Store age & history
    """
    
    def score(self, store_data: Optional[dict]) -> StoreReliabilitySignal:
        """
        Calculate store reliability score.
        
        Args:
            store_data: Store metrics dictionary
            
        Returns:
            StoreReliabilitySignal with score and breakdown
        """
        if not store_data:
            return StoreReliabilitySignal()
        
        # Calculate component scores
        review_score = self._score_reviews(
            store_data.get("reviews", 0),
            store_data.get("avg_rating", 0),
        )
        
        fulfillment_score = self._score_fulfillment(
            store_data.get("fulfillment_rate", 0),
        )
        
        refund_score = self._score_refund_rate(
            store_data.get("refund_rate", 0),
        )
        
        response_score = self._score_response_time(
            store_data.get("response_time_hours", 24),
        )
        
        age_bonus = self._calculate_age_bonus(
            store_data.get("age_months", 0),
        )
        
        # Weighted average
        total_score = int(
            review_score * 0.30 +
            fulfillment_score * 0.25 +
            refund_score * 0.20 +
            response_score * 0.15 +
            age_bonus * 0.10
        )
        
        # Determine tier
        tier = self._determine_tier(total_score)
        
        # Detect red flags
        red_flags = self._detect_red_flags(store_data)
        
        return StoreReliabilitySignal(
            score=total_score,
            tier=tier,
            breakdown={
                "reviews": review_score,
                "fulfillment": fulfillment_score,
                "refunds": refund_score,
                "response": response_score,
                "age_bonus": age_bonus,
            },
            red_flags=red_flags,
            confidence=0.88,
        )
    
    def _score_reviews(self, count: int, avg_rating: float) -> int:
        """Score based on reviews."""
        score = 50
        
        # Rating contribution (max 40 points)
        if avg_rating >= 4.5:
            score += 40
        elif avg_rating >= 4.0:
            score += 30
        elif avg_rating >= 3.5:
            score += 20
        elif avg_rating >= 3.0:
            score += 10
        else:
            score -= 10
        
        # Count contribution (max 10 points)
        if count >= 1000:
            score += 10
        elif count >= 500:
            score += 7
        elif count >= 100:
            score += 5
        elif count < 20:
            score -= 5
        
        return max(min(score, 100), 0)
    
    def _score_fulfillment(self, rate: float) -> int:
        """Score based on order fulfillment rate."""
        if rate >= 0.98:
            return 100
        elif rate >= 0.95:
            return 90
        elif rate >= 0.90:
            return 75
        elif rate >= 0.85:
            return 60
        elif rate >= 0.80:
            return 45
        else:
            return 30
    
    def _score_refund_rate(self, rate: float) -> int:
        """Score based on refund rate (lower is better)."""
        if rate <= 0.01:
            return 100
        elif rate <= 0.03:
            return 90
        elif rate <= 0.05:
            return 75
        elif rate <= 0.08:
            return 60
        elif rate <= 0.10:
            return 45
        else:
            return 30
    
    def _score_response_time(self, hours: float) -> int:
        """Score based on response time."""
        if hours <= 1:
            return 100
        elif hours <= 4:
            return 90
        elif hours <= 12:
            return 75
        elif hours <= 24:
            return 60
        elif hours <= 48:
            return 40
        else:
            return 20
    
    def _calculate_age_bonus(self, months: int) -> int:
        """Calculate bonus based on store age."""
        if months >= 60:  # 5+ years
            return 100
        elif months >= 36:  # 3+ years
            return 80
        elif months >= 24:  # 2+ years
            return 60
        elif months >= 12:  # 1+ year
            return 40
        elif months >= 6:
            return 20
        else:
            return 0
    
    def _determine_tier(self, score: int) -> str:
        """Determine reliability tier from score."""
        if score >= 80:
            return "trusted"
        elif score >= 60:
            return "standard"
        elif score >= 40:
            return "caution"
        else:
            return "avoid"
    
    def _detect_red_flags(self, store_data: dict) -> list[str]:
        """Detect red flags in store data."""
        flags = []
        
        if store_data.get("avg_rating", 5) < 3.5:
            flags.append("Düşük müşteri puanı")
        
        if store_data.get("refund_rate", 0) > 0.10:
            flags.append("Yüksek iade oranı")
        
        if store_data.get("age_months", 0) < 6:
            flags.append("Yeni satıcı")
        
        if store_data.get("fulfillment_rate", 1) < 0.85:
            flags.append("Düşük sipariş tamamlama oranı")
        
        return flags
