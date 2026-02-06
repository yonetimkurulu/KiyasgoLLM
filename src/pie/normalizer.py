"""
Spec Normalizer Service
Ham ürün spec verilerini standart formata dönüştürür.
"""
import re
from typing import Optional
from src.models.product import ProductSpecs


class SpecNormalizer:
    """
    Normalize raw product specifications into structured format.
    
    Handles:
    - Unit conversion (inch, GB, mAh, etc.)
    - Variant extraction (storage options)
    - Chipset tier classification
    """
    
    def normalize(self, raw_specs: dict) -> ProductSpecs:
        """
        Normalize raw specifications.
        
        Args:
            raw_specs: Raw spec dictionary from scraper/API
            
        Returns:
            ProductSpecs with structured data
        """
        specs = ProductSpecs()
        
        # Screen size
        if "screen_size" in raw_specs:
            specs.screen_size = self._extract_number(raw_specs["screen_size"])
        
        # Screen type
        if "screen_type" in raw_specs:
            specs.screen_type = self._normalize_screen_type(raw_specs["screen_type"])
        
        # Chipset
        if "chipset" in raw_specs:
            specs.chipset = raw_specs["chipset"]
            specs.chipset_tier = self._classify_chipset(raw_specs["chipset"])
        
        # RAM
        if "ram" in raw_specs:
            specs.ram_gb = self._extract_number(raw_specs["ram"])
        
        # Storage
        if "storage" in raw_specs:
            storage = self._extract_storage(raw_specs["storage"])
            specs.storage_gb = storage["primary"]
            specs.extra["storage_variants"] = storage.get("variants", [])
        
        # Battery
        if "battery" in raw_specs:
            specs.battery_mah = self._extract_number(raw_specs["battery"])
        
        # Camera
        if "camera" in raw_specs:
            specs.camera_mp = self._extract_main_camera(raw_specs["camera"])
        
        # Weight
        if "weight" in raw_specs:
            specs.weight_grams = self._extract_number(raw_specs["weight"])
        
        return specs
    
    def _extract_number(self, value: str) -> Optional[int]:
        """Extract first number from string."""
        if isinstance(value, (int, float)):
            return int(value)
        
        match = re.search(r'(\d+(?:\.\d+)?)', str(value))
        if match:
            return int(float(match.group(1)))
        return None
    
    def _normalize_screen_type(self, screen_type: str) -> str:
        """Normalize screen type to standard format."""
        screen_type = screen_type.upper()
        
        if "AMOLED" in screen_type or "OLED" in screen_type:
            if "DYNAMIC" in screen_type or "SUPER" in screen_type:
                return "SUPER_AMOLED"
            return "AMOLED"
        elif "IPS" in screen_type:
            return "IPS_LCD"
        elif "LCD" in screen_type:
            return "LCD"
        elif "RETINA" in screen_type:
            return "OLED"
        
        return screen_type
    
    def _classify_chipset(self, chipset: str) -> str:
        """
        Classify chipset into tier.
        
        Tiers:
        - flagship: Top-tier processors
        - upper_mid: High-end mid-range
        - mid: Mid-range
        - entry: Entry-level
        """
        chipset_lower = chipset.lower()
        
        # Flagship chips
        flagship_keywords = [
            "snapdragon 8", "a18", "a17", "a16", "dimensity 9",
            "exynos 2", "kirin 9", "tensor g"
        ]
        
        for keyword in flagship_keywords:
            if keyword in chipset_lower:
                return "flagship"
        
        # Upper mid
        upper_mid_keywords = [
            "snapdragon 7", "dimensity 8", "exynos 1", "a15"
        ]
        
        for keyword in upper_mid_keywords:
            if keyword in chipset_lower:
                return "upper_mid"
        
        # Mid
        mid_keywords = [
            "snapdragon 6", "dimensity 7", "helio g9"
        ]
        
        for keyword in mid_keywords:
            if keyword in chipset_lower:
                return "mid"
        
        return "entry"
    
    def _extract_storage(self, storage_str: str) -> dict:
        """Extract storage variants."""
        # Find all storage values
        matches = re.findall(r'(\d+)\s*(?:GB|TB)', str(storage_str), re.IGNORECASE)
        
        variants = []
        for match in matches:
            value = int(match)
            # Convert TB to GB if needed
            if "TB" in storage_str.upper() and value < 10:
                value = value * 1024
            variants.append(value)
        
        if variants:
            return {
                "primary": variants[0],
                "variants": variants,
            }
        
        return {"primary": None, "variants": []}
    
    def _extract_main_camera(self, camera_str: str) -> Optional[int]:
        """Extract main camera megapixels."""
        # Find first/highest MP value
        matches = re.findall(r'(\d+)\s*MP', str(camera_str), re.IGNORECASE)
        
        if matches:
            return max(int(m) for m in matches)
        
        return None
