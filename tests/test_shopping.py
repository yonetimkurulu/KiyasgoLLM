"""
Tests for the Shopping module (normalizer + client mocking).
"""
import pytest
from src.shopping.normalizer import ShoppingNormalizer


class TestShoppingNormalizer:
    """Tests for ShoppingNormalizer."""

    def setup_method(self):
        self.normalizer = ShoppingNormalizer()

    # --- Price parsing ---

    def test_parse_price_extracted(self):
        result = self.normalizer._parse_price({"extracted_price": 85999})
        assert result == 85999

    def test_parse_price_extracted_float(self):
        result = self.normalizer._parse_price({"extracted_price": 85999.99})
        assert result == 85999

    def test_parse_price_turkish_format(self):
        result = self.normalizer._parse_price({"price": "85.999,00 TL"})
        assert result == 85999

    def test_parse_price_simple(self):
        result = self.normalizer._parse_price({"price": "74000 TL"})
        assert result == 74000

    def test_parse_price_comma_decimal(self):
        result = self.normalizer._parse_price({"price": "74000,50"})
        assert result == 74000

    def test_parse_price_empty(self):
        result = self.normalizer._parse_price({})
        assert result is None

    def test_parse_price_usd(self):
        result = self.normalizer._parse_price({"price": "$1299"})
        assert result == 1299

    # --- Slugify ---

    def test_slugify_basic(self):
        slug = self.normalizer._slugify("Samsung Galaxy S24 Ultra")
        assert slug == "samsung-galaxy-s24-ultra"

    def test_slugify_parenthetical(self):
        slug = self.normalizer._slugify("iPhone 16 Pro (256GB)")
        assert slug == "iphone-16-pro"

    def test_slugify_special_chars(self):
        slug = self.normalizer._slugify("MacBook Pro 16\" M3 Max")
        assert "macbook-pro-16" in slug

    def test_slugify_turkish_chars(self):
        slug = self.normalizer._slugify("Akilli Telefon 2024")
        assert "akilli" in slug or "aklli" in slug

    # --- Brand detection ---

    def test_brand_samsung(self):
        assert self.normalizer._detect_brand("Samsung Galaxy S24 Ultra") == "Samsung"

    def test_brand_apple_iphone(self):
        assert self.normalizer._detect_brand("iPhone 16 Pro Max") == "Apple"

    def test_brand_apple_macbook(self):
        assert self.normalizer._detect_brand("MacBook Pro 16 M3") == "Apple"

    def test_brand_xiaomi(self):
        assert self.normalizer._detect_brand("Xiaomi 14T Pro") == "Xiaomi"

    def test_brand_unknown(self):
        assert self.normalizer._detect_brand("Some Random Product") == "Unknown"

    # --- Category detection ---

    def test_category_phone(self):
        assert self.normalizer._detect_category("Akilli Telefon Samsung", "unknown") == "smartphone"

    def test_category_laptop(self):
        assert self.normalizer._detect_category("Gaming Laptop RTX 4090", "unknown") == "laptop"

    def test_category_tablet(self):
        assert self.normalizer._detect_category("iPad Pro 13 inch", "unknown") == "tablet"

    def test_category_default(self):
        assert self.normalizer._detect_category("Some Product", "smartphone") == "smartphone"

    # --- Specs extraction ---

    def test_extract_ram(self):
        specs = self.normalizer._extract_specs("Samsung 12GB RAM 256GB", [])
        assert specs.get("ram_gb") == 12

    def test_extract_storage(self):
        specs = self.normalizer._extract_specs("iPhone 256GB Storage", [])
        assert specs.get("storage_gb") == 256

    def test_extract_camera(self):
        specs = self.normalizer._extract_specs("200MP Kamera Telefon", [])
        assert specs.get("camera_mp") == 200

    def test_extract_battery(self):
        specs = self.normalizer._extract_specs("5000mAh Batarya", [])
        assert specs.get("battery_mah") == 5000

    def test_extract_screen(self):
        specs = self.normalizer._extract_specs("6.8 inch AMOLED Ekran", [])
        assert specs.get("screen_size") == 6.8

    # --- Full normalization ---

    def test_normalize_one_full(self):
        item = {
            "title": "Samsung Galaxy S24 Ultra 12GB RAM 256GB",
            "extracted_price": 89999,
            "source": "Trendyol",
            "link": "https://example.com",
            "thumbnail": "https://example.com/img.jpg",
            "rating": 4.5,
            "reviews": 120,
            "extensions": [],
        }
        result = self.normalizer._normalize_one(item, "smartphone")
        assert result is not None
        assert result["brand"] == "Samsung"
        assert result["price_avg"] == 89999
        assert result["specs"]["ram_gb"] == 12

    def test_normalize_one_no_price(self):
        item = {"title": "Samsung Galaxy", "extensions": []}
        result = self.normalizer._normalize_one(item, "smartphone")
        assert result is None

    def test_normalize_results_filters_bad(self):
        items = [
            {"title": "Samsung Galaxy S24 Ultra", "extracted_price": 89999},
            {"title": "", "extracted_price": 50000},  # Empty title
            {"title": "Valid Product", "price": ""},  # No price
        ]
        results = self.normalizer.normalize_results(items, "smartphone")
        assert len(results) == 1
        assert results[0]["brand"] == "Samsung"
