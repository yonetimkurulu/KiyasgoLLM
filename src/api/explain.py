"""
Explain Recommendation API endpoint.
GET /api/v1/ai/explain/recommendation/{product_id}
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from src.pie import ProductIntelligenceEngine
from src.cse import CommerceSignalEngine
from src.llm.advanced_provider import get_advanced_llm

router = APIRouter()
pie = ProductIntelligenceEngine()
cse = CommerceSignalEngine()
llm = get_advanced_llm()


@router.get("/explain/recommendation/{product_id}")
async def explain_recommendation(
    product_id: str,
    context: Optional[str] = Query(None, description="Usage context: gaming, photography, student, etc."),
):
    """
    Explain why a product is recommended (or not) for a given context.

    Combines PIE intelligence and CSE signals into a human-readable
    explanation powered by LLM.
    """
    try:
        # Gather intelligence
        intel = await pie.analyze_product(product_id, context=context)
        signals = await cse.analyze_product(product_id)

        # Build explanation prompt
        context_label = context or "genel kullanım"
        prompt = f"""Aşağıdaki ürün verilerine dayanarak, bu ürünün "{context_label}" için neden önerilip önerilmediğini kısaca açıkla.

Ürün: {intel.name}
Kategori: {intel.category}
Headline: {intel.headline}
Verdict Score: {intel.verdict_score}/10

Güçlü Yönler: {', '.join([s['point'] for s in intel.key_strengths[:3]])}
Zayıf Yönler: {', '.join([w['point'] for w in intel.key_weaknesses[:2]])}

Best For: {', '.join(intel.best_for)}
Avoid For: {', '.join(intel.avoid_for)}

Ticari Sinyaller:
- Satın Alma Güvenliği: {signals.buy_safety}/100
- Değer Skoru: {signals.value_score}/100
- Zamanlama: {signals.timing_score}/100
- Genel: {signals.overall}

3-4 cümlelik, Türkçe, objektif bir açıklama yaz."""

        response = await llm.generate(
            prompt=prompt,
            system_prompt="Sen KıyasGO AI asistanısın. Kısa, net ve objektif açıklamalar yap. Türkçe yanıt ver.",
            temperature=0.5,
        )

        return {
            "product_id": product_id,
            "context": context_label,
            "explanation": response.content,
            "data": {
                "verdict_score": intel.verdict_score,
                "best_for": intel.best_for,
                "avoid_for": intel.avoid_for,
                "buy_safety": signals.buy_safety,
                "overall_signal": signals.overall,
            },
            "source": "kiyasgo.com",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
