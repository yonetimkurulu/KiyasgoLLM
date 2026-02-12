
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.pie.decision_synthesizer import DecisionSynthesizer
from src.models.product import ProductSpecs, UsageContextScores

async def main():
    print("Initializing DecisionSynthesizer...")
    synthesizer = DecisionSynthesizer()
    
    # Dummy data for a flagship phone
    product_id = "test_123"
    name = "Samsung Galaxy S24 Ultra"
    specs = ProductSpecs(
        screen_size=6.8,
        screen_type="AMOLED",
        chipset="Snapdragon 8 Gen 3",
        chipset_tier="flagship",
        ram_gb=12,
        storage_gb=512,
        battery_mah=5000,
        camera_mp=200,
        weight_grams=232,
    )
    
    context_scores = UsageContextScores(
        gaming=0.95,
        photography=0.98,
        student=0.6,
        business=0.9,
        budget=0.2,
        long_term=0.9,
        creator=0.95,
    )
    
    price_info = {
        "average": 75000,
        "current_low": 72000,
        "current_high": 80000
    }
    
    reviews = [
        {"text": "Kamerası inanılmaz, özellikle gece çekimleri harika.", "sentiment": "positive"},
        {"text": "Batarya performansı beklediğimden iyi, 2 gün gidiyor.", "sentiment": "positive"},
        {"text": "Biraz ağır ve büyük, tek elle kullanımı zor.", "sentiment": "negative"},
        {"text": "Fiyatı çok yüksek ama parasını hak ediyor.", "sentiment": "neutral"},
    ]
    
    print("\nRunning synthesis...")
    try:
        result = await synthesizer.synthesize(
            product_id=product_id,
            name=name,
            specs=specs,
            context_scores=context_scores,
            price_info=price_info,
            reviews=reviews
        )
        
        print("\n--- SYNTHESIS RESULT ---")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print("\n--- CHECKS ---")
        if "headline" in result and result["headline"]:
            print("✅ Headline generated")
        else:
            print("❌ Headline missing")
            
        if result["verdict_score"] > 0:
            print(f"✅ Verdict score: {result['verdict_score']}")
        else:
            print("❌ Verdict score missing/invalid")
            
        if len(result["who_should_buy"]) > 0:
             print(f"✅ Who should buy: {len(result['who_should_buy'])} items")
        else:
             print("❌ Who should buy missing")

    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
