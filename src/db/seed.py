"""
Database seeder — populates the database with initial product data.
Uses the same mock data that the engines currently return.

Usage:
    python -m src.db.seed
"""
from src.db.session import SessionLocal, init_db
from src.db.models import Product, PriceHistory, Store


def seed():
    """Seed the database with mock product data."""
    init_db()
    db = SessionLocal()

    # Check if already seeded
    if db.query(Product).first():
        print("Database already seeded, skipping.")
        db.close()
        return

    # ---- Products ----
    products = [
        Product(
            id="samsung-galaxy-s24-ultra",
            name="Samsung Galaxy S24 Ultra",
            brand="Samsung",
            category="smartphone",
            release_date="2024-01",
            specs={
                "screen_size": 6.8, "screen_type": "Dynamic AMOLED 2X",
                "chipset": "Snapdragon 8 Gen 3", "chipset_tier": "flagship",
                "ram_gb": 12, "storage_gb": 256, "battery_mah": 5000,
                "camera_mp": 200, "weight_grams": 232,
            },
            price_low=69999, price_high=89999, price_avg=74999, currency="TRY",
            sentiment="positive", sentiment_score=0.82,
            score_gaming=0.92, score_photography=0.95, score_student=0.35,
            score_business=0.88, score_budget=0.15, score_long_term=0.90,
            score_creator=0.88,
            best_for=["photography", "gaming", "long_term"],
            avoid_for=["budget", "student"],
            who_should_buy=["Mobil fotoğrafçılık tutkunları", "Mobil oyun tutkunları",
                            "Premium deneyim arayanlar", "İş profesyonelleri"],
            who_should_avoid=["Bütçe bilincli alıcılar", "Kompakt telefon arayanlar"],
            key_strengths=[
                {"point": "200MP kamera", "impact": "high"},
                {"point": "Flagship işlemci", "impact": "high"},
                {"point": "S Pen", "impact": "medium"},
            ],
            key_weaknesses=[
                {"point": "Yüksek fiyat", "impact": "high"},
                {"point": "Ağır (232g)", "impact": "medium"},
            ],
            verdict_score=8.7,
            verdict_text="Fotoğraf ve performans odaklı kullanıcılar için en iyi seçenek",
            headline="Samsung'un amiral gemisi: Fotoğraf canavarı S24 Ultra",
        ),
        Product(
            id="iphone-16-pro",
            name="iPhone 16 Pro",
            brand="Apple",
            category="smartphone",
            release_date="2024-09",
            specs={
                "screen_size": 6.3, "screen_type": "Super Retina XDR OLED",
                "chipset": "A18 Pro", "chipset_tier": "flagship",
                "ram_gb": 8, "storage_gb": 256, "battery_mah": 3582,
                "camera_mp": 48, "weight_grams": 199,
            },
            price_low=74999, price_high=94999, price_avg=79999, currency="TRY",
            sentiment="positive", sentiment_score=0.85,
            score_gaming=0.85, score_photography=0.90, score_student=0.40,
            score_business=0.92, score_budget=0.10, score_long_term=0.95,
            score_creator=0.90,
            best_for=["business", "long_term", "photography"],
            avoid_for=["budget"],
            who_should_buy=["Apple ekosistemi kullanıcıları", "İş profesyonelleri",
                            "Uzun vadeci kullanıcılar"],
            who_should_avoid=["Bütçe bilincli alıcılar", "Android tercihi olanlar"],
            key_strengths=[
                {"point": "A18 Pro çip", "impact": "high"},
                {"point": "Uzun yazılım desteği", "impact": "high"},
                {"point": "Kompakt boyut", "impact": "medium"},
            ],
            key_weaknesses=[
                {"point": "Fiyat", "impact": "high"},
                {"point": "Sınırlı özelleştirme", "impact": "medium"},
            ],
            verdict_score=8.9,
            verdict_text="İş ve uzun vadeli kullanım için mükemmel",
            headline="Apple'ın en güçlü Pro modeli: iPhone 16 Pro",
        ),
        Product(
            id="xiaomi-14t-pro",
            name="Xiaomi 14T Pro",
            brand="Xiaomi",
            category="smartphone",
            release_date="2024-10",
            specs={
                "screen_size": 6.67, "screen_type": "AMOLED",
                "chipset": "Dimensity 9300+", "chipset_tier": "flagship",
                "ram_gb": 12, "storage_gb": 256, "battery_mah": 5000,
                "camera_mp": 50, "weight_grams": 209,
            },
            price_low=29999, price_high=37999, price_avg=33999, currency="TRY",
            sentiment="positive", sentiment_score=0.78,
            score_gaming=0.88, score_photography=0.80, score_student=0.75,
            score_business=0.65, score_budget=0.80, score_long_term=0.70,
            score_creator=0.72,
            best_for=["gaming", "budget", "student"],
            avoid_for=[],
            who_should_buy=["Bütçe dostu flagship arayanlar", "Öğrenciler",
                            "Oyun severler"],
            who_should_avoid=["Kamera öncelikli kullanıcılar"],
            key_strengths=[
                {"point": "Fiyat/performans oranı", "impact": "high"},
                {"point": "Güçlü işlemci", "impact": "high"},
                {"point": "5000mAh batarya", "impact": "medium"},
            ],
            key_weaknesses=[
                {"point": "Yazılım güncellemesi belirsiz", "impact": "medium"},
            ],
            verdict_score=8.2,
            verdict_text="Fiyat/performans kralı",
            headline="Xiaomi 14T Pro: Uygun fiyata flagship deneyimi",
        ),
        Product(
            id="macbook-pro-16",
            name="MacBook Pro 16 (M3 Max)",
            brand="Apple",
            category="laptop",
            specs={
                "screen_size": 16.2, "screen_type": "Liquid Retina XDR",
                "chipset": "M3 Max", "chipset_tier": "flagship",
                "ram_gb": 36, "storage_gb": 1024,
            },
            price_low=129999, price_high=169999, price_avg=149999, currency="TRY",
            sentiment="very_positive", sentiment_score=0.92,
            score_gaming=0.55, score_photography=0.70, score_student=0.20,
            score_business=0.95, score_budget=0.05, score_long_term=0.95,
            score_creator=0.98,
            best_for=["creator", "business", "long_term"],
            avoid_for=["budget", "student", "gaming"],
            verdict_score=9.2,
            verdict_text="İçerik üreticileri ve profesyoneller için en iyi laptop",
            headline="MacBook Pro 16: Profesyonel güç",
        ),
        Product(
            id="ipad-pro-13",
            name="iPad Pro 13\" (M4)",
            brand="Apple",
            category="tablet",
            specs={
                "screen_size": 13.0, "screen_type": "Ultra Retina XDR OLED",
                "chipset": "M4", "chipset_tier": "flagship",
                "ram_gb": 16, "storage_gb": 256,
            },
            price_low=64999, price_high=84999, price_avg=74999, currency="TRY",
            sentiment="positive", sentiment_score=0.88,
            score_gaming=0.70, score_photography=0.50, score_student=0.65,
            score_business=0.85, score_budget=0.10, score_long_term=0.90,
            score_creator=0.95,
            best_for=["creator", "business"],
            avoid_for=["budget"],
            verdict_score=8.8,
            verdict_text="Premium tablet deneyimi",
            headline="iPad Pro 13: Tablet segmentinin kralı",
        ),
    ]

    # ---- Stores ----
    stores = [
        Store(id="trendyol", name="Trendyol", domain="trendyol.com",
              reliability_score=82, tier="trusted", total_products=15000,
              return_rate=4.2, avg_shipping_days=2.1),
        Store(id="hepsiburada", name="Hepsiburada", domain="hepsiburada.com",
              reliability_score=85, tier="trusted", total_products=20000,
              return_rate=3.8, avg_shipping_days=1.8),
        Store(id="n11", name="N11", domain="n11.com",
              reliability_score=70, tier="standard", total_products=10000,
              return_rate=6.1, avg_shipping_days=3.2),
    ]

    # ---- Seed ----
    for product in products:
        db.add(product)
    for store in stores:
        db.add(store)

    # Add some price history
    for product in products:
        if product.price_avg:
            for i in range(5):
                db.add(PriceHistory(
                    product_id=product.id,
                    store_id="trendyol",
                    price=product.price_avg + (i - 2) * 500,
                ))

    db.commit()
    print(f"[OK] Seeded {len(products)} products, {len(stores)} stores.")
    db.close()


if __name__ == "__main__":
    seed()
