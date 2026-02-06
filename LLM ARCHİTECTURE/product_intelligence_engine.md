# 🧠 Product Intelligence Engine (PIE)

**KıyasGO'nun kalbi: Ham veriyi karar sinyaline dönüştüren katman.**

---

## 1. Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION                               │
│    [Scraper] → [API Feeds] → [User Reviews] → [Price Streams]       │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PRODUCT INTELLIGENCE ENGINE                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Normaliza-  │  │  Review     │  │   Usage     │  │  Decision   │ │
│  │ tion Svc    │→ │  Intel Svc  │→ │ Inference   │→ │  Synthesis  │ │
│  │             │  │             │  │   Svc       │  │    Svc      │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
│         │               │               │               │           │
│         └───────────────┴───────────────┴───────────────┘           │
│                              │                                       │
│                    ┌─────────▼─────────┐                            │
│                    │ Product Intel DB  │                            │
│                    │ (Decision Store)  │                            │
│                    └───────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CONSUMPTION LAYER                               │
│  [AI Agents] ← [Search API] ← [Product Pages] ← [Recommendation]    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Service Breakdown

### 2.1 Normalization Service
**Görev:** Ham veriyi standart formata dönüştür.

| Input | Output |
|-------|--------|
| "6.7 inch AMOLED" | `{screen_size: 6.7, screen_type: "AMOLED"}` |
| "128 GB / 256 GB" | `{storage_variants: [128, 256]}` |
| "Snapdragon 8 Gen 3" | `{chipset: "snapdragon_8_gen_3", tier: "flagship"}` |

**İşlemler:**
```
┌──────────────┐    ┌────────────────┐    ┌──────────────┐
│ Raw Spec     │ →  │ Parser +       │ →  │ Normalized   │
│ Extraction   │    │ Unit Converter │    │ Spec Object  │
└──────────────┘    └────────────────┘    └──────────────┘
                           │
                    ┌──────▼──────┐
                    │ Variant     │
                    │ Clustering  │
                    └─────────────┘
```

**Variant Resolution:**
```json
{
  "base_product_id": "iphone-16-pro",
  "variants": [
    {"sku": "iphone-16-pro-128", "storage": 128, "color": "black"},
    {"sku": "iphone-16-pro-256", "storage": 256, "color": "white"}
  ],
  "canonical_model": "iPhone 16 Pro"
}
```

---

### 2.2 Review Intelligence Service
**Görev:** Yorumlardan sentiment, pros/cons, risk sinyalleri çıkar.

**Pipeline:**
```
[Raw Reviews] → [Sentiment Analysis] → [Aspect Extraction] → [Aggregation]
                      │
            ┌─────────┴─────────┐
            │                   │
     [Pros Extraction]    [Cons Extraction]
            │                   │
            └─────────┬─────────┘
                      ▼
            [Risk & Drawback Detection]
```

**Çıktı:**
```json
{
  "sentiment_score": 0.78,
  "review_count": 1247,
  "pros": [
    {"aspect": "camera", "mention_rate": 0.45, "confidence": 0.92},
    {"aspect": "battery_life", "mention_rate": 0.38, "confidence": 0.88}
  ],
  "cons": [
    {"aspect": "price", "mention_rate": 0.52, "confidence": 0.95},
    {"aspect": "weight", "mention_rate": 0.15, "confidence": 0.72}
  ],
  "risks": [
    {"type": "durability", "severity": "medium", "evidence": "Screen crack complaints in 3% of reviews"}
  ]
}
```

---

### 2.3 Usage Inference Service
**Görev:** Ürünün hangi kullanım senaryolarına uygun olduğunu belirle.

**Usage Contexts:**
| Context | Criteria |
|---------|----------|
| `gaming` | GPU tier, refresh rate, cooling |
| `student` | Price, battery, portability |
| `photography` | Camera specs, sensor size, OIS |
| `business` | Build quality, security features |
| `budget` | Price/performance ratio |
| `long_term` | Update policy, build quality, repairability |
| `creator` | Display accuracy, performance, ports |

**İşlem:**
```
[Normalized Specs] + [Price Data] + [Review Intel]
                    │
                    ▼
        ┌───────────────────────┐
        │ Usage Context Scorer  │
        │ (Rule-based + ML)     │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Context Fit Scores    │
        │ {gaming: 0.9, ...}    │
        └───────────────────────┘
```

**Çıktı:**
```json
{
  "primary_contexts": ["gaming", "creator"],
  "secondary_contexts": ["long_term"],
  "avoid_contexts": ["budget", "student"],
  "context_scores": {
    "gaming": 0.92,
    "creator": 0.85,
    "photography": 0.78,
    "business": 0.45,
    "student": 0.25,
    "budget": 0.15
  }
}
```

---

### 2.4 Decision Synthesis Service
**Görev:** Tüm sinyalleri birleştirerek final karar özetini üret.

