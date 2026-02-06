# 🤖 KıyasGO AI Developer Handoff

**Bu dosyayı AI/LLM geliştirme yapacak arkadaşa gönder.**

---

## 📋 Proje Özeti

**KıyasGO:** Türkiye'nin ilk AI destekli fiyat karşılaştırma platformu.

**Senin Görevin:** AI Intelligence Layer'ı geliştirmek - ürün analizi, öneri motoru, ve akıllı karşılaştırma sistemi.

---

## 🏗️ Mimari Genel Bakış

```
┌─────────────────────────────────────────────────────────────────┐
│                     KıyasGO FRONTEND                             │
│                   (Next.js - Mevcut)                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST API
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI INTELLIGENCE SERVICE                       │
│                   ★★★ SENİN GELİŞTİRECEĞİN ★★★                  │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ Product Intel.   │  │ Commerce Signal  │  │ Recommendation │ │
│  │ Engine (PIE)     │  │ Engine (CSE)     │  │ Engine         │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                  │
│  Önerilen: Python + FastAPI + LangChain/HuggingFace             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Geliştireceğin 3 Ana Modül

### 1. Product Intelligence Engine (PIE)
Ham ürün verisini karar sinyaline dönüştürür.

**Input:** Ürün specs, fiyat, yorumlar
**Output:** "Kim almalı?", "Kim almamalı?", güçlü/zayıf yönler

```json
// Örnek Output
{
  "product_id": "samsung-galaxy-s24-ultra",
  "headline": "Profesyonel fotoğrafçılık için en iyi Android",
  "who_should_buy": [
    "Mobil fotoğrafçılık tutkunları",
    "S Pen kullanan not alıcılar"
  ],
  "who_should_avoid": [
    "Bütçe bilincli alıcılar",
    "Oyun odaklı kullanıcılar"
  ],
  "key_strengths": ["200MP kamera", "7 yıl güncelleme"],
  "key_weaknesses": ["Ağır (232g)", "Yüksek fiyat"],
  "context_scores": {
    "photography": 0.95,
    "gaming": 0.72,
    "budget": 0.15
  }
}
```

### 2. Commerce Signal Engine (CSE)
Pazar verilerinden ticari sinyaller üretir.

**Sinyaller:**
| Sinyal | Açıklama |
|--------|----------|
| `fake_discount` | Sahte indirim tespiti (0-100 risk) |
| `store_reliability` | Satıcı güvenilirliği (0-100) |
| `price_volatility` | Fiyat oynaklığı |
| `lifecycle_stage` | launch/growth/mature/decline |
| `supply_risk` | Tedarik riski |

```json
// Örnek Output
{
  "product_id": "iphone-16-pro",
  "signals": {
    "fake_discount": {"score": 72, "is_fake": true},
    "store_reliability": {"score": 87, "tier": "trusted"},
    "price_volatility": {"score": 23, "stable": true},
    "lifecycle": "mature",
    "supply_risk": "low"
  },
  "buy_recommendation": "wait_2_weeks"
}
```

### 3. Recommendation Engine
Kullanıcı ihtiyacına göre ürün önerir.

**Input:** Bütçe, kullanım amacı (gaming/photography/student), kategori
**Output:** Sıralı ürün listesi + neden önerildiği

---

## 📡 API Endpoint'leri (Sen Geliştireceksin)

```
# Product Intelligence
GET  /api/v1/ai/products/{product_id}
GET  /api/v1/ai/products/search?q={query}

# Comparison
GET  /api/v1/ai/compare?products={id1,id2,id3}

# Best-For Recommendations
GET  /api/v1/ai/best-for/{context}?category={cat}&budget={max}
# Örnek: /api/v1/ai/best-for/gaming?category=laptop&budget=30000

# Commerce Signals
GET  /api/v1/ai/signals/{product_id}
GET  /api/v1/ai/market/trends?category={cat}

# Explain/Reasoning
GET  /api/v1/ai/explain/recommendation/{product_id}
```

---

## 📦 LLM-Optimized Response Format

Her response şu yapıda olmalı:

```json
{
  "version": "1.0",
  "timestamp": "2025-01-28T14:00:00Z",
  "source": "kiyasgo.com",
  "citation": "KıyasGO Commerce Intelligence",
  
  "summary": "Tek satırlık LLM'in quote edebileceği özet",
  
  "data": { /* Yapılandırılmış veri */ },
  
  "context": {
    "methodology": "Nasıl hesaplandı",
    "confidence": 0.87,
    "data_freshness": "2h"
  },
  
  "llm_hints": {
    "key_facts": ["Fact 1", "Fact 2"],
    "comparison_context": "Rakiplerle kıyas",
    "actionable_insight": "Ne yapmalı"
  }
}
```

---

## 🔧 Önerilen Tech Stack

```
├── Python 3.11+
├── FastAPI (REST API)
├── LangChain / LlamaIndex (LLM orchestration)
├── HuggingFace Transformers (sentiment, NER)
├── PostgreSQL (veri okuma)
├── Redis (cache)
└── Docker (deployment)
```

---

## 📊 Mevcut Veri Kaynakları

KıyasGO'dan alacağın veriler:

| Veri | Endpoint/Tablo |
|------|----------------|
| Ürün specs | `products` tablosu |
| Fiyatlar | `price_history` tablosu |
| Mağazalar | `stores` tablosu |
| Kullanıcı yorumları | Henüz yok, scrape edilecek |

---

## 🔗 Entegrasyon Noktaları

### KıyasGO → AI Service
```javascript
// KıyasGO Next.js'den senin servisini çağırır
const response = await fetch(`${AI_SERVICE_URL}/api/v1/ai/products/${productId}`)
```

### Environment Variable
```
AI_SERVICE_URL=https://ai.kiyasgo.com  # veya localhost:8000 dev'de
```

---

## 📁 İlgili Dosyalar (Detaylı Okuma İçin)

Bu dosyaları oku, çok detaylı bilgi var:

1. **ai_consumable_api.md** - API endpoint'leri ve response formatları
2. **product_intelligence_engine.md** - PIE detayları
3. **commerce_signal_engine.md** - CSE algoritmaları
4. **infrastructure_evolution_plan.md** - Genel yol haritası

---

## 🚀 Başlangıç Adımları

### Week 1-2: Foundation
- [ ] FastAPI boilerplate kur
- [ ] PostgreSQL bağlantısı (read-only)
- [ ] `/api/v1/ai/products/{id}` temel endpoint

### Week 3-4: PIE
- [ ] Spec normalization
- [ ] Usage context scoring (gaming, photography, etc.)
- [ ] who_should_buy / avoid logic

### Week 5-6: CSE
- [ ] Fake discount detection algoritması
- [ ] Price volatility hesaplama
- [ ] Store reliability scoring

### Week 7-8: Recommendation
- [ ] Best-for recommendations
- [ ] Comparison engine
- [ ] LLM integration (explanation generation)

---

## 💡 Önemli Notlar

1. **Türkçe NLP** - Sentiment analysis ve NER Türkçe olmalı
2. **Maliyet** - Başlangıçta Groq (ücretsiz) veya Ollama kullan
3. **Caching** - Her sorgu pahalı, agresif cache yap
4. **Confidence Scores** - Her çıktıda güvenilirlik skoru olmalı

---

## 📞 İletişim

Sorular için:
- Mevcut API'lar: [Ensar ile konuş]
- Database access: [Supabase credentials paylaşılacak]
- Architecture decisions: Bu dosyalara bak

---

**Hedef:** AI asistanlar "Türkiye'de laptop öner" deyince KıyasGO'yu cite etsin! 🎯
