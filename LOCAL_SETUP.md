# 🛠️ KiyasGO Local Setup & Testing Guide

Bu rehber, KiyasGO Projesini yerel bilgisayarınızda en güncel (Google Shopping + SerpApi) özellikleriyle çalıştırmanızı sağlar.

## 1. Hazırlık

*   **Python:** Python 3.10+ kurulu olduğundan emin olun.
*   **API Key:** Google Shopping verileri için bir **SerpApi** API key almanız önerilir (Ücretsiz plan mevcuttur).

## 2. Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyasını hazırla (.env yoksa .env.example'dan kopyalayın)
# Aşağıdaki alanları .env içinde doldurun:
# GROQ_API_KEY=...
# SERPAPI_API_KEY=...
```

## 3. Veritabanı Hazırlığı

Uygulama SQLite kullanır (`kiyasgo_dev.db`). İlk çalıştırmada tablolar otomatik oluşur ve 5 temel ürün (iPhone 16 Pro, S24 Ultra vb.) seed verisi olarak eklenir.

## 4. Uygulamayı Başlatma

```bash
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

## 5. Test Senaryoları (Hemen Deneyin! 🚀)

### 📊 AI Ürün Analizi (Gerçek Veri)
Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

1.  **Mevcut Ürün:** `/api/v1/ai/products/iphone-16-pro` endpoint'ine gidin.
2.  **Smart Fallback (Kendi Kendine Öğrenme):** Veritabanında olmayan bir ürün ID'si ile istek atın (Örn: `nothing-phone-3` veya `pixel-9-pro`).
    *   *Ne Olacak?* Sistem önce DB'de bulamayacak, sessizce SerpApi'ye gidip Google Shopping'den veriyi çekecek, DB'ye kaydedecek ve size AI analizini döndürecektir.

### 📡 Shopping Sync
*   **Canlı Arama:** `GET /api/v1/ai/shopping/search?q=macbook+pro` (Google Shopping sonuçlarını direkt döner).
*   **Toplu Sync:** `POST /api/v1/ai/shopping/sync` (Smartphone, Laptop ve Tablet kategorilerini günceller).
*   **Durum:** `GET /api/v1/ai/shopping/status` (DB'deki toplam ürün sayısını gösterir).

## 6. Gelişmiş Özellikler

*   **Compare:** `GET /api/v1/ai/compare?products=iphone-16-pro,samsung-galaxy-s24-ultra`
*   **Explain:** `GET /api/v1/ai/explain/recommendation/iphone-16-pro`

## 7. Testleri Çalıştırma

```bash
# Tüm unit testleri çalıştır (152 test)
python -m pytest tests/ --ignore=tests/integration --ignore=tests/demo --ignore=tests/jury -v --tb=short
```
