"""
Commerce Signal Engine (CSE)
Canlı ticari veriyi izleyip proprietary market sinyalleri üreten motor.
"""
from typing import Optional
import structlog
from datetime import datetime

from src.models.product import (
    CommerceSignals,
    FakeDiscountSignal,
    StoreReliabilitySignal,
    PriceVolatilitySignal,
    LifecycleSignal,
    SupplyRiskSignal,
)
from src.cse.fake_discount_detector import FakeDiscountDetector
from src.cse.store_reliability import StoreReliabilityScorer
from src.cse.price_volatility import PriceVolatilityAnalyzer
from src.cse.lifecycle_scorer import LifecycleScorer

logger = structlog.get_logger()


class CommerceSignalEngine:
    """
    Main CSE orchestrator.
    
    Generates commerce signals:
    - Fake discount detection
    - Store reliability scoring
    - Price volatility analysis
    - Product lifecycle stage
    - Supply risk assessment
    """
    
    def __init__(self):
        self.fake_discount = FakeDiscountDetector()
        self.store_reliability = StoreReliabilityScorer()
        self.price_volatility = PriceVolatilityAnalyzer()
        self.lifecycle = LifecycleScorer()
    
    async def analyze_product(
        self,
        product_id: str,
        seller_id: Optional[str] = None,
    ) -> CommerceSignals:
        """
        Analyze a product and generate commerce signals.
        
        Args:
            product_id: Product identifier
            seller_id: Optional specific seller
            
        Returns:
            CommerceSignals with all signal data
        """
        logger.info("Generating commerce signals", product_id=product_id, seller_id=seller_id)
        
        # Get mock data (would connect to real data sources)
        product_data = await self._fetch_product_data(product_id)
        price_history = await self._fetch_price_history(product_id)
        store_data = await self._fetch_store_data(seller_id) if seller_id else None
        
        # Generate individual signals
        fake_discount_signal = self.fake_discount.detect(
            current_price=product_data.get("current_price", 0),
            claimed_old_price=product_data.get("claimed_old_price"),
            price_history=price_history,
        )
        
        store_signal = self.store_reliability.score(store_data) if store_data else StoreReliabilitySignal()
        
        volatility_signal = self.price_volatility.analyze(price_history)
        
        lifecycle_signal = self.lifecycle.determine_stage(product_data)
        
        supply_signal = await self._assess_supply_risk(product_id)
        
        # Calculate composite scores
        buy_safety = self._calculate_buy_safety(fake_discount_signal, store_signal, supply_signal)
        value_score = self._calculate_value_score(volatility_signal, lifecycle_signal)
        timing_score = self._calculate_timing_score(volatility_signal, lifecycle_signal)
        
        # Determine overall recommendation
        overall = self._determine_overall(buy_safety, value_score, timing_score)
        
        signals = CommerceSignals(
            product_id=product_id,
            seller_id=seller_id,
            generated_at=datetime.utcnow(),
            
            fake_discount=fake_discount_signal,
            store_reliability=store_signal,
            price_volatility=volatility_signal,
            lifecycle=lifecycle_signal,
            supply_risk=supply_signal,
            
            buy_safety=buy_safety,
            value_score=value_score,
            timing_score=timing_score,
            overall=overall,
        )
        
        logger.info("Signals generated", product_id=product_id, overall=overall)
        return signals
    
    async def get_market_trends(self, category: str, period: int) -> dict:
        """Get market trends for a category."""
        # Mock implementation
        return {
            "price_trend": {
                "direction": "declining",
                "avg_change_percent": -3.2,
                "period_days": period,
            },
            "popular_products": [
                {"id": "samsung-galaxy-s24-ultra", "name": "Samsung Galaxy S24 Ultra"},
                {"id": "iphone-16-pro", "name": "iPhone 16 Pro"},
            ],
            "supply_situation": "normal",
            "upcoming_releases": [
                {"name": "Samsung Galaxy S25", "expected": "Q1 2025"},
            ],
        }
    
    async def get_category_signals(self, category: str, limit: int) -> list[dict]:
        """Get signals for all products in a category."""
        # Mock implementation
        return [
            {
                "product_id": "samsung-galaxy-s24-ultra",
                "fake_discount_score": 15,
                "store_reliability_score": 85,
                "overall": "safe",
            },
            {
                "product_id": "iphone-16-pro",
                "fake_discount_score": 8,
                "store_reliability_score": 92,
                "overall": "safe",
            },
        ][:limit]
    
    def _calculate_buy_safety(
        self,
        fake_discount: FakeDiscountSignal,
        store: StoreReliabilitySignal,
        supply: SupplyRiskSignal,
    ) -> int:
        """Calculate overall buy safety score."""
        # Start with base score
        score = 70
        
        # Deduct for fake discount risk
        if fake_discount.is_fake:
            score -= 30
        elif fake_discount.score > 50:
            score -= 15
        
        # Add for trusted store
        if store.tier == "trusted":
            score += 15
        elif store.tier == "caution":
            score -= 10
        elif store.tier == "avoid":
            score -= 25
        
        # Deduct for supply risk
        if supply.level == "high":
            score -= 10
        elif supply.level == "critical":
            score -= 20
        
        return max(min(score, 100), 0)
    
    def _calculate_value_score(
        self,
        volatility: PriceVolatilitySignal,
        lifecycle: LifecycleSignal,
    ) -> int:
        """Calculate value score based on price and lifecycle."""
        score = 50
        
        # Better value if price is declining
        if volatility.trend == "declining":
            score += 20
        elif volatility.trend == "rising":
            score -= 10
        
        # Lifecycle affects value
        if lifecycle.stage == "decline":
            score += 15  # Good value, new model coming
        elif lifecycle.stage == "clearance":
            score += 25  # Best value
        elif lifecycle.stage == "launch":
            score -= 15  # Premium pricing
        
        return max(min(score, 100), 0)
    
    def _calculate_timing_score(
        self,
        volatility: PriceVolatilitySignal,
        lifecycle: LifecycleSignal,
    ) -> int:
        """Calculate timing score - is now a good time to buy?"""
        score = 50
        
        if volatility.recommendation == "buy_now":
            score += 25
        elif volatility.recommendation == "wait":
            score -= 15
        
        if lifecycle.stage == "mature":
            score += 15
        elif lifecycle.stage == "launch":
            score -= 10
        
        if volatility.stability == "stable":
            score += 10
        
        return max(min(score, 100), 0)
    
    def _determine_overall(self, buy_safety: int, value: int, timing: int) -> str:
        """Determine overall recommendation."""
        avg = (buy_safety + value + timing) / 3
        
        if avg >= 70:
            return "safe"
        elif avg >= 50:
            return "proceed_with_caution"
        else:
            return "avoid"
    
    async def _fetch_product_data(self, product_id: str) -> dict:
        """Fetch product data (mock)."""
        return {
            "current_price": 85000,
            "claimed_old_price": 95000,
            "release_date": "2024-01-01",
            "active_sellers": 47,
        }
    
    async def _fetch_price_history(self, product_id: str) -> list[dict]:
        """Fetch price history (mock)."""
        # Generate mock 90-day history
        import random
        base_price = 85000
        history = []
        
        for i in range(90):
            variation = random.randint(-3000, 3000)
            history.append({
                "date": f"2024-{(i // 30) + 1:02d}-{(i % 30) + 1:02d}",
                "price": base_price + variation,
            })
        
        return history
    
    async def _fetch_store_data(self, seller_id: str) -> dict:
        """Fetch store data (mock)."""
        return {
            "seller_id": seller_id,
            "reviews": 4532,
            "avg_rating": 4.2,
            "fulfillment_rate": 0.94,
            "refund_rate": 0.03,
            "response_time_hours": 2,
            "age_months": 48,
        }
    
    async def _assess_supply_risk(self, product_id: str) -> SupplyRiskSignal:
        """Assess supply risk (mock)."""
        return SupplyRiskSignal(
            level="low",
            active_sellers=47,
            stock_status="abundant",
            alerts=[],
            confidence=0.9,
        )
