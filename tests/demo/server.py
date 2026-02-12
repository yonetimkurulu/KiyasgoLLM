
import sys
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.pie.decision_synthesizer import DecisionSynthesizer
from src.models.product import ProductSpecs, UsageContextScores

app = FastAPI()

# Mount static files (we'll just use a template for now but good practice)
# app.mount("/static", StaticFiles(directory="static"), name="static")

class DemoRequest(BaseModel):
    name: str
    specs: dict
    reviews: list

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(os.path.join(os.path.dirname(__file__), "index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.post("/analyze")
async def analyze_product(request: DemoRequest):
    synthesizer = DecisionSynthesizer()
    
    # Convert dict to ProductSpecs object
    # Handle potential empty fields safely
    specs_data = request.specs
    specs = ProductSpecs(
        screen_size=float(specs_data.get("screen_size", 0) or 0),
        screen_type=specs_data.get("screen_type", ""),
        chipset=specs_data.get("chipset", ""),
        chipset_tier=specs_data.get("chipset_tier", "mid"),
        ram_gb=int(specs_data.get("ram_gb", 0) or 0),
        storage_gb=int(specs_data.get("storage_gb", 0) or 0),
        battery_mah=int(specs_data.get("battery_mah", 0) or 0),
        camera_mp=int(specs_data.get("camera_mp", 0) or 0),
        weight_grams=int(specs_data.get("weight_grams", 0) or 0),
    )
    
    # Mock context scores for demo purposes (in a real app these come from other engines)
    # We'll just generate some random-ish but logical ones based on specs
    is_flagship = specs.chipset_tier == "flagship"
    context_scores = UsageContextScores(
        gaming=0.9 if is_flagship else 0.5,
        photography=0.9 if specs.camera_mp > 100 else 0.6,
        student=0.5,
        business=0.8,
        budget=0.2 if is_flagship else 0.8,
        long_term=0.9 if is_flagship else 0.6,
        creator=0.8 if specs.storage_gb > 256 else 0.4
    )
    
    # Mock price info
    price_info = {"average": 50000} # Dummy
    
    result = await synthesizer.synthesize(
        product_id="demo_id",
        name=request.name,
        specs=specs,
        context_scores=context_scores,
        price_info=price_info,
        reviews=request.reviews
    )
    
    return result

if __name__ == "__main__":
    print("Starting Demo Server at http://localhost:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)
