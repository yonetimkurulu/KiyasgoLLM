"""
SerpApi Google Shopping client.

Wraps the SerpApi library to search Google Shopping for Turkish market products.
"""
import structlog
from typing import Optional
from serpapi import GoogleSearch

from src.config import get_settings

logger = structlog.get_logger()


class ShoppingClient:
    """Google Shopping search via SerpApi."""

    # Default search queries per category
    CATEGORY_QUERIES = {
        "smartphone": [
            "en iyi akilli telefon 2024",
            "samsung galaxy flagship",
            "iphone pro",
            "xiaomi flagship telefon",
        ],
        "laptop": [
            "en iyi laptop 2024",
            "gaming laptop",
            "macbook pro",
            "ultrabook",
        ],
        "tablet": [
            "en iyi tablet 2024",
            "ipad pro",
            "samsung galaxy tab",
        ],
    }

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.serpapi_api_key

    def search(
        self,
        query: str,
        gl: Optional[str] = None,
        hl: Optional[str] = None,
        num: int = 20,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
    ) -> dict:
        """
        Search Google Shopping via SerpApi.

        Args:
            query: Search query string
            gl: Country code (default: config value, typically 'tr')
            hl: Language code (default: config value, typically 'tr')
            num: Number of results (max 100)
            price_min: Minimum price filter
            price_max: Maximum price filter

        Returns:
            Raw SerpApi response as dict
        """
        if not self.api_key:
            logger.warning("SerpApi API key not configured, returning empty results")
            return {"shopping_results": []}

        params = {
            "engine": "google_shopping",
            "q": query,
            "gl": gl or self.settings.serpapi_gl,
            "hl": hl or self.settings.serpapi_hl,
            "num": min(num, 100),
            "api_key": self.api_key,
        }

        if price_min is not None:
            params["price_min"] = price_min
        if price_max is not None:
            params["price_max"] = price_max

        logger.info("SerpApi search", query=query, gl=params["gl"], num=num)

        try:
            search = GoogleSearch(params)
            results = search.get_dict()

            result_count = len(results.get("shopping_results", []))
            logger.info("SerpApi results received", query=query, count=result_count)

            return results

        except Exception as e:
            logger.error("SerpApi search failed", query=query, error=str(e))
            return {"shopping_results": [], "error": str(e)}

    def search_category(self, category: str, num: int = 20) -> list[dict]:
        """
        Search Google Shopping for all queries in a category.

        Returns combined list of shopping_results from all queries.
        """
        queries = self.CATEGORY_QUERIES.get(category.lower(), [])
        if not queries:
            logger.warning("Unknown category for shopping search", category=category)
            queries = [f"en iyi {category} 2024"]

        all_results = []
        seen_ids = set()

        for query in queries:
            response = self.search(query, num=num)
            for item in response.get("shopping_results", []):
                # Deduplicate by title
                title_key = item.get("title", "").lower().strip()
                if title_key and title_key not in seen_ids:
                    seen_ids.add(title_key)
                    all_results.append(item)

        logger.info(
            "Category search complete",
            category=category,
            total_results=len(all_results),
            queries_used=len(queries),
        )
        return all_results
