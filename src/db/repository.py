"""
Repository layer — data access patterns for KıyasGO.

Encapsulates all database queries so engines never touch SQLAlchemy directly.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.db.models import Product, PriceHistory, Store, Review


class ProductRepository:
    """Read/write operations for products."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, product_id: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> list[Product]:
        q = self.db.query(Product).filter(
            or_(
                Product.name.ilike(f"%{query}%"),
                Product.brand.ilike(f"%{query}%"),
            )
        )
        if category:
            q = q.filter(Product.category == category)
        return q.limit(limit).all()

    def get_by_category(
        self,
        category: str,
        budget: Optional[int] = None,
        limit: int = 10,
    ) -> list[Product]:
        q = self.db.query(Product).filter(Product.category == category)
        if budget:
            q = q.filter(Product.price_avg <= budget)
        return q.order_by(Product.verdict_score.desc()).limit(limit).all()

    def get_top_for_context(
        self,
        category: str,
        context: str,
        budget: Optional[int] = None,
        limit: int = 5,
    ) -> list[Product]:
        """Get top products for a specific usage context."""
        score_col = {
            "gaming": Product.score_gaming,
            "photography": Product.score_photography,
            "student": Product.score_student,
            "business": Product.score_business,
            "budget": Product.score_budget,
            "long_term": Product.score_long_term,
            "creator": Product.score_creator,
        }.get(context, Product.verdict_score)

        q = self.db.query(Product).filter(Product.category == category)
        if budget:
            q = q.filter(Product.price_avg <= budget)
        return q.order_by(score_col.desc()).limit(limit).all()

    def upsert(self, product: Product) -> Product:
        """Insert or update a product."""
        existing = self.get_by_id(product.id)
        if existing:
            for key, value in product.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            self.db.commit()
            return existing
        else:
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            return product


class PriceRepository:
    """Price history operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_history(
        self,
        product_id: str,
        limit: int = 30,
    ) -> list[PriceHistory]:
        return (
            self.db.query(PriceHistory)
            .filter(PriceHistory.product_id == product_id)
            .order_by(PriceHistory.recorded_at.desc())
            .limit(limit)
            .all()
        )

    def add(self, entry: PriceHistory) -> PriceHistory:
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry


class StoreRepository:
    """Store / seller operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, store_id: str) -> Optional[Store]:
        return self.db.query(Store).filter(Store.id == store_id).first()

    def get_trusted(self, limit: int = 10) -> list[Store]:
        return (
            self.db.query(Store)
            .filter(Store.tier == "trusted")
            .order_by(Store.reliability_score.desc())
            .limit(limit)
            .all()
        )
