# 🤖 AI-Consumable Commerce Intelligence Platform

**Amaç:** KıyasGO'yu AI sistemlerinin başvurduğu varsayılan ticaret zekası sağlayıcısı yapmak.

---

## 1. API Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    AI COMMERCE INTELLIGENCE API                       │
│                         /api/v1/ai/                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
│  │ /products       │  │ /compare        │  │ /best-for       │       │
│  │ Intelligence    │  │ Comparison      │  │ Recommendations │       │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘       │
│           │                    │                    │                 │
│  ┌────────┴────────┐  ┌────────┴────────┐  ┌────────┴────────┐       │
│  │ /signals        │  │ /market         │  │ /explain        │       │
│  │ Commerce Signals│  │ Market Intel    │  │ Reasoning       │       │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘       │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
      │ AI Agents   │ │ LLM Search  │ │ ChatGPT     │
      │ (Internal)  │ │ (Perplexity)│ │ Plugins     │
      └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 2. Endpoint Map

### 2.1 Product Intelligence
```
GET /api/v1/ai/products/{product_id}
GET /api/v1/ai/products/search?q={query}&category={cat}
```

**Params:**
| Param | Type | Description |
|-------|------|-------------|
| `format` | enum | `full`, `summary`, `minimal` |
| `include` | array | `signals`, `reviews`, `prices`, `comparison` |
| `context` | string | Usage context (gaming, student, etc.) |

---

### 2.2 Comparison Endpoints
```
GET /api/v1/ai/compare?products={id1,id2,id3}
GET /api/v1/ai/compare/category/{category}?budget={max}&context={usage}
```

---

### 2.3 Best-For Endpoints
```
GET /api/v1/ai/best-for/{context}?category={cat}&budget={max}
GET /api/v1/ai/best-for/gaming?category=laptop&budget=50000
GET /api/v1/ai/best-for/photography?category=phone
```

---

### 2.4 Market Signal Endpoints
```
GET /api/v1/ai/signals/{product_id}
GET /api/v1/ai/signals/category/{category}
GET /api/v1/ai/market/trends?category={cat}&period={days}
```

---

### 2.5 Explain/Reasoning Endpoints
```
GET /api/v1/ai/explain/recommendation/{product_id}
GET /api/v1/ai/explain/comparison/{product_id_1}/{product_id_2}
GET /api/v1/ai/explain/signal/{signal_type}/{product_id}
```

---

## 3. LLM-Optimized Response Formats

### 3.1 Standard Response Structure
```json
{
  "version": "1.0",
  "timestamp": "2025-01-28T14:00:00Z",
  "source": "kiyasgo.com",
  "citation": "KıyasGO Commerce Intelligence",
  
  "summary": "One-line human-readable summary for LLM to quote",
  
  "data": { /* Structured data */ },
  
  "context": {
    "methodology": "How this was calculated",
    "confidence": 0.87,
    "data_freshness": "2h",
    "limitations": ["Note any caveats"]
  },
  
  "llm_hints": {
    "key_facts": ["Fact 1", "Fact 2"],
    "comparison_context": "vs competitors",
    "actionable_insight": "What to do with this info"
  }
}
```

---

### 3.2 Product Intelligence Response
```json
{
  "version": "1.0",
  "source": "kiyasgo.com",
  "citation": "KıyasGO Product Intelligence, January 2025",
  
  "summary": "Samsung Galaxy S24 Ultra, profesyonel fotoğrafçılık için en iyi Android telefon. 200MP kamera, 7 yıl güncelleme, ₺89.999 ortalama fiyat.",
  
  "data": {
    "product": {
      "id": "samsung-galaxy-s24-ultra",
      "name": "Samsung Galaxy S24 Ultra",
      "category": "flagship_smartphone",
      "brand": "Samsung",
      "release_date": "2024-01"
    },
    
    "pricing": {
      "current_low": 85000,
      "current_high": 95000,
      "average": 89999,
      "currency": "TRY",
      "trend": "declining",
      "buy_signal": "wait"
    },
    
    "intelligence": {
      "headline": "Profesyonel fotoğrafçılık için en iyi Android",
      "sentiment": "positive",
      "sentiment_score": 0.78,
      
      "best_for": ["photography", "long_term", "business"],
      "avoid_for": ["budget", "compact_preference", "heavy_gaming"],
      
      "who_should_buy": [
        "Mobil fotoğrafçılık tutkunları",
        "S Pen kullanan not alıcılar",
        "7 yıl güncelleme isteyen uzun vadeciler"
      ],
      
      "who_should_avoid": [
        "Bütçe bilincli alıcılar",
        "Kompakt telefon arayanlar"
      ],
      
      "key_strengths": [
        "200MP ana kamera",
        "7 yıl yazılım desteği",
        "Titanium gövde"
      ],
      
      "key_weaknesses": [
        "Ağır (232g)",
        "Yüksek fiyat",
        "Oyunda ısınma"
      ]
    },
    
    "signals": {
      "fake_discount": {"score": 15, "safe": true},
      "store_reliability": {"avg_score": 85},
      "price_volatility": {"score": 23, "stable": true},
      "lifecycle": "mature",
      "supply_risk": "low"
    }
  },
  
  "llm_hints": {
    "key_facts": [
      "200MP kamera ile mobil fotoğrafçılıkta lider",
      "7 yıl yazılım güncellemesi garantisi",
      "₺85,000 - ₺95,000 fiyat aralığı",
      "Ağır (232g) - cep dostu değil"
    ],
    "comparison_context": "iPhone 15 Pro Max ile ana rakip. Kamera çeşitliliğinde kazanır, oyun performansında kaybeder.",
    "actionable_insight": "Fiyat düşüş trendinde, 2-3 hafta beklenmesi önerilir."
  }
}
```

