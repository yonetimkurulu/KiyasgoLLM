import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.pie.decision_synthesizer import DecisionSynthesizer
from src.models.product import ProductSpecs, UsageContextScores

@pytest.fixture
def mock_llm_provider():
    with patch("src.pie.decision_synthesizer.LLMProvider") as MockClass:
        mock_instance = MockClass.return_value
        # Mock generate to return a JSON string
        mock_instance.generate = AsyncMock(return_value='{"headline": "Test Headline", "verdict_score": 8.5}')
        # Mock prompts
        mock_instance.prompts.decision_synthesis_prompt = MagicMock(return_value="test prompt")
        mock_instance.prompts.system_prompt_turkish = MagicMock(return_value="system prompt")
        yield mock_instance

@pytest.fixture
def synthesizer(mock_llm_provider):
    return DecisionSynthesizer()

@pytest.fixture
def sample_data():
    specs = ProductSpecs(
        chipset_tier="flagship",
        ram_gb=12,
        storage_gb=256,
        screen_type="AMOLED",
        battery_mah=5000,
        camera_mp=200
    )
    scores = UsageContextScores(
        gaming=0.9,
        photography=0.8,
        business=0.7,
        creator=0.6,
        student=0.4,
        budget=0.2,
        long_term=0.8
    )
    return {
        "product_id": "test-1",
        "name": "Test Phone",
        "specs": specs,
        "context_scores": scores,
        "price_info": {"average": 85000},
        "reviews": [{"text": "Great phone", "sentiment": "positive"}]
    }

@pytest.mark.asyncio
async def test_synthesize_llm_success(synthesizer, sample_data):
    """Test synthesis when LLM succeeds."""
    result = await synthesizer.synthesize(**sample_data)
    
    assert result["headline"] == "Test Headline"
    assert result["analysis_type"] == "llm_generated"
    assert result["verdict_score"] == 8.5
    # Check if mathematical logic is preserved for 'best_for'
    assert "gaming" in result["best_for"]

@pytest.mark.asyncio
async def test_synthesize_llm_failure_fallback(synthesizer, sample_data):
    """Test fallback to rules when LLM fails."""
    # Simulate LLM failure
    synthesizer.llm.generate.side_effect = Exception("LLM Error")
    
    result = await synthesizer.synthesize(**sample_data)
    
    assert result["analysis_type"] == "rule_based"
    # Fallback headline generation logic check
    assert "Test Phone" in result["headline"]
    # Verify calculated score
    assert isinstance(result["verdict_score"], float)
    assert result["verdict_score"] > 0

def test_determine_best_for(synthesizer, sample_data):
    """Test rule-based context determination."""
    best = synthesizer.analyzer.determine_best_for(sample_data["context_scores"])
    assert "gaming" in best
    assert "budget" not in best
    assert len(best) <= 3

def test_extract_strengths(synthesizer, sample_data):
    """Test rule-based strength extraction."""
    strengths = synthesizer.analyzer.extract_strengths(sample_data["specs"], sample_data["context_scores"])
    points = [s["point"] for s in strengths]
    assert "200MP ana kamera" in points
    assert "Flagship işlemci" in points
