"""
Shopping API endpoints.
POST /api/v1/ai/shopping/sync
GET  /api/v1/ai/shopping/search
GET  /api/v1/ai/shopping/status
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import structlog

from src.shopping.client import ShoppingClient
from src.shopping.sync import sync_category, sync_all
from src.db.session import SessionLocal
from src.db.models import Product

logger = structlog.get_logger()
router = APIRouter()


@router.get("/shopping/search", response_model=dict)
async def shopping_search(
    q: str = Query(..., description="Search query for Google Shopping"),
    category: Optional[str] = Query(None, description="Product category filter"),
    num: int = Query(10, ge=1, le=50, description="Number of results"),
):
    """
    Live search on Google Shopping via SerpApi.

    Returns raw shopping results without DB persistence.
    """
    try:
        client = ShoppingClient()
        results = client.search(q, num=num)
        shopping_results = results.get("shopping_results", [])

        # Simplify for response
        items = []
        for r in shopping_results[:num]:
            items.append({
                "title": r.get("title", ""),
                "price": r.get("price", ""),
                "extracted_price": r.get("extracted_price"),
                "source": r.get("source", ""),
                "link": r.get("link", ""),
                "thumbnail": r.get("thumbnail", ""),
                "rating": r.get("rating"),
                "reviews": r.get("reviews", 0),
                "extensions": r.get("extensions", []),
            })

        return {
            "query": q,
            "count": len(items),
            "results": items,
        }

    except Exception as e:
        logger.error("Shopping search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shopping/sync", response_model=dict)
async def trigger_sync(
    category: Optional[str] = Query(None, description="Category to sync (default: all)"),
    num: int = Query(20, ge=5, le=50, description="Products per query"),
):
    """
    Trigger Google Shopping sync.

    Fetches products from Google Shopping and upserts to database.
    """
    try:
        if category:
            stats = sync_category(category, num=num)
            return {"synced": [stats]}
        else:
            all_stats = sync_all(num=num)
            return {"synced": all_stats}

    except Exception as e:
        logger.error("Shopping sync failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shopping/status", response_model=dict)
async def shopping_status():
    """
    Get shopping sync status.

    Returns product counts and last update times.
    """
    db = SessionLocal()
    try:
        total = db.query(Product).count()

        categories = {}
        for cat in ["smartphone", "laptop", "tablet"]:
            count = db.query(Product).filter(Product.category == cat).count()
            latest = (
                db.query(Product)
                .filter(Product.category == cat)
                .order_by(Product.updated_at.desc())
                .first()
            )
            categories[cat] = {
                "count": count,
                "last_updated": str(latest.updated_at) if latest and latest.updated_at else None,
            }

        return {
            "total_products": total,
            "categories": categories,
        }

    finally:
        db.close()
