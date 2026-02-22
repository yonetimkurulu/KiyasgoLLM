"""
Shopping sync service.

Orchestrates: SerpApi search → normalize → upsert to DB.
"""
import structlog
from datetime import datetime, timezone

from src.shopping.client import ShoppingClient
from src.shopping.normalizer import ShoppingNormalizer
from src.db.session import SessionLocal
from src.db.models import Product, PriceHistory

logger = structlog.get_logger()

# Module-level instances
_client = None
_normalizer = ShoppingNormalizer()


def _get_client() -> ShoppingClient:
    global _client
    if _client is None:
        _client = ShoppingClient()
    return _client


def sync_category(category: str, num: int = 20) -> dict:
    """
    Sync products for a category from Google Shopping.

    Returns stats dict: {new, updated, skipped, errors}.
    """
    client = _get_client()
    stats = {"category": category, "new": 0, "updated": 0, "skipped": 0, "errors": 0}

    logger.info("Starting shopping sync", category=category)

    # Step 1: Search Google Shopping
    raw_results = client.search_category(category, num=num)
    if not raw_results:
        logger.warning("No shopping results", category=category)
        return stats

    # Step 2: Normalize
    products = _normalizer.normalize_results(raw_results, default_category=category)
    logger.info("Normalized products", category=category, count=len(products))

    # Step 3: Upsert to DB
    db = SessionLocal()
    try:
        for p_data in products:
            try:
                existing = db.query(Product).filter(Product.id == p_data["id"]).first()

                if existing:
                    # Update price info
                    existing.price_low = min(existing.price_low or p_data["price_avg"], p_data["price_low"])
                    existing.price_high = max(existing.price_high or p_data["price_avg"], p_data["price_high"])
                    existing.price_avg = p_data["price_avg"]
                    existing.updated_at = datetime.now(timezone.utc)
                    stats["updated"] += 1
                else:
                    # Create new product
                    product = Product(
                        id=p_data["id"],
                        name=p_data["name"],
                        brand=p_data["brand"],
                        category=p_data["category"],
                        price_low=p_data.get("price_low"),
                        price_high=p_data.get("price_high"),
                        price_avg=p_data.get("price_avg"),
                        currency=p_data.get("currency", "TRY"),
                        specs=p_data.get("specs", {}),
                        headline=f"{p_data['brand']} {p_data['name'][:50]}",
                    )
                    db.add(product)
                    stats["new"] += 1

                # Record price history
                price_entry = PriceHistory(
                    product_id=p_data["id"],
                    price=p_data["price_avg"],
                    currency=p_data.get("currency", "TRY"),
                    recorded_at=datetime.now(timezone.utc),
                )
                db.add(price_entry)

            except Exception as e:
                logger.warning("Failed to upsert product", id=p_data.get("id"), error=str(e))
                stats["errors"] += 1

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Sync commit failed", category=category, error=str(e))
        stats["errors"] += 1
    finally:
        db.close()

    logger.info("Shopping sync complete", **stats)
    return stats


def sync_all(num: int = 20) -> list[dict]:
    """
    Sync all default categories.

    Returns list of stats dicts.
    """
    categories = ["smartphone", "laptop", "tablet"]
    all_stats = []

    for cat in categories:
        stats = sync_category(cat, num=num)
        all_stats.append(stats)

    total_new = sum(s["new"] for s in all_stats)
    total_updated = sum(s["updated"] for s in all_stats)
    logger.info(
        "Full sync complete",
        categories=len(categories),
        total_new=total_new,
        total_updated=total_updated,
    )
    return all_stats
