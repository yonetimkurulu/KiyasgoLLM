"""
Tests for Signal Analyzer module.
"""
import pytest
from src.pie.signal_analyzer import SignalAnalyzer
from src.models.product import ProductSpecs, UsageContextScores


@pytest.fixture
def analyzer():
    return SignalAnalyzer()


@pytest.fixture
def flagship_specs():
    return ProductSpecs(
        chipset="Snapdragon 8 Gen 3",
        chipset_tier="flagship",
        camera_mp=200,
        battery_mah=5000,
        screen_type="AMOLED",
        ram_gb=12,
        storage_gb=256,
        weight_grams=232,
    )


@pytest.fixture
def budget_specs():
    return ProductSpecs(
        chipset="Dimensity 700",
        chipset_tier="budget",
        camera_mp=48,
        battery_mah=3800,
        screen_type="IPS",
        ram_gb=4,
        storage_gb=64,
        weight_grams=180,
    )


@pytest.fixture
def high_scores():
    return UsageContextScores(
        gaming=0.9,
        photography=0.95,
        student=0.4,
        business=0.75,
        budget=0.15,
        long_term=0.85,
        creator=0.88,
    )


@pytest.fixture
def low_scores():
    return UsageContextScores(
        gaming=0.3,
        photography=0.35,
        student=0.8,
        business=0.4,
        budget=0.9,
        long_term=0.35,
        creator=0.3,
    )


class TestDetermineBestFor:

    def test_returns_high_scoring_contexts(self, analyzer, high_scores):
        best = analyzer.determine_best_for(high_scores)
        assert "photography" in best
        assert "gaming" in best

    def test_max_3_results(self, analyzer, high_scores):
        best = analyzer.determine_best_for(high_scores)
        assert len(best) <= 3

    def test_sorted_by_score(self, analyzer, high_scores):
        best = analyzer.determine_best_for(high_scores)
        assert best[0] == "photography"  # 0.95 is highest

    def test_budget_best_for(self, analyzer, low_scores):
        best = analyzer.determine_best_for(low_scores)
        assert "budget" in best
        assert "student" in best


class TestDetermineAvoidFor:

    def test_returns_low_scoring_contexts(self, analyzer, high_scores):
        avoid = analyzer.determine_avoid_for(high_scores)
        assert "budget" in avoid

    def test_budget_avoids_gaming(self, analyzer, low_scores):
        avoid = analyzer.determine_avoid_for(low_scores)
        assert "gaming" in avoid
        assert "photography" in avoid


class TestGenerateWhoShouldBuy:

    def test_photography_recommendation(self, analyzer, flagship_specs, high_scores):
        best_for = ["photography", "gaming", "creator"]
        result = analyzer.generate_who_should_buy(flagship_specs, high_scores, best_for)
        assert "Mobil fotoğrafçılık tutkunları" in result

    def test_gaming_recommendation(self, analyzer, flagship_specs, high_scores):
        best_for = ["gaming"]
        result = analyzer.generate_who_should_buy(flagship_specs, high_scores, best_for)
        assert "Mobil oyun tutkunları" in result

    def test_flagship_premium(self, analyzer, flagship_specs, high_scores):
        result = analyzer.generate_who_should_buy(flagship_specs, high_scores, [])
        assert "Premium deneyim arayanlar" in result

    def test_max_4_results(self, analyzer, flagship_specs, high_scores):
        best_for = ["photography", "gaming", "long_term", "business", "creator"]
        result = analyzer.generate_who_should_buy(flagship_specs, high_scores, best_for)
        assert len(result) <= 4


class TestGenerateWhoShouldAvoid:

    def test_budget_aware_avoid(self, analyzer, flagship_specs, high_scores):
        avoid_for = ["budget", "student"]
        result = analyzer.generate_who_should_avoid(
            flagship_specs, high_scores, avoid_for, {"average": 80000}
        )
        assert "Bütçe bilincli alıcılar" in result
        assert "Öğrenciler" in result

    def test_heavy_phone_avoid(self, analyzer, flagship_specs, high_scores):
        result = analyzer.generate_who_should_avoid(
            flagship_specs, high_scores, [], None
        )
        assert "Kompakt telefon arayanlar" in result

    def test_expensive_phone_avoid(self, analyzer, budget_specs, low_scores):
        result = analyzer.generate_who_should_avoid(
            budget_specs, low_scores, [], {"average": 80000}
        )
        assert "Uygun fiyat arayanlar" in result


class TestCalculateVerdictScore:

    def test_flagship_high_score(self, analyzer, flagship_specs, high_scores):
        score = analyzer.calculate_verdict_score(flagship_specs, high_scores, None)
        assert score >= 7.0

    def test_budget_lower_score(self, analyzer, budget_specs, low_scores):
        score = analyzer.calculate_verdict_score(budget_specs, low_scores, None)
        assert score <= 7.0

    def test_score_clamped(self, analyzer, flagship_specs, high_scores):
        score = analyzer.calculate_verdict_score(flagship_specs, high_scores, None)
        assert 1.0 <= score <= 10.0

    def test_expensive_price_penalty(self, analyzer, flagship_specs, high_scores):
        score_no_price = analyzer.calculate_verdict_score(flagship_specs, high_scores, None)
        score_expensive = analyzer.calculate_verdict_score(
            flagship_specs, high_scores, {"average": 100000}
        )
        assert score_expensive < score_no_price


class TestExtractStrengths:

    def test_camera_strength(self, analyzer, flagship_specs, high_scores):
        strengths = analyzer.extract_strengths(flagship_specs, high_scores)
        camera_strengths = [s for s in strengths if "kamera" in s["point"].lower() or "MP" in s["point"]]
        assert len(camera_strengths) > 0

    def test_chipset_strength(self, analyzer, flagship_specs, high_scores):
        strengths = analyzer.extract_strengths(flagship_specs, high_scores)
        chipset_strengths = [s for s in strengths if "Flagship" in s["point"]]
        assert len(chipset_strengths) > 0

    def test_max_5_strengths(self, analyzer, flagship_specs, high_scores):
        strengths = analyzer.extract_strengths(flagship_specs, high_scores)
        assert len(strengths) <= 5


class TestExtractWeaknesses:

    def test_heavy_weakness(self, analyzer, flagship_specs):
        weaknesses = analyzer.extract_weaknesses(flagship_specs, None)
        weight_weak = [w for w in weaknesses if "Ağır" in w["point"]]
        assert len(weight_weak) > 0

    def test_expensive_weakness(self, analyzer, flagship_specs):
        weaknesses = analyzer.extract_weaknesses(flagship_specs, {"average": 80000})
        price_weak = [w for w in weaknesses if "fiyat" in w["point"].lower()]
        assert len(price_weak) > 0

    def test_small_battery_weakness(self, analyzer, budget_specs):
        weaknesses = analyzer.extract_weaknesses(budget_specs, None)
        battery_weak = [w for w in weaknesses if "batarya" in w["point"].lower()]
        assert len(battery_weak) > 0

    def test_low_storage_weakness(self, analyzer, budget_specs):
        weaknesses = analyzer.extract_weaknesses(budget_specs, None)
        storage_weak = [w for w in weaknesses if "depolama" in w["point"].lower()]
        assert len(storage_weak) > 0