**Input:** Normalized specs + Review intel + Usage inference + Price data

**Pipeline:**
```
┌─────────────────────────────────────────────────────────────┐
│                   DECISION SYNTHESIS                         │
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │Spec Score│ + │Review    │ + │Usage Fit │ + │Price     │ │
│  │          │   │Score     │   │Score     │   │Position  │ │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘ │
│       └──────────────┴───────────────┴──────────────┘       │
│                          │                                   │
│                          ▼                                   │
│              ┌─────────────────────┐                        │
│              │ Who Should Buy /    │                        │
│              │ Who Should Avoid    │                        │
│              │ Reasoning Engine    │                        │
│              └─────────────────────┘                        │
│                          │                                   │
│                          ▼                                   │
│              ┌─────────────────────┐                        │
│              │ Decision Summary    │                        │
│              │ Generator           │                        │
│              └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Data Outputs

### 3.1 Decision Tags
```json
{
  "tags": [
    {"tag": "best_for_gaming", "confidence": 0.94},
    {"tag": "premium_build", "confidence": 0.89},
    {"tag": "heavy_device", "confidence": 0.82, "sentiment": "neutral"},
    {"tag": "expensive", "confidence": 0.95, "sentiment": "negative"},
    {"tag": "long_software_support", "confidence": 0.88, "sentiment": "positive"}
  ]
}
```

### 3.2 Confidence Scores
```json
{
  "overall_confidence": 0.87,
  "data_freshness": "2025-01-28T12:00:00Z",
  "component_confidence": {
    "specs": 0.95,
    "reviews": 0.82,
    "price": 0.91,
    "usage_inference": 0.78
  },
  "data_sources": ["gsmarena", "amazon_reviews", "nanoreview", "user_reviews"]
}
```

### 3.3 Structured Decision Summary
```json
{
  "product_id": "samsung-galaxy-s24-ultra",
  "canonical_name": "Samsung Galaxy S24 Ultra",
  
  "headline": "Profesyonel fotoğrafçılık ve uzun vadeli kullanım için en iyi Android",
  
  "who_should_buy": [
    "Mobil fotoğrafçılık tutkunları",
    "S Pen kullanan not alıcılar",
    "7 yıl güncelleme isteyen uzun vadeciler",
    "Premium Android arayanlar"
  ],
  
  "who_should_avoid": [
    "Bütçe bilincli alıcılar",
    "Kompakt telefon arayanlar",
    "Oyun odaklı kullanıcılar (ısınma sorunu)",
    "iOS ekosisteminde olanlar"
  ],
  
  "key_strengths": [
    {"point": "200MP ana kamera", "impact": "high"},
    {"point": "7 yıl yazılım desteği", "impact": "high"},
    {"point": "Titanium gövde", "impact": "medium"}
  ],
  
  "key_weaknesses": [
    {"point": "Ağır (232g)", "impact": "medium"},
    {"point": "Yüksek fiyat", "impact": "high"},
    {"point": "Uzun süreli oyunda ısınma", "impact": "medium"}
  ],
  
  "verdict": {
    "score": 8.7,
    "one_liner": "Premium fiyata premium deneyim, ama herkes için değil."
  }
}
```

### 3.4 AI-Consumable Block
```json
{
  "ai_context_block": {
    "product": "Samsung Galaxy S24 Ultra",
    "category": "flagship_smartphone",
    "price_tier": "premium",
    "release_date": "2024-01",
    
    "spec_highlights": "200MP camera, Snapdragon 8 Gen 3, 5000mAh, 6.8\" QHD+ AMOLED",
    
    "sentiment": "mostly_positive",
    "review_summary": "Excellent camera praised by 89% of reviewers. Battery life good but not best-in-class. Some complaints about weight and heat during gaming.",
    
    "best_for": ["photography", "long_term", "business"],
    "avoid_for": ["budget", "gaming_heavy", "compact_preference"],
    
    "comparison_note": "Main competitor: iPhone 15 Pro Max. Wins on camera versatility, loses on gaming performance.",
    
    "buy_signal": {
      "recommendation": "buy",
      "confidence": 0.82,
      "condition": "if budget allows and camera is priority"
    }
  }
}
```

---

## 4. Example Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. DATA INGESTION                                                    │
│    GSMArena scrape: "Samsung Galaxy S24 Ultra"                      │
│    → Raw specs: "200 MP, f/1.7, 6.8 inches, 232 g"                  │
│    → Reviews: 1247 reviews from Amazon, Reddit, YouTube             │
│    → Prices: Trendyol 89.999₺, Amazon 85.000₺, Hepsiburada 88.500₺ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. NORMALIZATION SERVICE                                            │
│    Input: "200 MP, f/1.7, 6.8 inches, 232 g"                        │
│    Output: {                                                         │
│      main_camera_mp: 200,                                           │
│      aperture: "f/1.7",                                             │
│      screen_inches: 6.8,                                            │
│      weight_grams: 232,                                             │
│      chipset_tier: "flagship",                                      │
│      variants: [{storage: 256}, {storage: 512}, {storage: 1024}]   │
│    }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. REVIEW INTELLIGENCE SERVICE                                      │
│    Input: 1247 reviews                                              │
│    Processing:                                                       │
│      - Sentiment: 78% positive                                      │
│      - Aspect extraction: camera (45%), battery (38%), weight (15%) │
│      - Risk detection: "heat during gaming" (8% mention)            │
│    Output: {pros: [...], cons: [...], risks: [...]}                 │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. USAGE INFERENCE SERVICE                                          │
│    Input: Normalized specs + Review intel                           │
│    Processing:                                                       │
│      - Camera specs → photography score: 0.95                       │
│      - Price tier → budget score: 0.15                              │
│      - Heat complaints → gaming score: 0.72                         │
│    Output: {primary: ["photography"], avoid: ["budget"]}            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. DECISION SYNTHESIS SERVICE                                        │
│    Input: All previous outputs                                       │
│    Processing:                                                       │
│      - Generate who_should_buy reasoning                            │
│      - Generate who_should_avoid reasoning                          │
│      - Create AI-consumable block                                   │
│    Output: Full Product Intelligence JSON                           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. STORAGE & CONSUMPTION                                             │
│    - Store in product_intelligence table                            │
│    - Index for search (tags, contexts)                              │
│    - Serve to AI agents via API                                     │
│    - Display on product pages                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Infrastructure Integration

```
┌─────────────────────── CURRENT PLAN ───────────────────────┐
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │             PRODUCT INTELLIGENCE ENGINE              │   │
│  │  (NEW - Bu doküman)                                  │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │              AI AGENT LAYER (Faz 2)                 │   │
│  │  - Tavsiye Agent ← PIE.ai_context_block             │   │
│  │  - Karşılaştırma Agent ← PIE.comparison_note        │   │
│  │  - Fiyat Agent ← PIE.buy_signal                     │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │              LLM ABSTRACTION (Faz 1)                │   │
│  │  - Groq / Ollama / OpenAI                           │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │              DATA LAYER (Faz 3-4)                   │   │
│  │  - PostgreSQL (products, normalized specs)          │   │
│  │  - TimescaleDB (price history)                      │   │
│  │  - product_intelligence table (PIE outputs)        │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │              SEARCH LAYER (Faz 5)                   │   │
│  │  - Typesense (index decision_tags, contexts)        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Database Schema

