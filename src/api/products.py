"""
Products API endpoints.
GET /api/v1/ai/products/{product_id}
GET /api/v1/ai/products/search
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from src.models.product import (
    ProductResponse,
    ProductIntelligence,
    ContextInfo,
    LLMHints,
    PricingInfo,
    ProductSpecs,
    UsageContextScores,
)
from src.pie import ProductIntelligenceEngine

router = APIRouter()
pie = ProductIntelligenceEngine()


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product_intelligence(
    product_id: str,
    format: str = Query("full", enum=["full", "summary", "minimal"]),
    include: Optional[list[str]] = Query(None),
    context: Optional[str] = Query(None, description="Usage context: gaming, student, photography, etc."),
):
    """
    Get AI-powered product intelligence.
    
    Returns detailed analysis including:
    - Product specifications (normalized)
    - Sentiment analysis from reviews
    - Usage context fit scores
    - Who should buy / avoid recommendations
    - Key strengths and weaknesses
    """
    try:
        # Generate product intelligence
        intelligence = await pie.analyze_product(product_id, context=context)
        
        # Build response
        response = ProductResponse(
            summary=intelligence.headline,
            data=intelligence,
            context=ContextInfo(
                methodology="aggregated-reviews-and-specs",
                confidence=0.85,
                data_freshness="2h",
            ),
            llm_hints=LLMHints(
                key_facts=[
                    f"{intelligence.specs.camera_mp}MP kamera" if intelligence.specs.camera_mp else None,
                    f"{intelligence.specs.ram_gb}GB RAM" if intelligence.specs.ram_gb else None,
                    f"Fiyat aralığı: ₺{intelligence.pricing.current_low:,} - ₺{intelligence.pricing.current_high:,}" if intelligence.pricing else None,
                ],
                comparison_context=f"Kategori: {intelligence.category}",
                actionable_insight=intelligence.verdict_text,
            ),
        )
        
        # Filter key_facts for None values
        response.llm_hints.key_facts = [f for f in response.llm_hints.key_facts if f]
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/search", response_model=dict)
async def search_products(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Search products with AI-enhanced results.
    
    Returns matching products with intelligence summaries.
    """
    try:
        # Search and analyze products
        results = await pie.search_products(q, category=category, limit=limit)
        
        return {
            "query": q,
            "category": category,
            "count": len(results),
            "results": results,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
