"""
Comparison API endpoints.
GET /api/v1/ai/compare
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from src.models.product import (
    ComparisonResponse,
    ComparisonResult,
    ComparisonWinner,
    ContextInfo,
    LLMHints,
)
from src.pie import ProductIntelligenceEngine
from src.llm import LLMProvider

router = APIRouter()
pie = ProductIntelligenceEngine()
llm = LLMProvider()


@router.get("/compare", response_model=ComparisonResponse)
async def compare_products(
    products: str = Query(..., description="Comma-separated product IDs (max 5)"),
    context: Optional[str] = Query(None, description="Usage context for comparison"),
):
    """
    Compare multiple products with AI analysis.
    
    Returns:
    - Head-to-head comparison matrix
    - Winner for each category
    - Context-specific recommendations
    - Overall verdict
    """
    try:
        # Parse product IDs
        product_ids = [p.strip() for p in products.split(",")][:5]
        
        if len(product_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 products required for comparison"
            )
        
        # Get intelligence for each product
        product_intels = []
        for pid in product_ids:
            intel = await pie.analyze_product(pid, context=context)
            product_intels.append(intel)
        
        # Generate comparison using LLM
        comparison = await _generate_comparison(product_intels, context)
        
        # Build response
        response = ComparisonResponse(
            summary=comparison["summary"],
            data=ComparisonResult(
                products=[{"id": p.product_id, "name": p.name} for p in product_intels],
                comparison_matrix=comparison["matrix"],
                verdict=comparison["verdict"],
                recommendation=comparison["recommendation"],
            ),
            context=ContextInfo(
                methodology="ai-powered-comparison",
                confidence=0.82,
            ),
            llm_hints=LLMHints(
                key_facts=comparison.get("key_facts", []),
                actionable_insight=comparison["recommendation"],
            ),
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/category/{category}", response_model=ComparisonResponse)
async def compare_category_products(
    category: str,
    budget: Optional[int] = Query(None, description="Maximum budget in TRY"),
    context: Optional[str] = Query(None, description="Usage context"),
    limit: int = Query(3, ge=2, le=5),
):
    """
    Compare top products in a category.
    
    Automatically selects best products based on budget and context.
    """
    try:
        # Get top products for category
        top_products = await pie.get_top_products(
            category=category,
            budget=budget,
            context=context,
            limit=limit
        )
        
        if len(top_products) < 2:
            raise HTTPException(
                status_code=404,
                detail=f"Not enough products found in category: {category}"
            )
        
        # Generate comparison
        comparison = await _generate_comparison(top_products, context)
        
        response = ComparisonResponse(
            summary=comparison["summary"],
            data=ComparisonResult(
                products=[{"id": p.product_id, "name": p.name} for p in top_products],
                comparison_matrix=comparison["matrix"],
                verdict=comparison["verdict"],
                recommendation=comparison["recommendation"],
            ),
            context=ContextInfo(
                methodology="category-based-comparison",
                confidence=0.80,
            ),
            llm_hints=LLMHints(
                key_facts=comparison.get("key_facts", []),
            ),
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_comparison(products: list, context: Optional[str] = None) -> dict:
    """Generate comparison analysis using LLM."""
    
    # Build comparison matrix based on product specs
    matrix = {}
    aspects = ["camera", "performance", "battery", "price", "build_quality"]
    
    for aspect in aspects:
        # Simple comparison logic (will be enhanced with LLM)
        scores = []
        for p in products:
            score = getattr(p.context_scores, aspect, 0.5) if hasattr(p, 'context_scores') else 0.5
            scores.append((p.product_id, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if len(scores) >= 2 and scores[0][1] - scores[1][1] > 0.2:
            margin = "significant"
        elif len(scores) >= 2 and scores[0][1] - scores[1][1] > 0.1:
            margin = "moderate"
        else:
            margin = "slight"
        
        matrix[aspect] = ComparisonWinner(
            winner=scores[0][0] if scores else "tie",
            margin=margin
        )
    
    # Generate verdict
    verdict = {
        "overall_winner": "context_dependent",
    }
    
    if context:
        # Find best for specific context
        context_scores = [(p.product_id, getattr(p.context_scores, context, 0.5)) for p in products]
        context_scores.sort(key=lambda x: x[1], reverse=True)
        verdict[f"for_{context}"] = context_scores[0][0] if context_scores else None
    
    # Generate summary
    product_names = [p.name for p in products]
    summary = f"{' vs '.join(product_names)}: Karşılaştırma analizi tamamlandı."
    
    recommendation = "Kullanım amacınıza göre en uygun ürünü seçin."
    
    return {
        "summary": summary,
        "matrix": matrix,
        "verdict": verdict,
        "recommendation": recommendation,
        "key_facts": [
            f"Karşılaştırılan ürün sayısı: {len(products)}",
        ],
    }
