# ⚡ Commerce Signal Engine (CSE)

**Canlı ticari veriyi izleyip proprietary market sinyalleri üreten katman.**

---

## 1. Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA COLLECTORS                                │
│  [Price Scraper] [Store API] [Order Tracking] [Review Stream]       │
└────────────┬────────────┬────────────┬────────────┬─────────────────┘
             │            │            │            │
             ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     RAW DATA LAKE                                    │
│  [Price Events] [Store Events] [Delivery Events] [Stock Events]     │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   COMMERCE SIGNAL ENGINE                             │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐           │
│  │ Fake      │ │ Store     │ │ Delivery  │ │ Price     │           │
│  │ Discount  │ │ Reliab.   │ │ Perf.     │ │ Volatility│           │
│  │ Detector  │ │ Scorer    │ │ Scorer    │ │ Scorer    │           │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘           │
│        │             │             │             │                   │
│  ┌─────┴─────┐ ┌─────┴─────┐                                        │
│  │ Lifecycle │ │ Supply    │                                        │
│  │ Scorer    │ │ Risk      │                                        │
│  └─────┬─────┘ └─────┬─────┘                                        │
│        └─────────────┴───────────────────────────────┐              │
│                              │                        │              │
│                    ┌─────────▼─────────┐   ┌─────────▼─────────┐   │
│                    │   Signal Store    │   │  Signal Publisher  │   │
│                    │   (TimescaleDB)   │   │  (Event Stream)    │   │
│                    └───────────────────┘   └───────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ User UI     │    │ AI Agents   │    │ Partner API │
   │ (Badges)    │    │ (Context)   │    │ (B2B)       │
   └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 2. Signal Kataloğu

| # | Sinyal | Açıklama | Değer Aralığı | Update Freq |
|---|--------|----------|---------------|-------------|
| 1 | **fake_discount** | Sahte indirim tespiti | 0-100 (risk) | Her fiyat değişiminde |
| 2 | **store_reliability** | Satıcı güvenilirlik skoru | 0-100 | Günlük |
| 3 | **delivery_performance** | Teslimat performansı | 0-100 | Haftalık |
| 4 | **price_volatility** | Fiyat oynaklığı | 0-100 | Günlük |
| 5 | **lifecycle_stage** | Ürün yaşam döngüsü | enum | Haftalık |
| 6 | **supply_risk** | Tedarik riski | 0-100 | Günlük |

---

## 3. Signal Detayları

### 3.1 Fake Discount Detector
**Amaç:** "Sahte indirim" taktiklerini tespit et.

**Input Sources:**
- Price history (son 90 gün)
- Competitor prices (aynı ürün, farklı satıcı)
- Campaign calendar (Black Friday, 11.11 vb.)

**Scoring Algorithm:**
```
fake_discount_score = weighted_average(
  reference_price_inflation_check(30%),   // "Eski fiyat" şişirilmiş mi?
  historical_low_comparison(25%),         // Gerçekten en düşük mü?
  cross_seller_anomaly(25%),              // Diğer satıcılarla karşılaştır
  timing_pattern_check(20%)               // Kampanya öncesi fiyat artışı?
)
```

**Logic Example:**
```javascript
function detectFakeDiscount(product, currentPrice, claimedOldPrice) {
  // 1. Son 90 günün gerçek fiyat ortalaması
  const realAvgPrice = getAvgPrice(product, 90);
  
  // 2. "Eski fiyat" gerçekçi mi?
  const referenceInflation = (claimedOldPrice - realAvgPrice) / realAvgPrice;
  
  // 3. Diğer satıcılardaki fiyat
  const competitorPrices = getCompetitorPrices(product);
  const avgCompetitorPrice = average(competitorPrices);
  
  // 4. Kampanya öncesi fiyat artışı var mı?
  const preCampaignSpike = detectPreCampaignSpike(product);
  
  let riskScore = 0;
  
  if (referenceInflation > 0.3) riskScore += 35;  // %30+ şişirme
  if (currentPrice > avgCompetitorPrice) riskScore += 25;
  if (preCampaignSpike) riskScore += 25;
  if (claimedOldPrice > getHistoricalMax(product)) riskScore += 15;
  
  return {
    score: Math.min(riskScore, 100),
    is_fake: riskScore > 50,
    evidence: [...]
  };
}
```

