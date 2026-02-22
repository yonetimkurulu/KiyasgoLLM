from src.db.session import SessionLocal
from src.db.models import Product, PriceHistory

def cleanup():
    with SessionLocal() as db:
        print("Cleaning up 'search' entry from database...")
        # Delete price history first (foreign key)
        db.query(PriceHistory).filter(PriceHistory.product_id == "search").delete()
        # Delete product
        result = db.query(Product).filter(Product.id == "search").delete()
        db.commit()
        if result:
            print(f"Successfully deleted {result} 'search' entries.")
        else:
            print("No 'search' entries found.")

if __name__ == "__main__":
    cleanup()