---

### 3.3 Comparison Response
```json
{
  "version": "1.0",
  "source": "kiyasgo.com",
  "citation": "KıyasGO Comparison Analysis",
  
  "summary": "iPhone 16 Pro vs Galaxy S24 Ultra: iPhone oyunda üstün, Galaxy fotoğrafçılıkta. Uzun vadeli kullanım için ikisi de iyi.",
  
  "data": {
    "products": [
      {"id": "iphone-16-pro", "name": "iPhone 16 Pro"},
      {"id": "galaxy-s24-ultra", "name": "Samsung Galaxy S24 Ultra"}
    ],
    
    "comparison_matrix": {
      "camera": {"winner": "galaxy-s24-ultra", "margin": "significant"},
      "gaming": {"winner": "iphone-16-pro", "margin": "moderate"},
      "battery": {"winner": "galaxy-s24-ultra", "margin": "slight"},
      "software_support": {"winner": "tie", "note": "Both 7 years"},
      "price": {"winner": "iphone-16-pro", "margin": "slight"}
    },
    
    "verdict": {
      "overall_winner": "context_dependent",
      "for_photography": "galaxy-s24-ultra",
      "for_gaming": "iphone-16-pro",
      "for_value": "iphone-16-pro"
    },
    
    "recommendation": "Fotoğrafçılık öncelikliyse Galaxy, genel kullanım ve oyun için iPhone."
  },
  
  "llm_hints": {
    "key_facts": [
      "Kamera: Galaxy S24 Ultra (200MP vs 48MP)",
      "Oyun: iPhone 16 Pro (A18 Pro daha verimli)",
      "Güncelleme: İkisi de 7 yıl",
      "Fiyat: iPhone %5 daha ucuz"
    ]
  }
}
```

---

### 3.4 Best-For Response
```json
{
  "version": "1.0",
  "source": "kiyasgo.com",
  
  "summary": "30.000₺ bütçeyle oyun için en iyi laptop: ASUS TUF Gaming A15. RTX 4060, Ryzen 7, 144Hz ekran.",
  
  "data": {
    "query": {
      "context": "gaming",
      "category": "laptop",
      "budget": 30000,
      "currency": "TRY"
    },
    
    "recommendations": [
      {
        "rank": 1,
        "product": "asus-tuf-gaming-a15",
        "name": "ASUS TUF Gaming A15",
        "price": 28999,
        "fit_score": 0.94,
        "why": "Bu bütçede en iyi GPU (RTX 4060) ve soğutma sistemi"
      },
      {
        "rank": 2,
        "product": "lenovo-ideapad-gaming-3",
        "name": "Lenovo IdeaPad Gaming 3",
        "price": 26499,
        "fit_score": 0.87,
        "why": "Daha uygun fiyat, ama GPU bir kademe düşük (RTX 4050)"
      }
    ],
    
    "methodology": "GPU tier, soğutma, ekran yenileme hızı ve fiyat/performans oranı ağırlıklı sıralama"
  }
}
```

---

## 4. AEO/GEO Content Strategy

### 4.1 Structured Data (Schema.org)
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Samsung Galaxy S24 Ultra",
  "description": "Profesyonel fotoğrafçılık için en iyi Android telefon",
  "brand": {"@type": "Brand", "name": "Samsung"},
  
  "review": {
    "@type": "Review",
    "author": {"@type": "Organization", "name": "KıyasGO"},
    "reviewRating": {
      "@type": "Rating",
      "ratingValue": "8.7",
      "bestRating": "10"
    },
    "reviewBody": "200MP kamera ile fotoğrafçılıkta lider..."
  },
  
  "offers": {
    "@type": "AggregateOffer",
    "lowPrice": "85000",
    "highPrice": "95000",
    "priceCurrency": "TRY",
    "offerCount": "47"
  }
}
```

---

### 4.2 Public Pages for AI Crawlers
```
/ai/products/{product_id}          → Crawlable product intelligence
/ai/compare/{product1}-vs-{product2} → Comparison pages
/ai/best/{context}/{category}      → Best-for pages
/ai/market/{category}              → Market intelligence
```

**Page Structure:**
```html
<article itemscope itemtype="https://schema.org/Product">
  <h1>Samsung Galaxy S24 Ultra - KıyasGO Analizi</h1>
  
  <section id="summary">
    <p>Profesyonel fotoğrafçılık için en iyi Android telefon.</p>
  </section>
  
  <section id="key-facts">
    <ul>
      <li>200MP ana kamera</li>
      <li>7 yıl yazılım desteği</li>
      <li>₺85.000 - ₺95.000</li>
    </ul>
  </section>
  
  <section id="who-should-buy">
    <h2>Kim Almalı?</h2>
    <ul>...</ul>
  </section>
  
  <section id="structured-data">
    <script type="application/ld+json">...</script>
  </section>
