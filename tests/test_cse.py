"""
Unit tests for CSE components.
"""
import pytest
from src.cse.fake_discount_detector import FakeDiscountDetector
from src.cse.store_reliability import StoreReliabilityScorer
from src.cse.price_volatility import PriceVolatilityAnalyzer
from src.cse.lifecycle_scorer import LifecycleScorer


class TestFakeDiscountDetector:
    """Tests for FakeDiscountDetector."""
    
    def setup_method(self):
        self.detector = FakeDiscountDetector()
    
    def test_no_discount(self):
        """Test when there's no claimed discount."""
        signal = self.detector.detect(
            current_price=50000,
            claimed_old_price=None,
            price_history=[],
        )
        
        assert signal.is_fake is False
        assert signal.score == 0
    
    def test_real_discount(self):
        """Test a real discount."""
        history = [{"price": 55000} for _ in range(30)]
        
        signal = self.detector.detect(
            current_price=45000,
            claimed_old_price=55000,
            price_history=history,
        )
        
        assert signal.is_fake is False
        assert signal.real_discount > 0
    
    def test_fake_discount_inflated_reference(self):
        """Test fake discount with inflated reference price."""
        # Average price is 50000, but claimed old price is 80000
        history = [{"price": 50000} for _ in range(30)]
        
        signal = self.detector.detect(
            current_price=48000,
            claimed_old_price=80000,
            price_history=history,
        )
        
        assert signal.score > 30  # Should have high risk score
        assert len(signal.evidence) > 0


class TestStoreReliability:
    """Tests for StoreReliabilityScorer."""
    
    def setup_method(self):
        self.scorer = StoreReliabilityScorer()
    
    def test_trusted_store(self):
        """Test scoring a trusted store."""
        store_data = {
            "reviews": 5000,
            "avg_rating": 4.8,
            "fulfillment_rate": 0.99,
            "refund_rate": 0.01,
            "response_time_hours": 1,
            "age_months": 60,
        }
        
        signal = self.scorer.score(store_data)
        
        assert signal.tier == "trusted"
        assert signal.score >= 80
    
    def test_caution_store(self):
        """Test scoring a cautionary store."""
        store_data = {
            "reviews": 50,
            "avg_rating": 3.2,
            "fulfillment_rate": 0.82,
            "refund_rate": 0.08,
            "response_time_hours": 36,
            "age_months": 4,
        }
        
        signal = self.scorer.score(store_data)
        
        assert signal.tier in ["caution", "avoid"]
        assert len(signal.red_flags) > 0
    
    def test_empty_store_data(self):
        """Test with no store data."""
        signal = self.scorer.score(None)
        
        assert signal.score == 50  # Default
        assert signal.tier == "standard"


class TestPriceVolatility:
    """Tests for PriceVolatilityAnalyzer."""
    
    def setup_method(self):
        self.analyzer = PriceVolatilityAnalyzer()
    
    def test_stable_prices(self):
        """Test with stable prices."""
        history = [{"price": 50000} for _ in range(30)]
        
        signal = self.analyzer.analyze(history)
        
        assert signal.stability == "stable"
        assert signal.trend == "stable"
    
    def test_declining_trend(self):
        """Test with declining prices."""
        history = [{"price": 60000 - i * 500} for i in range(30)]
        
        signal = self.analyzer.analyze(history)
        
        assert signal.trend == "declining"
    
    def test_insufficient_data(self):
        """Test with insufficient data."""
        history = [{"price": 50000}]
        
        signal = self.analyzer.analyze(history)
        
        assert signal.stability == "unknown"
        assert signal.confidence == 0.5


class TestLifecycleScorer:
    """Tests for LifecycleScorer."""
    
    def setup_method(self):
        self.scorer = LifecycleScorer()
    
    def test_launch_stage(self):
        """Test newly launched product."""
        product_data = {
            "release_date": "2026-01",
            "successor_announced": False,
        }
        
        signal = self.scorer.determine_stage(product_data)
        
        assert signal.stage == "launch"
        assert signal.months_since_launch < 3
    
    def test_decline_with_successor(self):
        """Test product with announced successor."""
        product_data = {
            "release_date": "2024-01",
            "successor_announced": True,
        }
        
        signal = self.scorer.determine_stage(product_data)
        
        assert signal.stage == "decline"
        assert signal.successor_announced is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
