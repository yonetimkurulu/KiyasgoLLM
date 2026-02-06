# KıyasGO AI Intelligence Service

LLM tabanlı ürün kıyaslama ve alışveriş zekası platformu.

## 🚀 Hızlı Başlangıç

```bash
# Virtual environment oluştur
python -m venv venv
venv\Scripts\activate  # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt

# Environment variables
copy .env.example .env
# .env dosyasını düzenle

# Sunucuyu başlat
uvicorn src.main:app --reload --port 8000
```

## 📡 API Endpoints

| Endpoint | Açıklama |
|----------|----------|
| `GET /api/v1/ai/products/{id}` | Ürün intelligence |
| `GET /api/v1/ai/compare` | Ürün karşılaştırma |
| `GET /api/v1/ai/best-for/{context}` | Context-based öneriler |
| `GET /api/v1/ai/signals/{id}` | Commerce signals |

## 📖 API Docs

Sunucu çalışırken: `http://localhost:8000/docs`

## 🏗️ Mimari

- **PIE:** Product Intelligence Engine
- **CSE:** Commerce Signal Engine
- **LLM:** Groq (varsayılan) / Ollama / OpenAI
