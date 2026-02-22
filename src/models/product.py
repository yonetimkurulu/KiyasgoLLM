"""
Pydantic models for KıyasGO AI Intelligence Service.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


# ===== Common Models =====

class ContextInfo(BaseModel):
    """Metadata about how data was generated."""
    methodology: str = "aggregated-reviews-and-specs"
    confidence: float = Field(ge=0, le=1, default=0.85)
    data_freshness: str = "2h"
    limitations: list[str] = []


class LLMHints(BaseModel):
    """Hints for LLM consumption."""
    key_facts: list[str] = []
    comparison_context: Optional[str] = None
    actionable_insight: Optional[str] = None


class BaseResponse(BaseModel):
    """Base response structure for all API endpoints."""
    version: str = "1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "kiyasgo.com"
    citation: str = "KıyasGO Commerce Intelligence"


# ===== Product Models =====

class PricingInfo(BaseModel):
    """Product pricing information."""
    current_low: int
    current_high: int
    average: int
    currency: str = "TRY"
    trend: str = "stable"  # rising, stable, declining
    buy_signal: str = "neutral"  # buy_now, wait, neutral


class ProductSpecs(BaseModel):
    """Normalized product specifications."""
    screen_size: Optional[float] = None
    screen_type: Optional[str] = None
    chipset: Optional[str] = None
    chipset_tier: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    battery_mah: Optional[int] = None
    camera_mp: Optional[int] = None
    weight_grams: Optional[int] = None
    extra: dict = {}


class UsageContextScores(BaseModel):
    """Scores for different usage contexts."""
    gaming: float = Field(ge=0, le=1, default=0.5)
    photography: float = Field(ge=0, le=1, default=0.5)
    student: float = Field(ge=0, le=1, default=0.5)
    business: float = Field(ge=0, le=1, default=0.5)
    budget: float = Field(ge=0, le=1, default=0.5)
    long_term: float = Field(ge=0, le=1, default=0.5)
    creator: float = Field(ge=0, le=1, default=0.5)


class ProductIntelligence(BaseModel):
    """Product intelligence output from PIE."""
    product_id: str
    name: str
    category: str
    brand: str
    release_date: Optional[str] = None
    
    # Core intelligence
    headline: str
    sentiment: str = "neutral"
    sentiment_score: float = Field(ge=0, le=1, default=0.5)
    
    # Specifications
    specs: ProductSpecs = Field(default_factory=ProductSpecs)
    pricing: Optional[PricingInfo] = None
    
    # Usage contexts
    best_for: list[str] = []
    avoid_for: list[str] = []
    context_scores: UsageContextScores = Field(default_factory=UsageContextScores)
    
    # Decision factors
    who_should_buy: list[str] = []
    who_should_avoid: list[str] = []
    key_strengths: list[dict] = []
    key_weaknesses: list[dict] = []
    
    # Verdict
    verdict_score: float = Field(ge=0, le=10, default=5.0)
    verdict_text: Optional[str] = None


class ProductResponse(BaseResponse):
    """Complete product intelligence response."""
    summary: str
    data: ProductIntelligence
    context: ContextInfo = Field(default_factory=ContextInfo)
    llm_hints: LLMHints = Field(default_factory=LLMHints)


# ===== Commerce Signal Models =====

class FakeDiscountSignal(BaseModel):
    """Fake discount detection signal."""
    score: int = Field(ge=0, le=100, default=0)
    is_fake: bool = False
    claimed_discount: Optional[int] = None
    real_discount: Optional[int] = None
    evidence: list[str] = []
    confidence: float = Field(ge=0, le=1, default=0.8)


class StoreReliabilitySignal(BaseModel):
    """Store reliability signal."""
    score: int = Field(ge=0, le=100, default=50)
    tier: str = "standard"  # trusted, standard, caution, avoid
    breakdown: dict = {}
    red_flags: list[str] = []
    confidence: float = Field(ge=0, le=1, default=0.8)


class PriceVolatilitySignal(BaseModel):
    """Price volatility signal."""
    score: int = Field(ge=0, le=100, default=50)
    stability: str = "moderate"  # stable, moderate, volatile
    trend: str = "stable"  # rising, stable, declining
    weekly_change: Optional[float] = None
    monthly_range: Optional[dict] = None
    recommendation: str = "monitor"  # buy_now, wait, monitor
    confidence: float = Field(ge=0, le=1, default=0.8)


class LifecycleSignal(BaseModel):
    """Product lifecycle signal."""
    stage: str = "mature"  # launch, growth, mature, decline, clearance, discontinued
    months_since_launch: Optional[int] = None
    successor_announced: bool = False
    expected_replacement: Optional[str] = None
    confidence: float = Field(ge=0, le=1, default=0.8)


class SupplyRiskSignal(BaseModel):
    """Supply risk signal."""
    level: str = "low"  # low, medium, high, critical
    active_sellers: int = 0
    stock_status: str = "unknown"  # abundant, normal, low, critical
    alerts: list[str] = []
    confidence: float = Field(ge=0, le=1, default=0.8)


class CommerceSignals(BaseModel):
    """All commerce signals for a product."""
    product_id: str
    seller_id: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    fake_discount: FakeDiscountSignal = Field(default_factory=FakeDiscountSignal)
    store_reliability: StoreReliabilitySignal = Field(default_factory=StoreReliabilitySignal)
    price_volatility: PriceVolatilitySignal = Field(default_factory=PriceVolatilitySignal)
    lifecycle: LifecycleSignal = Field(default_factory=LifecycleSignal)
    supply_risk: SupplyRiskSignal = Field(default_factory=SupplyRiskSignal)
    
    # Composite scores
    buy_safety: int = Field(ge=0, le=100, default=50)
    value_score: int = Field(ge=0, le=100, default=50)
    timing_score: int = Field(ge=0, le=100, default=50)
    overall: str = "neutral"  # safe, proceed_with_caution, avoid


class SignalsResponse(BaseResponse):
    """Commerce signals response."""
    summary: str
    data: CommerceSignals
    context: ContextInfo = Field(default_factory=ContextInfo)
    llm_hints: LLMHints = Field(default_factory=LLMHints)


# ===== Comparison Models =====

class ComparisonWinner(BaseModel):
    """Winner info for a comparison aspect."""
    winner: str  # product_id or "tie"
    margin: str = "slight"  # significant, moderate, slight


class ComparisonResult(BaseModel):
    """Comparison between products."""
    products: list[dict]
    comparison_matrix: dict[str, ComparisonWinner] = {}
    verdict: dict = {}
    recommendation: str


class ComparisonResponse(BaseResponse):
    """Comparison response."""
    summary: str
    data: ComparisonResult
    context: ContextInfo = Field(default_factory=ContextInfo)
    llm_hints: LLMHints = Field(default_factory=LLMHints)


# ===== Best-For Models =====

class RecommendedProduct(BaseModel):
    """A recommended product."""
    rank: int
    product_id: str
    name: str
    price: int
    fit_score: float = Field(ge=0, le=1)
    why: str


class BestForQuery(BaseModel):
    """The query parameters for best-for request."""
    context: str
    category: str
    budget: Optional[int] = None
    currency: str = "TRY"


class BestForResult(BaseModel):
    """Best-for recommendation result."""
    query: BestForQuery
    recommendations: list[RecommendedProduct] = []
    methodology: str


class BestForResponse(BaseResponse):
    """Best-for response."""
    summary: str
    data: BestForResult
    context: ContextInfo = Field(default_factory=ContextInfo)
    llm_hints: LLMHints = Field(default_factory=LLMHints)