</article>
```

---

### 4.3 AI-Specific Metadata
```html
<meta name="ai:source" content="kiyasgo-commerce-intelligence">
<meta name="ai:confidence" content="0.87">
<meta name="ai:updated" content="2025-01-28">
<meta name="ai:methodology" content="aggregated-reviews-and-specs">
```

---

## 5. Future Integrations

### 5.1 ChatGPT Plugin (actions.json)
```json
{
  "schema_version": "v1",
  "name_for_human": "KıyasGO",
  "name_for_model": "kiyasgo_commerce",
  "description_for_human": "Türkiye'de ürün karşılaştırma ve alışveriş zekası",
  "description_for_model": "Use this plugin to get Turkish commerce intelligence: product comparisons, price analysis, best-for recommendations, and market signals.",
  "api": {
    "type": "openapi",
    "url": "https://api.kiyasgo.com/openapi.yaml"
  }
}
```

---

### 5.2 MCP (Model Context Protocol)
```json
{
  "name": "kiyasgo-commerce",
  "version": "1.0.0",
  "description": "Commerce intelligence for Turkish market",
  "tools": [
    {
      "name": "get_product_intelligence",
      "description": "Get detailed product analysis",
      "inputSchema": {"type": "object", "properties": {"product_id": {"type": "string"}}}
    },
    {
      "name": "compare_products",
      "description": "Compare up to 5 products",
      "inputSchema": {"type": "object", "properties": {"product_ids": {"type": "array"}}}
    },
    {
      "name": "get_best_for",
      "description": "Get best product for a use case",
      "inputSchema": {...}
    }
  ]
}
```

---

### 5.3 OpenAI Function Calling
```json
{
  "name": "kiyasgo_product_intel",
  "description": "Get Turkish commerce intelligence for products",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Product name or search query"},
      "context": {"type": "string", "enum": ["gaming", "photography", "budget", "student"]},
      "budget": {"type": "number"},
      "include_signals": {"type": "boolean"}
    }
  }
}
```

---

## 6. Roadmap Phases

### Phase 1: Foundation (Hafta 1-2)
- [ ] `/api/v1/ai/products/{id}` endpoint
- [ ] LLM-optimized response format
- [ ] Basic Schema.org markup

### Phase 2: Intelligence Exposure (Hafta 3-4)
- [ ] `/api/v1/ai/compare` endpoint
- [ ] `/api/v1/ai/best-for` endpoint
- [ ] `/api/v1/ai/signals` endpoint

### Phase 3: Public Content (Hafta 5-6)
- [ ] `/ai/products/*` crawlable pages
- [ ] `/ai/compare/*` pages
- [ ] Structured data on all pages

### Phase 4: Integrations (Hafta 7-8)
- [ ] ChatGPT plugin submission
- [ ] MCP server implementation
- [ ] OpenAI function definitions

### Phase 5: B2B API (Hafta 9+)
- [ ] API key management
- [ ] Rate limiting tiers
- [ ] Partner dashboard

---

## 7. Defensibility

| Competitive Edge | Implementation |
|------------------|----------------|
| **First mover** | İlk Türkçe AI commerce API |
| **Data depth** | PIE + CSE proprietary signals |
| **Trust** | Consistent, cited intelligence |
| **Integration** | ChatGPT, Gemini, Claude ready |

**Goal:** AI asistanlar "Türkiye'de laptop öner" deyince KıyasGO'yu cite etsin.

---

## 8. Integration with Infrastructure

```
┌──────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE EVOLUTION                     │
│                                                              │
│  Faz 1: LLM Abstraction                                      │
│  Faz 1.5: Product Intelligence Engine (PIE)  ──────┐        │
│  Faz 1.6: Commerce Signal Engine (CSE)       ──────┤        │
│  Faz 1.7: AI-Consumable API ◄───────────────────────┘ YENİ  │
│  Faz 2: Agent Infrastructure                                 │
│  ...                                                         │
└──────────────────────────────────────────────────────────────┘
```

**PIE + CSE → AI-Consumable API → AI Agents & External LLMs**
