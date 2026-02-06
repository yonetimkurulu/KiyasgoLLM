"""
Fake Discount Detector
Sahte indirim taktiklerini tespit eder.
"""
from typing import Optional
from src.models.product import FakeDiscountSignal


class FakeDiscountDetector:
    """
    Detect fake discount tactics.
    
    Checks:
    - Reference price inflation (vs 90-day average)
    - Historical low comparison
    - Cross-seller price anomalies
    - Pre-campaign price spikes
    """
    
    def detect(
        self,
        current_price: int,
        claimed_old_price: Optional[int],
        price_history: list[dict],
    ) -> FakeDiscountSignal:
        """
        Detect if a discount is fake.
        
        Args:
            current_price: Current selling price
            claimed_old_price: Claimed "original" price
            price_history: List of {date, price} dicts
            
        Returns:
            FakeDiscountSignal with detection results
        """
        if not claimed_old_price or claimed_old_price <= current_price:
            return FakeDiscountSignal(
                score=0,
                is_fake=False,
                confidence=0.95,
            )
        
        # Calculate real discount
        claimed_discount = int((claimed_old_price - current_price) / claimed_old_price * 100)
        
        # Get 90-day average price
        avg_price = self._calculate_average(price_history)
        
        # Calculate real discount based on average
        real_discount = int((avg_price - current_price) / avg_price * 100) if avg_price > current_price else 0
        
        # Check reference price inflation
        reference_inflation = self._check_reference_inflation(claimed_old_price, avg_price)
        
        # Check if current is actually a historical low
        historical_low = self._get_historical_low(price_history)
        is_real_low = current_price <= historical_low * 1.05  # Within 5% of lowest
        
        # Check for pre-campaign spike
        pre_campaign_spike = self._detect_pre_campaign_spike(price_history)
        
        # Calculate risk score
        risk_score = 0
        evidence = []
        
        if reference_inflation > 0.3:  # >30% inflation
            risk_score += 35
            evidence.append(f"Referans fiyat ortalamadan %{int(reference_inflation*100)} yüksek")
        
        if not is_real_low:
            risk_score += 25
            evidence.append("Mevcut fiyat tarihi en düşük değil")
        
        if pre_campaign_spike:
            risk_score += 25
            evidence.append("Kampanya öncesi fiyat artışı tespit edildi")
        
        if claimed_discount > 50 and real_discount < 15:
            risk_score += 15
            evidence.append("İddia edilen indirim gerçeği yansıtmıyor")
        
        return FakeDiscountSignal(
            score=min(risk_score, 100),
            is_fake=risk_score > 50,
            claimed_discount=claimed_discount,
            real_discount=max(real_discount, 0),
            evidence=evidence,
            confidence=0.85,
        )
    
    def _calculate_average(self, price_history: list[dict]) -> float:
        """Calculate average price from history."""
        if not price_history:
            return 0
        
        prices = [p.get("price", 0) for p in price_history]
        return sum(prices) / len(prices) if prices else 0
    
    def _check_reference_inflation(self, claimed_old: int, avg_price: float) -> float:
        """Check if claimed old price is inflated vs average."""
        if avg_price <= 0:
            return 0
        
        return (claimed_old - avg_price) / avg_price
    
    def _get_historical_low(self, price_history: list[dict]) -> int:
        """Get the lowest price in history."""
        if not price_history:
            return 0
        
        prices = [p.get("price", float("inf")) for p in price_history]
        return min(prices) if prices else 0
    
    def _detect_pre_campaign_spike(self, price_history: list[dict]) -> bool:
        """
        Detect if there was a price spike before campaigns.
        
        Checks for:
        - Black Friday (November)
        - 11.11 (November 11)
        - New Year sales
        """
        if len(price_history) < 30:
            return False
        
        # Simple check: compare last 7 days vs previous 7 days
        recent_prices = [p.get("price", 0) for p in price_history[-7:]]
        previous_prices = [p.get("price", 0) for p in price_history[-14:-7]]
        
        if not recent_prices or not previous_prices:
            return False
        
        recent_avg = sum(recent_prices) / len(recent_prices)
        previous_avg = sum(previous_prices) / len(previous_prices)
        
        # If price dropped more than 15% in last 7 days after spike
        if previous_avg > recent_avg * 1.15:
            return True
        
        return False
