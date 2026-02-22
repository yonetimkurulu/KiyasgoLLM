"""
Commerce Signal Engine (CSE)
Canli ticari veriyi izleyip proprietary market sinyalleri ureten motor.

Database-backed: Tries repository first, falls back to mock if DB is empty.
"""
from typing import Optional
import structlog
import random
from datetime import datetime, timezone

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
from src.db.session import SessionLocal
from src.db.repository import ProductRepository, PriceRepository, StoreRepository

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
    
    def _get_session(self):
        return SessionLocal()

    async def analyze_product(
        self,
        product_id: str,
        seller_id: Optional[str] = None,
    ) -> CommerceSignals:
        """
        Analyze a product and generate commerce signals.
        """
        logger.info("Generating commerce signals", product_id=product_id, seller_id=seller_id)
        
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
        overall = self._determine_overall(buy_safety, value_score, timing_score)
        
        signals = CommerceSignals(
            product_id=product_id,
            seller_id=seller_id,
            generated_at=datetime.now(timezone.utc),
            
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
        """Get market trends for a category — DB-backed."""
        db = self._get_session()
        try:
            repo = ProductRepository(db)
            products = repo.get_by_category(category, limit=10)
            
            if products:
                popular = [{"id": p.id, "name": p.name} for p in products[:5]]
            else:
                popular = [
                    {"id": "samsung-galaxy-s24-ultra", "name": "Samsung Galaxy S24 Ultra"},
                    {"id": "iphone-16-pro", "name": "iPhone 16 Pro"},
                ]
        finally:
            db.close()

        return {
            "price_trend": {
                "direction": "declining",
                "avg_change_percent": -3.2,
                "period_days": period,
            },
            "popular_products": popular,
            "supply_situation": "normal",
            "upcoming_releases": [
                {"name": "Samsung Galaxy S25", "expected": "Q1 2025"},
            ],
        }
    
    async def get_category_signals(self, category: str, limit: int) -> list[dict]:
        """Get signals for all products in a category."""
        db = self._get_session()
        try:
            repo = ProductRepository(db)
            products = repo.get_by_category(category, limit=limit)
            
            if products:
                results = []
                for p in products:
                    signals = await self.analyze_product(p.id)
                    results.append({
                        "product_id": p.id,
                        "fake_discount_score": signals.fake_discount.score,
                        "store_reliability_score": signals.store_reliability.score,
                        "overall": signals.overall,
                    })
                return results
        finally:
            db.close()

        # Mock fallback
        return [
            {"product_id": "samsung-galaxy-s24-ultra", "fake_discount_score": 15,
             "store_reliability_score": 85, "overall": "safe"},
            {"product_id": "iphone-16-pro", "fake_discount_score": 8,
             "store_reliability_score": 92, "overall": "safe"},
        ][:limit]
    
    def _calculate_buy_safety(
        self,
        fake_discount: FakeDiscountSignal,
        store: StoreReliabilitySignal,
        supply: SupplyRiskSignal,
    ) -> int:
        """Calculate overall buy safety score."""
        score = 70
        
        if fake_discount.is_fake:
            score -= 30
        elif fake_discount.score > 50:
            score -= 15
        
        if store.tier == "trusted":
            score += 15
        elif store.tier == "caution":
            score -= 10
        elif store.tier == "avoid":
            score -= 25
        
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
        
        if volatility.trend == "declining":
            score += 20
        elif volatility.trend == "rising":
            score -= 10
        
        if lifecycle.stage == "decline":
            score += 15
        elif lifecycle.stage == "clearance":
            score += 25
        elif lifecycle.stage == "launch":
            score -= 15
        
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
        """Fetch product data — DB first, then mock."""
        db = self._get_session()
        try:
            repo = ProductRepository(db)
            p = repo.get_by_id(product_id)
            if p and p.price_avg:
                return {
                    "current_price": p.price_avg,
                    "claimed_old_price": p.price_high,
                    "release_date": p.release_date or "2024-01-01",
                    "active_sellers": 47,
                }
        finally:
            db.close()

        return {
            "current_price": 85000,
            "claimed_old_price": 95000,
            "release_date": "2024-01-01",
            "active_sellers": 47,
        }
    
    async def _fetch_price_history(self, product_id: str) -> list[dict]:
        """Fetch price history — DB first, then mock."""
        db = self._get_session()
        try:
            repo = PriceRepository(db)
            entries = repo.get_history(product_id, limit=90)
            if entries:
                return [
                    {"date": str(e.recorded_at.date()) if e.recorded_at else "2024-01-01",
                     "price": e.price}
                    for e in entries
                ]
        finally:
            db.close()

        # Mock fallback
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
        """Fetch store data — DB first, then mock."""
        db = self._get_session()
        try:
            repo = StoreRepository(db)
            store = repo.get_by_id(seller_id)
            if store:
                return {
                    "seller_id": store.id,
                    "reviews": store.total_products,
                    "avg_rating": 4.2,
                    "fulfillment_rate": 0.94,
                    "refund_rate": store.return_rate / 100 if store.return_rate else 0.03,
                    "response_time_hours": 2,
                    "age_months": 48,
                }
        finally:
            db.close()

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
        """Assess supply risk (mock — real feed integration later)."""
        return SupplyRiskSignal(
            level="low",
            active_sellers=47,
            stock_status="abundant",
            alerts=[],
            confidence=0.9,
        )
