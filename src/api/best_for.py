"""
Best-For API endpoints.
GET /api/v1/ai/best-for/{context}
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import structlog

from src.models.product import (
    BestForResponse,
    BestForResult,
    BestForQuery,
    RecommendedProduct,
    ContextInfo,
    LLMHints,
)
from src.recommendation import RecommendationEngine

logger = structlog.get_logger()
router = APIRouter()
recommendation_engine = RecommendationEngine()


@router.get("/best-for/{context}", response_model=BestForResponse)
async def get_best_for(
    context: str,
    category: str = Query(..., description="Product category (laptop, phone, tablet, etc.)"),
    budget: Optional[int] = Query(None, description="Maximum budget in TRY"),
    limit: int = Query(5, ge=1, le=10),
):
    """
    Get best products for a specific use case.
    
    Contexts:
    - gaming: Oyun performansı öncelikli
    - photography: Kamera kalitesi öncelikli
    - student: Uygun fiyat + taşınabilirlik
    - business: Güvenilirlik + profesyonel özellikler
    - budget: En iyi fiyat/performans
    - creator: İçerik üretimi için
    - long_term: Uzun vadeli kullanım
    
    Returns ranked product recommendations with explanations.
    """
    try:
        # Validate context
        valid_contexts = ["gaming", "photography", "student", "business", "budget", "creator", "long_term"]
        if context not in valid_contexts:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid context. Valid contexts: {', '.join(valid_contexts)}"
            )
        
        # Get recommendations
        recommendations = await recommendation_engine.get_best_for(
            context=context,
            category=category,
            budget=budget,
            limit=limit
        )
        
        # Build query info
        query = BestForQuery(
            context=context,
            category=category,
            budget=budget,
        )
        
        # Generate summary
        if budget:
            summary = f"TL{budget:,} bütçeyle {context} için en iyi {category}: {recommendations[0].name if recommendations else 'Bulunamadı'}"
        else:
            summary = f"{context.title()} için en iyi {category}: {recommendations[0].name if recommendations else 'Bulunamadı'}"
        
        response = BestForResponse(
            summary=summary,
            data=BestForResult(
                query=query,
                recommendations=recommendations,
                methodology=f"{context} context scoring + price/performance ratio"
            ),
            context=ContextInfo(
                methodology="context-based-recommendation",
                confidence=0.88,
            ),
            llm_hints=LLMHints(
                key_facts=[
                    f"Önerilen ürün sayısı: {len(recommendations)}",
                    f"Kullanım amacı: {context}",
                    f"Kategori: {category}",
                ],
                actionable_insight=f"En uygun seçim: {recommendations[0].name}" if recommendations else None,
            ),
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Best-for recommendation failed", context=context, category=category, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/best-for", response_model=dict)
async def list_contexts():
    """
    List available usage contexts for best-for recommendations.
    """
    return {
        "contexts": [
            {"id": "gaming", "name": "Oyun", "description": "Yüksek GPU ve ekran yenileme hızı öncelikli"},
            {"id": "photography", "name": "Fotoğrafçılık", "description": "Kamera kalitesi ve sensör boyutu öncelikli"},
            {"id": "student", "name": "Öğrenci", "description": "Uygun fiyat, taşınabilirlik ve batarya ömrü"},
            {"id": "business", "name": "İş", "description": "Güvenilirlik, güvenlik özellikleri ve dayanıklılık"},
            {"id": "budget", "name": "Bütçe Dostu", "description": "En iyi fiyat/performans oranı"},
            {"id": "creator", "name": "İçerik Üretici", "description": "Ekran doğruluğu, performans ve bağlantı portları"},
            {"id": "long_term", "name": "Uzun Vadeli", "description": "Güncelleme politikası, yapı kalitesi ve tamir edilebilirlik"},
        ]
    }
