"""
SQLAlchemy ORM models for KıyasGO.

These models mirror the Pydantic models in src/models/product.py
but represent the persistent database layer.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    JSON,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from src.db.session import Base


class Product(Base):
    """Product table — the core entity."""
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    release_date = Column(String, nullable=True)

    # Specifications (denormalized JSON for flexibility)
    specs = Column(JSON, default={})

    # Pricing snapshot
    price_low = Column(Integer, nullable=True)
    price_high = Column(Integer, nullable=True)
    price_avg = Column(Integer, nullable=True)
    currency = Column(String, default="TRY")

    # Sentiment
    sentiment = Column(String, default="neutral")
    sentiment_score = Column(Float, default=0.5)

    # Usage context scores (denormalized for fast queries)
    score_gaming = Column(Float, default=0.5)
    score_photography = Column(Float, default=0.5)
    score_student = Column(Float, default=0.5)
    score_business = Column(Float, default=0.5)
    score_budget = Column(Float, default=0.5)
    score_long_term = Column(Float, default=0.5)
    score_creator = Column(Float, default=0.5)

    # Decision factors
    best_for = Column(JSON, default=[])
    avoid_for = Column(JSON, default=[])
    who_should_buy = Column(JSON, default=[])
    who_should_avoid = Column(JSON, default=[])
    key_strengths = Column(JSON, default=[])
    key_weaknesses = Column(JSON, default=[])

    # Verdict
    verdict_score = Column(Float, default=5.0)
    verdict_text = Column(Text, nullable=True)
    headline = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    prices = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product {self.id}: {self.name}>"


class PriceHistory(Base):
    """Price history for a product from a specific store."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    store_id = Column(String, ForeignKey("stores.id"), nullable=True, index=True)
    price = Column(Integer, nullable=False)
    currency = Column(String, default="TRY")
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    product = relationship("Product", back_populates="prices")
    store = relationship("Store", back_populates="price_entries")


class Store(Base):
    """E-commerce store / seller entity."""
    __tablename__ = "stores"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=True)
    
    # Reliability metrics
    reliability_score = Column(Integer, default=50)
    tier = Column(String, default="standard")  # trusted, standard, caution, avoid
    red_flags = Column(JSON, default=[])
    
    # Stats
    total_products = Column(Integer, default=0)
    return_rate = Column(Float, nullable=True)
    avg_shipping_days = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    price_entries = relationship("PriceHistory", back_populates="store")

    def __repr__(self):
        return f"<Store {self.id}: {self.name}>"


class Review(Base):
    """Product review for sentiment analysis."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    source = Column(String, nullable=True)  # e.g. "trendyol", "hepsiburada"
    rating = Column(Float, nullable=True)
    text = Column(Text, nullable=True)
    sentiment = Column(String, default="neutral")
    sentiment_score = Column(Float, default=0.5)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    product = relationship("Product", back_populates="reviews")

    def __repr__(self):
        return f"<Review product={self.product_id} rating={self.rating}>"