---

### 3.2 Store Reliability Scorer
**Amaç:** Satıcı güvenilirliğini ölç.

**Input Sources:**
- User reviews & ratings
- Order completion rate
- Refund/return rate
- Response time
- Store age & history

**Scoring Algorithm:**
```
store_reliability = weighted_average(
  review_sentiment_score(30%),
  order_fulfillment_rate(25%),
  refund_rate_inverse(20%),
  response_time_score(15%),
  store_longevity_bonus(10%)
)
```

**Output:**
```json
{
  "store_id": "trendyol-official",
  "reliability_score": 87,
  "tier": "trusted",  // trusted, standard, caution, avoid
  "breakdown": {
    "reviews": 92,
    "fulfillment": 88,
    "refunds": 85,
    "response": 78,
    "age_bonus": 5
  },
  "red_flags": [],
  "last_updated": "2025-01-28T12:00:00Z"
}
```

---

### 3.3 Delivery Performance Scorer
**Amaç:** Teslimat performansını ölç.

**Input Sources:**
- Promised delivery date vs actual
- Order tracking events
- Region-specific performance
- Carrier data

**Scoring Algorithm:**
```
delivery_score = weighted_average(
  on_time_delivery_rate(40%),
  avg_delivery_speed(30%),
  damage_complaint_rate_inverse(20%),
  tracking_accuracy(10%)
)
```

---

### 3.4 Price Volatility Scorer
**Amaç:** Fiyat stabilitesini ölç.

**Input Sources:**
- Price history (7, 30, 90 gün)
- Price change frequency
- Price change magnitude

**Scoring Algorithm:**
```javascript
function calculateVolatility(priceHistory) {
  const changes = priceHistory.map((p, i) => 
    i > 0 ? Math.abs(p - priceHistory[i-1]) / priceHistory[i-1] : 0
  );
  
  const stdDev = standardDeviation(changes);
  const changeFreq = countChanges(priceHistory) / priceHistory.length;
  
  // 0 = sabit, 100 = çok oynak
  return Math.min(
    (stdDev * 100 * 0.6) + (changeFreq * 100 * 0.4),
    100
  );
}
```

**Output:**
```json
{
  "product_id": "iphone-16-pro",
  "volatility_score": 23,
  "stability": "stable",  // stable, moderate, volatile
  "trend": "declining",   // rising, stable, declining
  "weekly_change": -2.3,
  "monthly_range": {"min": 74000, "max": 78000},
  "recommendation": "wait"  // buy_now, wait, monitor
}
```

---

### 3.5 Product Lifecycle Scorer
**Amaç:** Ürünün yaşam döngüsündeki yerini belirle.

**Stages:**
| Stage | Açıklama | Tipik Davranış |
|-------|----------|----------------|
| `launch` | Yeni çıktı | Premium fiyat, stok sıkıntısı |
| `growth` | Popülerlik artıyor | Fiyat düşmeye başlıyor |
| `mature` | Pazar doymuş | Stabil fiyat, çok satıcı |
| `decline` | Yeni model geliyor | İndirimler başlıyor |
| `clearance` | Stok eritme | Derin indirimler |
| `discontinued` | Üretim bitti | Stok azalıyor |

**Input Sources:**
- Release date
- Successor product announcements
- Price trend
- Stock availability trend
- Search volume trend

