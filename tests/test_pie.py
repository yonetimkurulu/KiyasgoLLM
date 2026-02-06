"""
Unit tests for PIE components.
"""
import pytest
from src.pie.normalizer import SpecNormalizer
from src.pie.usage_inference import UsageInferenceService
from src.models.product import ProductSpecs


class TestSpecNormalizer:
    """Tests for SpecNormalizer."""
    
    def setup_method(self):
        self.normalizer = SpecNormalizer()
    
    def test_normalize_basic_specs(self):
        """Test basic spec normalization."""
        raw = {
            "screen_size": "6.8 inch",
            "ram": "12GB",
            "storage": "256GB",
            "battery": "5000mAh",
            "camera": "200MP",
        }
        
        specs = self.normalizer.normalize(raw)
        
        assert specs.screen_size == 6
        assert specs.ram_gb == 12
        assert specs.storage_gb == 256
        assert specs.battery_mah == 5000
        assert specs.camera_mp == 200
    
    def test_extract_number(self):
        """Test number extraction."""
        assert self.normalizer._extract_number("12GB") == 12
        assert self.normalizer._extract_number("256") == 256
        assert self.normalizer._extract_number("6.8 inch") == 6
        assert self.normalizer._extract_number(None) is None
    
    def test_classify_chipset_flagship(self):
        """Test flagship chipset classification."""
        assert self.normalizer._classify_chipset("Snapdragon 8 Gen 3") == "flagship"
        assert self.normalizer._classify_chipset("Apple A17 Pro") == "flagship"
        assert self.normalizer._classify_chipset("Dimensity 9300") == "flagship"
    
    def test_classify_chipset_mid(self):
        """Test mid-range chipset classification."""
        assert self.normalizer._classify_chipset("Snapdragon 7 Gen 2") == "upper_mid"
        assert self.normalizer._classify_chipset("Snapdragon 6 Gen 1") == "mid"
    
    def test_normalize_screen_type(self):
        """Test screen type normalization."""
        assert self.normalizer._normalize_screen_type("Dynamic AMOLED 2X") == "SUPER_AMOLED"
        assert self.normalizer._normalize_screen_type("Super AMOLED") == "SUPER_AMOLED"
        assert self.normalizer._normalize_screen_type("IPS LCD") == "IPS_LCD"
        assert self.normalizer._normalize_screen_type("OLED") == "AMOLED"


class TestUsageInference:
    """Tests for UsageInferenceService."""
    
    def setup_method(self):
        self.service = UsageInferenceService()
    
    def test_gaming_score_flagship(self):
        """Test gaming score for flagship."""
        specs = ProductSpecs(
            chipset_tier="flagship",
            ram_gb=12,
            battery_mah=5000,
            screen_type="AMOLED",
        )
        
        scores = self.service.infer_contexts(specs, price=80000)
        
        assert scores.gaming >= 0.9
    
    def test_photography_score_high_mp(self):
        """Test photography score for high megapixel."""
        specs = ProductSpecs(
            camera_mp=200,
            screen_type="AMOLED",
            storage_gb=256,
        )
        
        scores = self.service.infer_contexts(specs, price=80000)
        
        assert scores.photography >= 0.8
    
    def test_student_score_budget(self):
        """Test student score for budget phone."""
        specs = ProductSpecs(
            battery_mah=5000,
            weight_grams=175,
        )
        
        scores = self.service.infer_contexts(specs, price=12000)
        
        assert scores.student >= 0.8
    
    def test_budget_score_expensive(self):
        """Test budget score for expensive phone."""
        specs = ProductSpecs(chipset_tier="flagship")
        
        scores = self.service.infer_contexts(specs, price=90000)
        
        assert scores.budget <= 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
