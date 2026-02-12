"""
Security Sanitizer Module
=========================
Reflexion Rule #1 (CRITICAL): Input sanitization + prompt injection koruması
Reflexion Rule #5 (CRITICAL): Uzun vadeli güvenlik (rate limiting destegi)

Bu modül tüm kullanıcı girdilerini LLM'e göndermeden önce temizler.
"""
import re
from typing import Optional


# Prompt injection kalıpları (case-insensitive)
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(everything|all|previous)",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(a|an|if)",
    r"pretend\s+(you|to\s+be)",
    r"system\s*:\s*",
    r"<\s*system\s*>",
    r"\[\s*system\s*\]",
    r"assistant\s*:\s*",
    r"\\n\s*system\s*:",
    r"REVEAL\s+(YOUR|THE)\s+(INSTRUCTIONS|PROMPT|SYSTEM)",
    r"(önceki|tüm|yukarıdaki)\s+(talimatları?|kuralları?|komutları?)\s+(unut|yoksay|atla)",
    r"sen\s+artık\s+bir",
    r"gibi\s+davran",
    r"rolünü\s+değiştir",
]

# HTML/Script injection kalıpları
HTML_PATTERNS = [
    r"<\s*script",
    r"<\s*iframe",
    r"javascript\s*:",
    r"on\w+\s*=",
    r"<\s*img\s+.*?onerror",
]

# Pre-compiled regex
_INJECTION_RE = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
_HTML_RE = [re.compile(p, re.IGNORECASE) for p in HTML_PATTERNS]

# Maximum input length
MAX_INPUT_LENGTH = 2000
MAX_PRODUCT_ID_LENGTH = 100


def sanitize_user_input(text: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    """
    Kullanıcı girdisini sanitize eder.
    
    1. Uzunluk limiti uygular
    2. Prompt injection kalıplarını tespit edip siler
    3. HTML/script injection'ı temizler
    4. Kontrolsüz unicode karakterleri kaldırır
    
    Args:
        text: Ham kullanıcı girdisi
        max_length: Maksimum karakter sınırı
        
    Returns:
        Temizlenmiş güvenli metin
    """
    if not text:
        return ""
    
    # 1. Uzunluk limiti
    text = text[:max_length]
    
    # 2. Kontrol karakterlerini kaldır (tab, newline hariç)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # 3. Prompt injection kalıplarını tespit et ve sil
    for pattern in _INJECTION_RE:
        text = pattern.sub('[FILTERED]', text)
    
    # 4. HTML/Script injection temizliği
    for pattern in _HTML_RE:
        text = pattern.sub('[FILTERED]', text)
    
    return text.strip()


def detect_injection(text: str) -> dict:
    """
    Girdi metninde prompt injection olup olmadığını tespit eder.
    
    Returns:
        {"is_safe": bool, "threats": list[str]}
    """
    if not text:
        return {"is_safe": True, "threats": []}
    
    threats = []
    
    for pattern in _INJECTION_RE:
        match = pattern.search(text)
        if match:
            threats.append(f"prompt_injection: '{match.group()}'")
    
    for pattern in _HTML_RE:
        match = pattern.search(text)
        if match:
            threats.append(f"html_injection: '{match.group()}'")
    
    if len(text) > MAX_INPUT_LENGTH:
        threats.append(f"input_too_long: {len(text)} chars (max {MAX_INPUT_LENGTH})")
    
    return {
        "is_safe": len(threats) == 0,
        "threats": threats,
    }


def validate_product_id(product_id: str) -> str:
    """
    Product ID doğrulaması. Sadece güvenli karakterler kabul edilir.
    
    Kabul: alfanumerik, tire (-), alt çizgi (_)
    Reddedilir: boşluk, özel karakterler, injection denemeleri
    
    Raises:
        ValueError: Geçersiz product_id formatı
    """
    if not product_id:
        raise ValueError("Product ID boş olamaz")
    
    if len(product_id) > MAX_PRODUCT_ID_LENGTH:
        raise ValueError(f"Product ID çok uzun (max {MAX_PRODUCT_ID_LENGTH} karakter)")
    
    # Sadece alfanumerik, tire ve alt çizgi kabul et
    if not re.match(r'^[a-zA-Z0-9\-_]+$', product_id):
        raise ValueError(f"Product ID geçersiz karakterler içeriyor: {product_id}")
    
    return product_id


def clamp_score(score: float, min_val: float = 1.0, max_val: float = 10.0) -> float:
    """
    LLM çıktısındaki puanları güvenli aralığa sınırlar.
    
    Reflexion Rule: LLM halüsinasyona karşı çıktı doğrulaması.
    """
    try:
        score = float(score)
    except (ValueError, TypeError):
        return 5.0  # Varsayılan güvenli değer
    
    return round(min(max(score, min_val), max_val), 1)


def sanitize_llm_output(data: dict, required_fields: list[str]) -> dict:
    """
    LLM çıktısını doğrulay ve eksik alanları tamamla.
    
    Args:
        data: LLM'den gelen parse edilmiş JSON
        required_fields: Zorunlu alanlar listesi
        
    Returns:
        Doğrulanmış ve tamamlanmış dictionary
    """
    if not isinstance(data, dict):
        return {field: _default_value(field) for field in required_fields}
    
    result = {}
    for field in required_fields:
        value = data.get(field)
        if value is None:
            result[field] = _default_value(field)
        else:
            result[field] = value
    
    return result


def _default_value(field: str):
    """Eksik alanlar için güvenli varsayılan değerler."""
    defaults = {
        "headline": "Ürün Analizi",
        "who_should_buy": [],
        "who_should_avoid": [],
        "key_strengths": [],
        "key_weaknesses": [],
        "verdict_text": "Analiz tamamlanamadı.",
        "verdict_score": 5.0,
    }
    return defaults.get(field, "")