```sql
-- Product Intelligence outputs storage
CREATE TABLE product_intelligence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id TEXT NOT NULL UNIQUE,
  canonical_name TEXT NOT NULL,
  
  -- Normalized specs (JSONB)
  normalized_specs JSONB,
  
  -- Review intelligence
  sentiment_score DECIMAL(3,2),
  pros JSONB,
  cons JSONB,
  risks JSONB,
  
  -- Usage inference
  usage_contexts JSONB,
  primary_contexts TEXT[],
  avoid_contexts TEXT[],
  
  -- Decision synthesis
  decision_tags JSONB,
  who_should_buy TEXT[],
  who_should_avoid TEXT[],
  key_strengths JSONB,
  key_weaknesses JSONB,
  
  -- AI-consumable
  ai_context_block JSONB,
  
  -- Confidence & freshness
  overall_confidence DECIMAL(3,2),
  data_sources TEXT[],
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_review_sync TIMESTAMPTZ,
  last_price_sync TIMESTAMPTZ
);

-- Index for fast lookups
CREATE INDEX idx_pi_contexts ON product_intelligence USING GIN (primary_contexts);
CREATE INDEX idx_pi_tags ON product_intelligence USING GIN (decision_tags);
```

---

## 7. Implementation Priority

| Öncelik | Bileşen | Neden Önce? |
|---------|---------|-------------|
| **1** | Normalization Service | Diğer tüm servislerin temeli |
| **2** | Usage Inference Service | Basit rule-based ile başlanabilir |
| **3** | Decision Synthesis Service | AI agenları besleyecek |
| **4** | Review Intelligence Service | NLP gerektirir, en karmaşık |

---

## 8. Long-Term Defensibility

Bu katman KıyasGO'yu rakiplerden ayıran temel:

| Rakip | Durumu | KıyasGO PIE Avantajı |
|-------|--------|---------------------|
| Akakçe | Sadece fiyat listeler | ✅ Karar desteği |
| Cimri | Sadece fiyat karşılaştırır | ✅ Kim için uygun? |
| Amazon | Genel öneriler | ✅ Türkiye bağlamı |
| Google Shopping | Fiyat + temel bilgi | ✅ Deep analysis |

**Sonuç:** PIE = KıyasGO'nun beyin korteksi. Ham veriyi anlamlı karara dönüştürür.
