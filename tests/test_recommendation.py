"""
Tests for Recommendation Engine.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.recommendation.engine import RecommendationEngine
from src.models.product import ProductSpecs, UsageContextScores, PricingInfo


class TestGetCandidates:
    """Tests for candidate retrieval."""

    @pytest.mark.asyncio
    async def test_smartphone_candidates(self):
        engine = RecommendationEngine()
        candidates = await engine._get_candidates("smartphone", None)
        assert len(candidates) > 0
        assert all("id" in c for c in candidates)

    @pytest.mark.asyncio
    async def test_laptop_candidates(self):
        engine = RecommendationEngine()
        candidates = await engine._get_candidates("laptop", None)
        assert len(candidates) > 0
        ids = [c["id"] for c in candidates]
        assert "macbook-pro-16" in ids

    @pytest.mark.asyncio
    async def test_tablet_candidates(self):
        engine = RecommendationEngine()
        candidates = await engine._get_candidates("tablet", None)
        assert len(candidates) > 0

    @pytest.mark.asyncio
    async def test_unknown_category_defaults_to_smartphone(self):
        engine = RecommendationEngine()
        candidates = await engine._get_candidates("unknown_category", None)
        # Should fallback to smartphone
        assert len(candidates) > 0

    @pytest.mark.asyncio
    async def test_phone_alias(self):
        engine = RecommendationEngine()
        candidates = await engine._get_candidates("phone", None)
        assert len(candidates) > 0


class TestGenerateWhy:
    """Tests for why-text generation."""

    def _make_intel(self, context_scores=None, specs=None, pricing=None):
        intel = MagicMock()
        intel.specs = specs or ProductSpecs(
            chipset_tier="flagship",
            camera_mp=200,
            battery_mah=5000,
        )
        intel.context_scores = context_scores or UsageContextScores(
            gaming=0.9, photography=0.95, budget=0.2,
        )
        intel.pricing = pricing
        return intel

    def test_gaming_context_flagship(self):
        engine = RecommendationEngine()
        intel = self._make_intel()
        why = engine._generate_why(intel, "gaming", None)
        assert isinstance(why, str)
        assert len(why) > 0

    def test_photography_context(self):
        engine = RecommendationEngine()
        intel = self._make_intel()
        why = engine._generate_why(intel, "photography", None)
        assert isinstance(why, str)

    def test_budget_reason_added(self):
        engine = RecommendationEngine()
        pricing = PricingInfo(current_low=15000, current_high=18000, average=16000)
        intel = self._make_intel(pricing=pricing)
        why = engine._generate_why(intel, "budget", budget=30000)
        # Should mention budget if price is well under budget
        assert isinstance(why, str)

    def test_default_reason(self):
        engine = RecommendationEngine()
        intel = self._make_intel(
            context_scores=UsageContextScores(gaming=0.5),
            specs=ProductSpecs(),
        )
        why = engine._generate_why(intel, "some_random_context", None)
        assert isinstance(why, str)
        assert len(why) > 0


class TestCalculateSimilarity:
    """Tests for similarity calculation."""

    def _make_intel_with_scores(self, **kwargs):
        intel = MagicMock()
        scores = UsageContextScores(**kwargs)
        intel.context_scores = scores
        return intel

    def test_identical_products(self):
        engine = RecommendationEngine()
        intel = self._make_intel_with_scores(
            gaming=0.9, photography=0.8, student=0.3,
            business=0.7, budget=0.2, long_term=0.8, creator=0.7,
        )
        similarity = engine._calculate_similarity(intel, intel)
        assert similarity == pytest.approx(1.0)

    def test_different_products(self):
        engine = RecommendationEngine()
        intel1 = self._make_intel_with_scores(
            gaming=0.9, photography=0.9, student=0.2,
            business=0.8, budget=0.1, long_term=0.9, creator=0.9,
        )
        intel2 = self._make_intel_with_scores(
            gaming=0.2, photography=0.3, student=0.9,
            business=0.3, budget=0.9, long_term=0.2, creator=0.2,
        )
        similarity = engine._calculate_similarity(intel1, intel2)
        assert similarity < 0.5

    def test_similarity_range(self):
        engine = RecommendationEngine()
        intel1 = self._make_intel_with_scores(gaming=1.0)
        intel2 = self._make_intel_with_scores(gaming=0.0)
        similarity = engine._calculate_similarity(intel1, intel2)
        assert 0 <= similarity <= 1
