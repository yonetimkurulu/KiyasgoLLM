"""
Streaming Chat API Endpoint
Gelişmiş chat endpoint - streaming, memory, context-aware.
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel
import json
import asyncio

from src.llm.advanced_provider import get_advanced_llm
from src.llm.memory import get_memory
from src.pie import ProductIntelligenceEngine
from src.cse import CommerceSignalEngine
from src.security.sanitizer import sanitize_user_input, validate_product_id

router = APIRouter()
llm = get_advanced_llm()
memory = get_memory()
pie = ProductIntelligenceEngine()
cse = CommerceSignalEngine()


class ChatRequest(BaseModel):
    """Chat request body."""
    message: str
    conversation_id: Optional[str] = None
    context: Optional[str] = None  # gaming, shopping, comparison
    product_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response."""
    response: str
    conversation_id: str
    sources: list[str] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with AI assistant.
    """
    conversation_id = request.conversation_id or _generate_id()
    
    # Process request (Sanitize, Validate, Build Prompt)
    safe_data, prompt = await _prepare_chat_context(request, conversation_id)
    
    # Generate response
    response = await llm.generate(
        prompt=prompt,
        system_prompt=_get_system_prompt(request.context),
        temperature=0.7,
    )
    
    # Save to memory
    memory.add_exchange(conversation_id, request.message, response.content)
    
    return ChatResponse(
        response=response.content,
        conversation_id=conversation_id,
        sources=[response.provider],
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response.
    """
    conversation_id = request.conversation_id or _generate_id()
    
    # Process request (Sanitize, Validate, Build Prompt)
    safe_data, prompt = await _prepare_chat_context(request, conversation_id)
    
    async def generate():
        full_response = []
        async for chunk in llm.stream(
            prompt=prompt,
            system_prompt=_get_system_prompt(request.context),
        ):
            full_response.append(chunk)
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Save complete response to memory
        complete = "".join(full_response)
        memory.add_exchange(conversation_id, request.message, complete)
        
        yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


@router.post("/chat/analyze")
async def analyze_product(
    product_id: str = Query(..., description="Product ID to analyze"),
    question: Optional[str] = Query(None, description="Specific question"),
):
    """
    Analyze a product with AI.
    
    Returns structured analysis.
    """
    # Get product intelligence
    intel = await pie.analyze_product(product_id)
    
    # Get commerce signals
    signals = await cse.analyze_product(product_id)
    
    price_text = f"TL{intel.pricing.average:,}" if intel.pricing else "Bilinmiyor"
    
    # Build analysis prompt
    context = f"""
Ürün: {intel.name}
Kategori: {intel.category}
Fiyat: {price_text}
Özellikler: {intel.specs.chipset}, {intel.specs.ram_gb}GB RAM, {intel.specs.camera_mp}MP kamera

Güçlü: {', '.join([s['point'] for s in intel.key_strengths[:3]])}
Zayıf: {', '.join([w['point'] for w in intel.key_weaknesses[:2]])}

Ticari Sinyaller:
- Güvenlik Skoru: {signals.buy_safety}/100
- Genel: {signals.overall}
"""
    
    if question:
        prompt = f"{context}\n\nSoru: {question}"
    else:
        prompt = f"{context}\n\nBu ürün hakkında kısa bir analiz yap."
    
    # Generate with structured output
    schema = {
        "ozet": "Tek cümle özet",
        "puan": "1-10 arası puan",
        "oneri": "Alınmalı/Beklenmeli/Alternatif bakılmalı",
        "neden": "Kısa açıklama"
    }
    
    result = await llm.generate_structured(prompt, schema)
    
    return {
        "product_id": product_id,
        "analysis": result,
        "intelligence": {
            "verdict_score": intel.verdict_score,
            "best_for": intel.best_for,
        },
        "signals": {
            "buy_safety": signals.buy_safety,
            "overall": signals.overall,
        }
    }


async def _prepare_chat_context(request: ChatRequest, conversation_id: str) -> tuple[dict, str]:
    """Helper to prepare chat context: sanitize, validate, and build prompt."""
    # Get conversation history
    history_context = memory.get_context(conversation_id)
    
    # Sanitize inputs
    safe_message = sanitize_user_input(request.message)
    safe_context = sanitize_user_input(request.context) if request.context else None
    
    # Validate product_id if present
    if request.product_id:
        try:
            validate_product_id(request.product_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Build enhanced prompt
    prompt = await _build_context_prompt(
        message=safe_message,
        history=history_context,
        context=safe_context,
        product_id=request.product_id,
    )
    
    return {
        "message": safe_message,
        "context": safe_context,
        "product_id": request.product_id
    }, prompt


async def _build_context_prompt(
    message: str,
    history: str,
    context: Optional[str],
    product_id: Optional[str],
) -> str:
    """Build enhanced prompt with context."""
    parts = []
    
    # Add product context if available
    if product_id:
        try:
            intel = await pie.analyze_product(product_id)
            parts.append(f"[Ürün Bağlamı: {intel.name} - {intel.headline}]")
        except:
            pass
    
    # Add conversation history
    if history:
        parts.append(f"[Önceki Konuşma]\n{history}\n[/Önceki Konuşma]")
    
    # Add user message
    parts.append(f"Kullanıcı: {message}")
    
    return "\n\n".join(parts)


def _get_system_prompt(context: Optional[str]) -> str:
    """Get context-specific system prompt."""
    base = """Sen KıyasGO AI asistanısın. Türkiye'nin akıllı alışveriş platformu için çalışıyorsun.

Kurallar:
- Her zaman Türkçe yanıt ver
- Kısa ve öz ol
- Fiyatları TL ile göster
- Tarafsız ve objektif ol"""
    
    if context == "gaming":
        base += "\n\nOdak: Oyun performansı, GPU, FPS, soğutma sistemi."
    elif context == "photography":
        base += "\n\nOdak: Kamera kalitesi, sensör boyutu, video özellikleri."
    elif context == "comparison":
        base += "\n\nOdak: Ürünleri karşılaştır, artı/eksileri listele."
    elif context == "shopping":
        base += "\n\nOdak: Fiyat, değer, satın alma zamanlaması."
    
    return base


def _generate_id() -> str:
    """Generate unique conversation ID (12 chars)."""
    import uuid
    return str(uuid.uuid4())[:12]
