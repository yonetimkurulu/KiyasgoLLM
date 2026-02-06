"""
Signals API endpoints.
GET /api/v1/ai/signals/{product_id}
GET /api/v1/ai/market/trends
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from src.models.product import (
    SignalsResponse,
    CommerceSignals,
    ContextInfo,
    LLMHints,
)
from src.cse import CommerceSignalEngine

router = APIRouter()
cse = CommerceSignalEngine()


@router.get("/signals/{product_id}", response_model=SignalsResponse)
async def get_product_signals(
    product_id: str,
    seller_id: Optional[str] = Query(None, description="Specific seller ID"),
):
    """
    Get commerce signals for a product.
    
    Signals include:
    - fake_discount: Sahte indirim tespiti (0-100 risk skoru)
    - store_reliability: Satıcı güvenilirliği
    - price_volatility: Fiyat oynaklığı
    - lifecycle: Ürün yaşam döngüsü aşaması
    - supply_risk: Tedarik riski
    
    Returns composite buy safety and timing scores.
    """
    try:
        # Generate signals
        signals = await cse.analyze_product(product_id, seller_id=seller_id)
        
        # Generate summary based on signals
        warnings = []
        tips = []
        
        if signals.fake_discount.is_fake:
            warnings.append("Bu indirim gerçeği yansıtmıyor olabilir")
        
        if signals.store_reliability.tier == "trusted":
            tips.append("Güvenilir satıcı")
        elif signals.store_reliability.tier == "caution":
            warnings.append("Satıcı dikkatle değerlendirilmeli")
        
        if signals.price_volatility.recommendation == "wait":
            tips.append("Fiyat düşüş trendinde, beklemek mantıklı")
        
        summary = f"{product_id}: "
        if signals.overall == "safe":
            summary += "Güvenli alışveriş"
        elif signals.overall == "proceed_with_caution":
            summary += "Dikkatli olunmalı"
        else:
            summary += "Risk değerlendirmesi yapıldı"
        
        response = SignalsResponse(
            summary=summary,
            data=signals,
            context=ContextInfo(
                methodology="commerce-signal-analysis",
                confidence=0.85,
                data_freshness="2h",
            ),
            llm_hints=LLMHints(
                key_facts=[
                    f"Sahte indirim riski: {'Yüksek' if signals.fake_discount.score > 50 else 'Düşük'}",
                    f"Satıcı güvenilirliği: {signals.store_reliability.tier}",
                    f"Fiyat trendi: {signals.price_volatility.trend}",
                    f"Ürün aşaması: {signals.lifecycle.stage}",
                ],
                actionable_insight=tips[0] if tips else (warnings[0] if warnings else "Normal alışveriş koşulları"),
            ),
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/trends", response_model=dict)
async def get_market_trends(
    category: str = Query(..., description="Product category"),
    period: int = Query(30, description="Period in days", ge=7, le=90),
):
    """
    Get market trends for a category.
    
    Returns:
    - Price trend (average, min, max over period)
    - Popular products
    - Supply situation
    - Upcoming releases
    """
    try:
        trends = await cse.get_market_trends(category, period)
        
        return {
            "category": category,
            "period_days": period,
            "trends": trends,
            "generated_at": "2025-01-28T14:00:00Z",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/category/{category}", response_model=dict)
async def get_category_signals(
    category: str,
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get signals summary for all products in a category.
    
    Returns aggregated risk indicators and opportunities.
    """
    try:
        signals = await cse.get_category_signals(category, limit)
        
        return {
            "category": category,
            "count": len(signals),
            "signals": signals,
            "summary": {
                "avg_fake_discount_risk": sum(s.get("fake_discount_score", 0) for s in signals) / max(len(signals), 1),
                "avg_store_reliability": sum(s.get("store_reliability_score", 0) for s in signals) / max(len(signals), 1),
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
