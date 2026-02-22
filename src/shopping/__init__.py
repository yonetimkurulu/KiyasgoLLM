"""
Google Shopping integration via SerpApi.
"""
from src.shopping.client import ShoppingClient
from src.shopping.normalizer import ShoppingNormalizer
from src.shopping.sync import sync_category, sync_all

__all__ = ["ShoppingClient", "ShoppingNormalizer", "sync_category", "sync_all"]