**Scoring:**
```javascript
function determineLifecycleStage(product) {
  const monthsSinceLaunch = getMonthsSinceLaunch(product);
  const hasSuccessor = checkSuccessorAnnounced(product);
  const priceTrend = getPriceTrend(product, 90);
  const stockTrend = getStockTrend(product);
  
  if (monthsSinceLaunch < 2 && !hasSuccessor) return "launch";
  if (monthsSinceLaunch < 6 && priceTrend === "declining") return "growth";
  if (hasSuccessor && priceTrend === "declining") return "decline";
  if (stockTrend === "critical_low") return "clearance";
  if (stockTrend === "zero" && monthsSinceLaunch > 12) return "discontinued";
  return "mature";
}
```

---

### 3.6 Supply Risk Signals
**Amaç:** Tedarik zinciri risklerini tespit et.

**Risk Types:**
| Risk | Trigger | Severity |
|------|---------|----------|
| `stock_out` | Stok sıfır | High |
| `low_stock` | Stok azalıyor | Medium |
| `price_spike` | Ani fiyat artışı | Medium |
| `seller_exit` | Satıcı sayısı düşüyor | Low |
| `global_shortage` | Kategori geneli sorun | High |

**Input Sources:**
- Stock levels per seller
- Active seller count
- Global news (chip shortage, etc.)
- Import/customs data

---

## 4. Database Schema

```sql
-- Signal events (time-series)
CREATE TABLE commerce_signals (
  time TIMESTAMPTZ NOT NULL,
  product_id TEXT NOT NULL,
  seller_id TEXT,
  signal_type TEXT NOT NULL,  -- fake_discount, store_reliability, etc.
  score DECIMAL(5,2),
  tier TEXT,
  metadata JSONB,
  confidence DECIMAL(3,2)
);

SELECT create_hypertable('commerce_signals', 'time');

-- Aggregated signals (for fast lookup)
CREATE TABLE signal_snapshot (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id TEXT NOT NULL,
  seller_id TEXT,
  
  fake_discount_score INT,
  fake_discount_evidence JSONB,
  
  store_reliability_score INT,
  store_tier TEXT,
  
  delivery_score INT,
  
  volatility_score INT,
  volatility_tier TEXT,
  
  lifecycle_stage TEXT,
  
  supply_risk_level TEXT,
  supply_risk_signals JSONB,
  
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_signal_snapshot ON signal_snapshot(product_id, seller_id);
```

---

## 5. Update Frequency

| Signal | Frequency | Trigger |
|--------|-----------|---------|
| fake_discount | Real-time | Price change event |
| store_reliability | Daily | Batch job 03:00 |
| delivery_performance | Weekly | Batch job Sunday |
| price_volatility | Daily | After price sync |
| lifecycle_stage | Weekly | After market analysis |
| supply_risk | Daily | Stock level change |

---

## 6. Exposure Layers

### 6.1 User UI (Badges & Warnings)
```javascript
// Product card badges
<Badge type="warning" if={fake_discount_score > 50}>
  ⚠️ Şüpheli İndirim
</Badge>

<Badge type="success" if={store_reliability > 80}>
  ✅ Güvenilir Satıcı
</Badge>

<Badge type="info" if={lifecycle_stage === "decline"}>
  📉 Yeni Model Geliyor
</Badge>
```

### 6.2 AI Agents (Context Block)
```json
{
  "commerce_signals": {
    "product_id": "iphone-16-pro",
    "seller_id": "trendyol",
    "signals": {
      "fake_discount": {"score": 15, "safe": true},
      "store_reliability": {"score": 87, "tier": "trusted"},
      "price_volatility": {"score": 23, "stable": true},
      "lifecycle": "mature",
      "supply_risk": "low"
    },
    "buy_recommendation": {
      "safe_to_buy": true,
      "confidence": 0.89,
      "warnings": []
    }
  }
}
```

