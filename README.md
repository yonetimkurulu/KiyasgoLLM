# KıyasGO AI Intelligence Service

LLM tabanlı, yeni nesil ürün kıyaslama, analiz ve alışveriş zekası platformu.

## 🚀 Özellikler

### 🧠 AI Core
- **Product Intelligence Engine (PIE):** Ürün özelliklerini analiz eder, normalize eder, kullanım senaryolarına (oyun, iş, vb.) göre puanlar.
- **Commerce Signal Engine (CSE):** Sahte indirimler, fiyat volatilitesi, stok riski ve satıcı güvenilirliği analizi yapar.
- **Recommendation Engine:** Kullanıcı bütçesine ve amacına en uygun ürünleri önerir.
- **Advanced LLM Provider:**
    - **Modeller:** Groq (Llama 3.3-70b - Varsayılan), Ollama, OpenAI.
    - **Capabilities:** Streaming response, Conversation Memory, Structured Output.
    - **Fallback:** API hatası durumunda otomatik model değiştirme.

### 📡 API Endpoints

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET` | `/health` | Servis sağlık durumu |
| `GET` | `/api/v1/ai/products/{id}` | Detaylı ürün zekası raporu |
| `GET` | `/api/v1/ai/compare` | Akıllı ürün karşılaştırma matrisi |
| `GET` | `/api/v1/ai/best-for/{context}` | Senaryo bazlı (örn: 'gaming') öneriler |
| `GET` | `/api/v1/ai/signals/{id}` | Ticari risk ve fırsat sinyalleri |
| `POST` | `/api/v1/ai/chat` | AI Asistan (Genel sohbet) |
| `POST` | `/api/v1/ai/chat/stream` | AI Asistan (Streaming yanıt) |
| `POST` | `/api/v1/ai/chat/analyze` | Sohbet tabanlı derin ürün analizi |

## 🛠️ Kurulum ve Başlatma

1. **Gereksinimleri Yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Yapılandırma:**
   - `.env.example` dosyasını `.env` olarak kopyalayın.
   - Groq API anahtarınızı ekleyin (`GROQ_API_KEY=...`).
   - Diğer API anahtarlarını (Opsiyonel: OpenAI) ekleyin.

3. **Redis (Opsiyonel ama Önerilir):**
   - Cache mekanizması için Redis gereklidir. Docker ile hızlıca başlatabilirsiniz:
     ```bash
     docker run -d -p 6379:6379 redis
     ```
   - Redis yoksa uygulama çalışır ancak cache devre dışı kalır.

4. **Sunucuyu Başlatın:**
   ```bash
   python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
   ```

## 📖 Dokümantasyon

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 🧪 Testler

```bash
# Unit testleri çalıştır
python -m pytest tests/

# Entegrasyon testlerini çalıştır (Sunucu 8006 portunda çalışırken)
python tests/integration/test_api.py
python tests/integration/test_chat.py
```

## 🏗️ Mimari

- `src/pie`: Ürün analizi ve özellik normalizasyonu.
- `src/cse`: Pazar sinyalleri (fiyat, stok, satıcı).
- `src/llm`: LLM entegrasyonu (Groq, Ollama, OpenAI fallback zinciri).
- `src/api`: FastAPI route tanımları.
- `src/cache`: Redis cache katmanı.
