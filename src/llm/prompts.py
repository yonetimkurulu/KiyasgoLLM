"""
LLM Prompt Templates
Türkçe optimize edilmiş prompt şablonları.
"""


class PromptTemplates:
    """
    Türkçe prompt templates for KıyasGO.
    
    All prompts are optimized for:
    - Turkish language output
    - Structured responses
    - Commerce/comparison context
    """
    
    def system_prompt_turkish(self) -> str:
        """Base system prompt for Turkish commerce AI."""
        return """Sen KıyasGO için çalışan bir Türk alışveriş zekası asistanısın.

Görevlerin:
1. Ürün analizleri yapmak
2. Ürünleri karşılaştırmak
3. Kullanıcılara doğru ürün önerileri sunmak
4. Türk pazarına özel öneriler vermek

Kurallar:
- Her zaman Türkçe yanıt ver
- Fiyatları TL (₺) cinsinden belirt
- Objektif ve tarafsız ol
- Veriye dayalı öneriler sun
- Kısa ve öz yanıtlar ver
- Karşılaştırmalarda her iki tarafın artı/eksilerini söyle"""
    
    def product_analysis(self, product_data: dict) -> str:
        """Generate product analysis prompt."""
        name = product_data.get("name", "Ürün")
        specs = product_data.get("specs", {})
        price = product_data.get("price", 0)
        reviews = product_data.get("reviews", [])
        
        specs_text = "\n".join([f"- {k}: {v}" for k, v in specs.items()])
        reviews_text = "\n".join([f"- {r.get('text', '')}" for r in reviews[:5]])
        
        return f"""Aşağıdaki ürün için kısa bir analiz yap:

Ürün: {name}
Fiyat: ₺{price:,}

Özellikler:
{specs_text}

Kullanıcı Yorumları:
{reviews_text}

Lütfen şu formatla analiz et:
1. Tek cümlelik özet (headline)
2. Kim almalı? (3 madde)
3. Kim almamalı? (3 madde)
4. Güçlü yanlar (3 madde)
5. Zayıf yanlar (3 madde)
6. Sonuç puanı (1-10)"""
    
    def product_comparison(self, products: list[dict]) -> str:
        """Generate product comparison prompt."""
        product_texts = []
        for i, p in enumerate(products, 1):
            name = p.get("name", f"Ürün {i}")
            price = p.get("price", 0)
            specs = p.get("specs", {})
            specs_text = ", ".join([f"{k}: {v}" for k, v in specs.items()])
            product_texts.append(f"{i}. {name} (₺{price:,}): {specs_text}")
        
        products_str = "\n".join(product_texts)
        
        return f"""Aşağıdaki ürünleri karşılaştır:

{products_str}

Lütfen şu formatta karşılaştır:
1. Her kategoride kazanan (kamera, performans, batarya, fiyat)
2. Genel kazanan
3. Hangi kullanıcı için hangisi uygun
4. Son tavsiye (1 cümle)"""
    
    def product_recommendation(
        self,
        context: str,
        category: str,
        budget: int,
        products: list[dict],
    ) -> str:
        """Generate product recommendation prompt."""
        context_descriptions = {
            "gaming": "mobil oyun oynamak",
            "photography": "fotoğrafçılık",
            "student": "öğrenci kullanımı",
            "business": "iş amaçlı kullanım",
            "budget": "bütçe dostu seçenek",
            "creator": "içerik üretimi",
            "long_term": "uzun vadeli kullanım",
        }
        
        context_desc = context_descriptions.get(context, context)
        
        product_list = "\n".join([
            f"- {p.get('name', 'Ürün')}: ₺{p.get('price', 0):,}"
            for p in products
        ])
        
        budget_text = f"Bütçe: ₺{budget:,}" if budget else "Bütçe sınırlaması yok"
        
        return f"""Kullanıcı için en uygun ürünü öner:

Kullanım Amacı: {context_desc}
Kategori: {category}
{budget_text}

Mevcut Seçenekler:
{product_list}

Lütfen şu formatta öner:
1. En uygun ürün ve neden
2. Alternatif seçenek
3. Dikkat edilmesi gerekenler"""
    
    def explain_signal(self, signal_type: str, signal_data: dict) -> str:
        """Generate signal explanation prompt."""
        signal_descriptions = {
            "fake_discount": "sahte indirim tespiti",
            "store_reliability": "satıcı güvenilirliği",
            "price_volatility": "fiyat oynaklığı",
            "lifecycle": "ürün yaşam döngüsü",
            "supply_risk": "tedarik riski",
        }
        
        signal_desc = signal_descriptions.get(signal_type, signal_type)
        signal_json = str(signal_data)
        
        return f"""Aşağıdaki ticari sinyali kullanıcıya açıkla:

Sinyal Türü: {signal_desc}
Veri: {signal_json}

Kullanıcının anlayabileceği basit bir dille açıkla:
1. Bu sinyal ne anlama geliyor?
2. Kullanıcı ne yapmalı?
3. Dikkat etmesi gereken şeyler"""
