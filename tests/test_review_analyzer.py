"""
Unit tests for ReviewAnalyzer (Sentiment Engine).
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.pie.review_analyzer import ReviewAnalyzer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def analyzer():
    """Create a ReviewAnalyzer with default settings."""
    return ReviewAnalyzer()


@pytest.fixture
def sample_serpapi_reviews():
    """Sample SerpApi reviews_results data."""
    return [
        {
            "rating": 5,
            "snippet": "Kamera kalitesi çok iyi, fotoğraflar gayet net ve detaylı çıkıyor.",
            "title": "Harika bir telefon",
            "source": "Google Play",
            "date": "2024-01-15",
        },
        {
            "rating": 4,
            "snippet": "Pil ömrü oldukça uzun, gün boyu şarj etmeden kullanabiliyorum. Ekran da parlak ve güzel.",
            "title": "Memnunum",
            "source": "Google Play",
            "date": "2024-01-10",
        },
        {
            "rating": 2,
            "snippet": "Performans konusunda hayal kırıklığı, oyunlarda kasma var ve fiyatına göre yetersiz.",
            "title": "Beklentilerimi karşılamadı",
            "source": "Google Play",
            "date": "2024-01-08",
        },
        {
            "rating": 3,
            "snippet": "Tasarım güzel ama batarya biraz zayıf, şarj hızlı bitiyor.",
            "title": "İdare eder",
            "source": "Google Play",
            "date": "2024-01-05",
        },
    ]


@pytest.fixture
def hollow_reviews():
    """Reviews that should be filtered as hollow/generic."""
    return [
        {"rating": 5, "snippet": "çok iyi", "title": ""},
        {"rating": 5, "snippet": "harika", "title": ""},
        {"rating": 1, "snippet": "kötü", "title": ""},
        {"rating": 5, "snippet": "mükemmel", "title": ""},
    ]


@pytest.fixture
def mixed_reviews():
    """Mix of valid and invalid reviews."""
    return [
        {"rating": 5, "snippet": "çok iyi", "title": ""},  # hollow
        {"rating": 5, "snippet": "ab", "title": ""},  # too short
        {
            "rating": 4,
            "snippet": "Kamera gerçekten çok başarılı, detaylı fotoğraflar çekebiliyorsunuz.",
            "title": "Güzel telefon",
        },  # valid
        {
            "rating": 4,
            "snippet": "Kamera gerçekten çok başarılı, detaylı fotoğraflar çekebiliyorsunuz.",
            "title": "Güzel telefon",
        },  # duplicate
        {
            "rating": 3,
            "snippet": "Ekran kalitesi iyi ama pil ömrü kısa, gün sonuna zor yetişiyor.",
            "title": "Orta seviye",
        },  # valid
    ]


# ===========================================================================
# TestParseReviews
# ===========================================================================

class TestParseReviews:
    """Tests for ReviewAnalyzer.parse_reviews."""

    def test_parse_normal_reviews(self, analyzer, sample_serpapi_reviews):
        """Test parsing standard SerpApi reviews."""
        result = analyzer.parse_reviews(sample_serpapi_reviews)

        assert len(result) == 4
        assert result[0]["rating"] == 5
        assert "Kamera kalitesi" in result[0]["snippet"]
        assert result[0]["title"] == "Harika bir telefon"
        assert result[0]["source"] == "Google Play"

    def test_parse_empty_list(self, analyzer):
        """Test parsing empty list returns empty."""
        assert analyzer.parse_reviews([]) == []
        assert analyzer.parse_reviews(None) == []

    def test_parse_invalid_items(self, analyzer):
        """Test that non-dict items are skipped."""
        result = analyzer.parse_reviews(["not a dict", 42, None])
        assert result == []

    def test_normalize_rating_10_scale(self, analyzer):
        """Test that 1-10 scale ratings are converted to 1-5."""
        assert analyzer._normalize_rating(10) == 5
        assert analyzer._normalize_rating(8) == 4
        assert analyzer._normalize_rating(6) == 3

    def test_normalize_rating_5_scale(self, analyzer):
        """Test that 1-5 scale ratings stay as-is."""
        assert analyzer._normalize_rating(5) == 5
        assert analyzer._normalize_rating(3) == 3
        assert analyzer._normalize_rating(1) == 1

    def test_normalize_rating_none(self, analyzer):
        """Test that None rating returns None."""
        assert analyzer._normalize_rating(None) is None
        assert analyzer._normalize_rating("invalid") is None

    def test_parse_missing_fields(self, analyzer):
        """Test parsing reviews with missing fields."""
        result = analyzer.parse_reviews([{"rating": 4}])
        assert len(result) == 1
        assert result[0]["snippet"] == ""
        assert result[0]["title"] == ""
        assert result[0]["rating"] == 4


# ===========================================================================
# TestFilterReviews
# ===========================================================================

class TestFilterReviews:
    """Tests for ReviewAnalyzer.filter_reviews."""

    def test_filter_hollow_reviews(self, analyzer, hollow_reviews):
        """Hollow reviews should be filtered out."""
        parsed = analyzer.parse_reviews(hollow_reviews)
        result = analyzer.filter_reviews(parsed)
        # All should be filtered (hollow + too short)
        assert len(result) == 0

    def test_filter_short_reviews(self, analyzer):
        """Reviews shorter than min_snippet_length should be filtered."""
        reviews = [
            {"rating": 5, "snippet": "ab", "title": ""},
            {"rating": 4, "snippet": "Bu telefon gerçekten çok iyi bir seçim.", "title": "Güzel"},
        ]
        result = analyzer.filter_reviews(reviews)
        assert len(result) == 1
        assert "Bu telefon" in result[0]["snippet"]

    def test_filter_duplicates(self, analyzer):
        """Duplicate snippets should be filtered."""
        reviews = [
            {"rating": 4, "snippet": "Bu telefon gerçekten harika bir cihaz.", "title": "İyi"},
            {"rating": 4, "snippet": "Bu telefon gerçekten harika bir cihaz.", "title": "İyi"},
        ]
        result = analyzer.filter_reviews(reviews)
        assert len(result) == 1

    def test_filter_extreme_short(self, analyzer):
        """5★ or 1★ with very short text should be filtered."""
        reviews = [
            {"rating": 5, "snippet": "güzel telefon bence", "title": ""},  # 19 chars, < 20, 5★ → filtered
            {"rating": 1, "snippet": "berbat bir cihazdır", "title": ""},  # 19 chars, < 20, 1★ → filtered
            {"rating": 3, "snippet": "idare eden bir telefon", "title": ""},  # 3★ not extreme → kept
            {"rating": 4, "snippet": "beğendim fena değil", "title": ""},  # 4★ not extreme → kept
        ]
        result = analyzer.filter_reviews(reviews)
        # Extreme ratings (5★, 1★) with < 20 chars removed, non-extreme kept
        assert len(result) == 2
        ratings = [r["rating"] for r in result]
        assert 5 not in ratings
        assert 1 not in ratings

    def test_filter_keeps_valid_reviews(self, analyzer, sample_serpapi_reviews):
        """Valid reviews should not be filtered."""
        parsed = analyzer.parse_reviews(sample_serpapi_reviews)
        result = analyzer.filter_reviews(parsed)
        assert len(result) == 4

    def test_filter_empty_list(self, analyzer):
        """Empty list returns empty."""
        assert analyzer.filter_reviews([]) == []

    def test_mixed_reviews(self, analyzer, mixed_reviews):
        """Only valid, non-duplicate reviews should survive."""
        result = analyzer.filter_reviews(mixed_reviews)
        # hollow + short + duplicate removed → 2 valid
        assert len(result) == 2


# ===========================================================================
# TestRuleBasedFallback
# ===========================================================================

class TestRuleBasedFallback:
    """Tests for ReviewAnalyzer._rule_based_fallback."""

    def test_positive_reviews(self, analyzer):
        """Mostly positive reviews should yield high sentiment score."""
        reviews = [
            {"rating": 5, "snippet": "Kamera çok iyi, fotoğraflar harika çıkıyor.", "title": ""},
            {"rating": 4, "snippet": "Pil ömrü uzun, güzel telefon.", "title": ""},
            {"rating": 5, "snippet": "Ekran parlak ve net, performans süper.", "title": ""},
        ]
        result = analyzer._rule_based_fallback(reviews)

        assert result["overall_sentiment_score"] > 0.7
        assert result["analysis_type"] == "rule_based"
        assert result["confidence"] == 0.5
        assert len(result["aspects"]) > 0

    def test_negative_reviews(self, analyzer):
        """Mostly negative reviews should yield low sentiment score."""
        reviews = [
            {"rating": 1, "snippet": "Kamera berbat, fotoğraflar kötü çıkıyor.", "title": ""},
            {"rating": 2, "snippet": "Pil yetersiz, performans yavaş.", "title": ""},
            {"rating": 1, "snippet": "Ekran kalitesi zayıf, hayal kırıklığı.", "title": ""},
        ]
        result = analyzer._rule_based_fallback(reviews)

        assert result["overall_sentiment_score"] < 0.3
        assert len(result["aspects"]) > 0

    def test_aspect_extraction(self, analyzer):
        """Should extract aspects from keyword mentions."""
        reviews = [
            {"rating": 4, "snippet": "Kamera çok güzel, batarya uzun ömürlü.", "title": ""},
            {"rating": 3, "snippet": "Ekran iyi ama fiyat pahalı.", "title": ""},
        ]
        result = analyzer._rule_based_fallback(reviews)

        aspect_names = [a["aspect"] for a in result["aspects"]]
        assert "Kamera" in aspect_names
        assert any("Ekran" in name for name in aspect_names)

    def test_empty_reviews(self, analyzer):
        """Empty reviews should return neutral result."""
        result = analyzer._rule_based_fallback([])
        assert result["overall_sentiment_score"] == 0.5
        assert result["aspects"] == []


# ===========================================================================
# TestAnalyzeSentiment
# ===========================================================================

class TestAnalyzeSentiment:
    """Tests for the full analyze_sentiment pipeline."""

    @pytest.mark.asyncio
    async def test_analyze_rule_based(self, analyzer, sample_serpapi_reviews):
        """Test analyze_sentiment with use_llm=False."""
        result = await analyzer.analyze_sentiment(
            sample_serpapi_reviews, use_llm=False
        )

        assert "overall_sentiment_score" in result
        assert 0.0 <= result["overall_sentiment_score"] <= 1.0
        assert result["review_count"] > 0
        assert result["filtered_count"] >= 0
        assert result["analysis_type"] == "rule_based"
        assert isinstance(result["aspects"], list)

    @pytest.mark.asyncio
    async def test_analyze_empty(self, analyzer):
        """Test analyze_sentiment with empty input."""
        result = await analyzer.analyze_sentiment([], use_llm=False)

        assert result["overall_sentiment_score"] == 0.5
        assert result["review_count"] == 0
        assert result["analysis_type"] == "no_data"

    @pytest.mark.asyncio
    async def test_analyze_llm_fallback_on_error(self, analyzer, sample_serpapi_reviews):
        """If LLM fails, should fall back to rule-based."""
        with patch(
            "src.llm.advanced_provider.get_advanced_llm",
            side_effect=Exception("LLM not available"),
        ):
            result = await analyzer.analyze_sentiment(
                sample_serpapi_reviews, use_llm=True
            )
        assert result["analysis_type"] == "rule_based"

    @pytest.mark.asyncio
    async def test_analyze_with_mocked_llm(self, analyzer, sample_serpapi_reviews):
        """Test analyze_sentiment with mocked LLM."""
        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = {
            "overall_sentiment_score": 0.82,
            "aspects": [
                {"aspect": "Kamera", "score": 1, "mention_count": 3},
                {"aspect": "Pil Ömrü", "score": 1, "mention_count": 2},
                {"aspect": "Performans", "score": -1, "mention_count": 1},
            ],
            "confidence": 0.88,
        }

        with patch(
            "src.llm.advanced_provider.get_advanced_llm",
            return_value=mock_llm,
        ):
            result = await analyzer._analyze_with_llm(
                analyzer.parse_reviews(sample_serpapi_reviews)
            )

        assert result["overall_sentiment_score"] == 0.82
        assert len(result["aspects"]) == 3
        assert result["aspects"][0]["aspect"] == "Kamera"
        assert result["analysis_type"] == "llm_absa"


# ===========================================================================
# TestHelpers
# ===========================================================================

class TestHelpers:
    """Tests for helper methods."""

    def test_clamp_01(self, analyzer):
        """Test value clamping to 0-1 range."""
        assert analyzer._clamp_01(0.5) == 0.5
        assert analyzer._clamp_01(-0.3) == 0.0
        assert analyzer._clamp_01(1.5) == 1.0
        assert analyzer._clamp_01("invalid") == 0.5

    def test_validate_aspects_valid(self, analyzer):
        """Test validation of proper aspect list."""
        aspects = [
            {"aspect": "Kamera", "score": 1, "mention_count": 3},
            {"aspect": "Ekran", "score": -1, "mention_count": 2},
        ]
        result = analyzer._validate_aspects(aspects)
        assert len(result) == 2
        assert result[0]["score"] == 1

    def test_validate_aspects_invalid_score(self, analyzer):
        """Scores outside -1/0/1 should be clamped."""
        aspects = [
            {"aspect": "Kamera", "score": 5, "mention_count": 3},
            {"aspect": "Ekran", "score": -3, "mention_count": 2},
        ]
        result = analyzer._validate_aspects(aspects)
        assert result[0]["score"] == 1   # 5 > 0 => 1
        assert result[1]["score"] == -1  # -3 < 0 => -1

    def test_validate_aspects_empty_name(self, analyzer):
        """Aspects with empty names should be filtered."""
        aspects = [
            {"aspect": "", "score": 1, "mention_count": 1},
            {"aspect": "Kamera", "score": 1, "mention_count": 2},
        ]
        result = analyzer._validate_aspects(aspects)
        assert len(result) == 1

    def test_is_hollow(self, analyzer):
        """Test hollow review detection."""
        assert analyzer._is_hollow("çok iyi") is True
        assert analyzer._is_hollow("harika") is True
        assert analyzer._is_hollow("mükemmel") is True
        assert analyzer._is_hollow("Bu telefon gerçekten çok iyi bir cihaz") is False

    def test_text_polarity(self, analyzer):
        """Test text polarity detection."""
        assert analyzer._text_polarity("güzel ve kaliteli bir ürün") == 1
        assert analyzer._text_polarity("berbat ve yetersiz") == -1
        assert analyzer._text_polarity("telefon var") == 0

    def test_empty_result(self, analyzer):
        """Test empty result generation."""
        result = analyzer._empty_result(5, 3)
        assert result["overall_sentiment_score"] == 0.5
        assert result["review_count"] == 5
        assert result["filtered_count"] == 3
        assert result["analysis_type"] == "no_data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
