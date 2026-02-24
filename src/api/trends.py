"""
Market Trends API endpoint.
GET /api/v1/ai/market/trends
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import structlog

from src.cse import CommerceSignalEngine

logger = structlog.get_logger()
router = APIRouter()
cse = CommerceSignalEngine()


@router.get("/market/trends")
async def get_market_trends(
    category: str = Query(..., description="Product category (smartphone, laptop, tablet)"),
    period: int = Query(30, ge=7, le=365, description="Analysis period in days"),
):
    """
    Get market trends and signals for a product category.

    Returns:
    - Average market signals
    - Price movement trends
    - Category-wide risk indicators
    - Buying timing insights
    """
    try:
        trends = await cse.get_market_trends(category, period=period)

        return {
            "category": category,
            "period_days": period,
            "trends": trends,
            "source": "kiyasgo.com",
            "citation": "KıyasGO Commerce Intelligence",
        }
    except Exception as e:
        logger.error("Market trends request failed", category=category, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