### 6.3 Partner API (B2B)
```
GET /api/v1/signals/{product_id}
Authorization: Bearer {api_key}

Response:
{
  "product_id": "iphone-16-pro",
  "timestamp": "2025-01-28T12:00:00Z",
  "signals": {
    "fake_discount": {...},
    "store_reliability": {...},
    ...
  },
  "meta": {
    "data_sources": ["price_history", "reviews", "stock_api"],
    "freshness": "2h"
  }
}
```

---

## 7. Example Complete Signal Object

```json
{
  "product_id": "samsung-galaxy-s24-ultra",
  "seller_id": "amazon-tr",
  "generated_at": "2025-01-28T14:00:00Z",
  
  "signals": {
    "fake_discount": {
      "score": 72,
      "is_fake": true,
      "claimed_discount": 25,
      "real_discount": 8,
      "evidence": [
        "Reference price inflated by 22% vs 90-day avg",
        "Pre-campaign spike detected 5 days before Black Friday"
      ],
      "confidence": 0.88
    },
    
    "store_reliability": {
      "score": 91,
      "tier": "trusted",
      "breakdown": {
        "reviews": 93,
        "fulfillment": 89,
        "refunds": 88,
        "response": 94
      },
      "red_flags": [],
      "confidence": 0.95
    },
    
    "delivery_performance": {
      "score": 78,
      "avg_days": 2.3,
      "on_time_rate": 0.89,
      "region_variance": "low",
      "confidence": 0.82
    },
    
    "price_volatility": {
      "score": 45,
      "tier": "moderate",
      "trend": "declining",
      "30d_range": {"min": 82000, "max": 89999},
      "recommendation": "wait_2_weeks",
      "confidence": 0.79
    },
    
    "lifecycle_stage": {
      "stage": "mature",
      "months_since_launch": 12,
      "successor_announced": false,
      "expected_replacement": "Q1 2026",
      "confidence": 0.85
    },
    
    "supply_risk": {
      "level": "low",
      "active_sellers": 47,
      "stock_status": "abundant",
      "alerts": [],
      "confidence": 0.92
    }
  },
  
  "composite_score": {
    "buy_safety": 68,
    "value_score": 72,
    "timing_score": 55,
    "overall": "proceed_with_caution"
  },
  
  "user_facing": {
    "badges": ["⚠️ Şüpheli İndirim"],
    "warnings": ["Bu indirim gerçeği yansıtmıyor olabilir"],
    "tips": ["Fiyat 2 hafta içinde düşebilir"]
  }
}
```

---

## 8. Long-Term Defensibility

| Rakip | KıyasGO CSE Avantajı |
|-------|---------------------|
| Akakçe | ❌ Sadece fiyat listeler → ✅ Sinyal üretiriz |
| Cimri | ❌ Geçmiş yok → ✅ 90 gün trend analizi |
| Amazon | ❌ Kendi satıcıları → ✅ Cross-market signals |
| Trendyol | ❌ Sadece kendi verisi → ✅ Bağımsız analiz |

**Moat:** Zaman geçtikçe veri birikir → Sinyaller daha doğru → Kullanıcılar güvenir → Daha çok veri → **Network effect**

---

## 9. Integration with Infrastructure Plan

```
┌──────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE EVOLUTION                     │
│                                                              │
│  Faz 1: LLM Abstraction                                      │
│  Faz 1.5: Product Intelligence Engine ←──┐                   │
│  Faz 1.6: Commerce Signal Engine ◄───────┤ YENİ              │
│  Faz 2: Agent Infrastructure                                 │
│  Faz 3: Database Migration                                   │
│  Faz 4: Price History DB (CSE için kritik)                   │
│  Faz 5: Search Engine                                        │
└──────────────────────────────────────────────────────────────┘
```

**CSE, PIE'yi tamamlar:**
- PIE = Ürün analizi (specs, reviews, usage)
- CSE = Pazar analizi (fiyat, satıcı, tedarik)
- İkisi birleşince = Tam karar desteği
