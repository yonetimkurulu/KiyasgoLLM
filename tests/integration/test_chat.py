"""Test chat API"""
import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://127.0.0.1:8006"

# Test health
r = urllib.request.urlopen(f"{BASE}/health")
print("Health:", json.loads(r.read()))

# Test chat endpoint
data = json.dumps({
    "message": "Samsung Galaxy S24 Ultra hakkinda ne dusunuyorsun?",
    "context": "shopping"
}).encode()

req = urllib.request.Request(
    f"{BASE}/api/v1/ai/chat",
    data=data,
    headers={"Content-Type": "application/json"}
)

try:
    r = urllib.request.urlopen(req)
    result = json.loads(r.read())
    print("\nChat Response:")
    print(f"  Response: {result['response'][:200]}...")
    print(f"  Conversation ID: {result['conversation_id']}")
    print("\n--- Chat API test passed! ---")
except Exception as e:
    print(f"Chat test error: {e}")
