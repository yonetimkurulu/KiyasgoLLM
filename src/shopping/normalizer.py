"""
Shopping result normalizer.

Converts raw SerpApi Google Shopping results into DB-compatible Product dicts.
"""
import re
import structlog
from typing import Optional

logger = structlog.get_logger()


class ShoppingNormalizer:
    """Normalizes SerpApi Google Shopping results into Product format."""

    # Brand detection keywords
    KNOWN_BRANDS = {
        "samsung", "apple", "iphone", "xiaomi", "huawei", "oppo", "vivo",
        "oneplus", "google", "pixel", "sony", "lg", "motorola", "realme",
        "asus", "lenovo", "dell", "hp", "msi", "acer", "macbook", "ipad",
        "microsoft", "surface", "nothing", "honor", "redmi", "poco",
    }

    # Category detection from title
    CATEGORY_KEYWORDS = {
        "smartphone": ["telefon", "phone", "cep", "akilli"],
        "laptop": ["laptop", "notebook", "dizustu", "macbook"],
        "tablet": ["tablet", "ipad", "tab"],
        "headphone": ["kulaklik", "earbuds", "headphone"],
        "watch": ["saat", "watch", "band"],
    }

    def normalize_results(
        self,
        raw_results: list[dict],
        default_category: str = "smartphone",
    ) -> list[dict]:
        """
        Normalize a list of raw SerpApi shopping results into Product dicts.

        Returns list of dicts ready for DB upsert.
        """
        normalized = []
        for item in raw_results:
            try:
                product = self._normalize_one(item, default_category)
                if product:
                    normalized.append(product)
            except Exception as e:
                logger.warning(
                    "Failed to normalize shopping result",
                    title=item.get("title", "?"),
                    error=str(e),
                )
        return normalized

    def _normalize_one(self, item: dict, default_category: str) -> Optional[dict]:
        """Normalize a single shopping result."""
        title = item.get("title", "").strip()
        if not title or len(title) < 5:
            return None

        # Extract price
        price = self._parse_price(item)
        if not price:
            return None

        # Generate slug ID
        product_id = self._slugify(title)
        if not product_id or len(product_id) < 3:
            return None

        # Extract brand
        brand = self._detect_brand(title)

        # Detect category
        category = self._detect_category(title, default_category)

        # Extract specs from title/extensions
        specs = self._extract_specs(title, item.get("extensions", []))

        # Extract source/store
        source = item.get("source", "")

        return {
            "id": product_id,
            "name": title,
            "brand": brand,
            "category": category,
            "price_low": price,
            "price_high": price,
            "price_avg": price,
            "currency": "TRY",
            "specs": specs,
            "source": source,
            "thumbnail": item.get("thumbnail", ""),
            "link": item.get("link", ""),
            "rating": item.get("rating"),
            "reviews_count": item.get("reviews", 0),
        }

    def _parse_price(self, item: dict) -> Optional[int]:
        """Parse price from SerpApi result. Returns price in smallest unit (kurus)."""
        # Try extracted_price first
        price_str = item.get("extracted_price")
        if price_str is not None:
            try:
                return int(float(price_str))
            except (ValueError, TypeError):
                pass

        # Try price string
        price_str = item.get("price", "")
        if not price_str:
            return None

        # Remove currency symbols, spaces, dots (thousands sep), replace comma with dot
        cleaned = price_str.replace("TL", "").replace("TRY", "").replace("$", "")
        cleaned = cleaned.replace("\xa0", "").strip()

        # Handle Turkish format: 85.999,00 or 85999
        if "," in cleaned and "." in cleaned:
            # 85.999,00 format
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            # 85999,00 format
            cleaned = cleaned.replace(",", ".")
        elif cleaned.count(".") > 1:
            # 85.999.00 → remove all dots
            cleaned = cleaned.replace(".", "")

        try:
            return int(float(cleaned))
        except (ValueError, TypeError):
            return None

    def _slugify(self, title: str) -> str:
        """Generate a URL-friendly slug from product title."""
        # Lowercase and normalize
        slug = title.lower().strip()
        # Remove parenthetical info
        slug = re.sub(r"\(.*?\)", "", slug)
        # Turkish chars
        tr_map = str.maketrans("cgsiouu", "cgsiouu", "")
        slug = slug.translate(tr_map)
        # Keep only alphanumeric and spaces
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        # Replace whitespace with hyphens
        slug = re.sub(r"\s+", "-", slug.strip())
        # Remove consecutive hyphens
        slug = re.sub(r"-+", "-", slug)
        # Trim to reasonable length
        return slug[:80].rstrip("-")

    def _detect_brand(self, title: str) -> str:
        """Detect brand from product title."""
        title_lower = title.lower()
        for brand in self.KNOWN_BRANDS:
            if brand in title_lower:
                # Special cases
                if brand == "iphone":
                    return "Apple"
                if brand == "macbook":
                    return "Apple"
                if brand == "ipad":
                    return "Apple"
                if brand == "pixel":
                    return "Google"
                if brand == "surface":
                    return "Microsoft"
                if brand == "redmi" or brand == "poco":
                    return "Xiaomi"
                return brand.title()
        return "Unknown"

    def _detect_category(self, title: str, default: str) -> str:
        """Detect product category from title."""
        title_lower = title.lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in title_lower:
                    return category
        return default

    def _extract_specs(self, title: str, extensions: list) -> dict:
        """Extract specs from title and extensions."""
        specs = {}
        combined = f"{title} {' '.join(extensions) if extensions else ''}"
        combined_lower = combined.lower()

        # RAM
        ram_match = re.search(r"(\d+)\s*gb\s*ram", combined_lower)
        if ram_match:
            specs["ram_gb"] = int(ram_match.group(1))

        # Storage
        storage_match = re.search(r"(\d+)\s*(?:gb|tb)\s*(?:ssd|storage|depolama|hafiza)", combined_lower)
        if not storage_match:
            storage_match = re.search(r"(\d+)\s*gb(?!\s*ram)", combined_lower)
        if storage_match:
            val = int(storage_match.group(1))
            if val >= 32 and val != specs.get("ram_gb"):
                specs["storage_gb"] = val

        # Screen size
        screen_match = re.search(r"(\d+[.,]\d+)\s*(?:inc|inch|\")", combined_lower)
        if screen_match:
            specs["screen_size"] = float(screen_match.group(1).replace(",", "."))

        # Camera MP
        cam_match = re.search(r"(\d+)\s*mp", combined_lower)
        if cam_match:
            specs["camera_mp"] = int(cam_match.group(1))

        # Battery
        bat_match = re.search(r"(\d{4,5})\s*mah", combined_lower)
        if bat_match:
            specs["battery_mah"] = int(bat_match.group(1))

        # Chipset keywords
        chipset_keywords = [
            "snapdragon", "dimensity", "exynos", "helio",
            "a18", "a17", "a16", "a15", "m4", "m3", "m2", "m1",
            "ryzen", "core i", "core ultra",
        ]
        for chip in chipset_keywords:
            if chip in combined_lower:
                # Find the full chipset name (chip + following words)
                chip_match = re.search(
                    rf"({re.escape(chip)}[\w\s]*?)(?:\s*[,|/]|\s+(?:ram|gb|mp|mah|inc)|\s*$)",
                    combined_lower,
                )
                if chip_match:
                    specs["chipset"] = chip_match.group(1).strip().title()
                    break

        return specs
