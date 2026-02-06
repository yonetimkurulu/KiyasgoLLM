"""API Test Script"""
import urllib.request
import json

BASE = "http://127.0.0.1:8003"

# Test health
r = urllib.request.urlopen(f"{BASE}/health")
print("Health:", json.loads(r.read()))

# Test best-for (access recommendations from data.recommendations)
r = urllib.request.urlopen(f"{BASE}/api/v1/ai/best-for/gaming?category=smartphone&limit=3")
d = json.loads(r.read())
print("\nGaming Recommendations:")
for p in d["data"]["recommendations"]:
    print(f"  {p['rank']}. {p['name']} (fit: {p['fit_score']})")

# Test compare
r = urllib.request.urlopen(f"{BASE}/api/v1/ai/compare/category/smartphone?limit=3")
d = json.loads(r.read())
print("\nComparison Winner:", d["data"]["verdict"].get("winner", "N/A"))

print("\n--- All tests passed! ---")

