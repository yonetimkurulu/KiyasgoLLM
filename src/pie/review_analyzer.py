"""
Review Analyzer - Sentiment Engine
SerpApi reviews_results verisini alarak Aspect-Based Sentiment Analysis (ABSA) uygular.

Pipeline:
1. Parse: Ham SerpApi reviews_results → yapılandırılmış review listesi
2. Filter: Sahte/boş/taraflı yorumları filtrele
3. Analyze: LLM ile ABSA veya rule-based fallback
"""
import re
from typing import Optional
import structlog

from src.config import get_settings
from src.security.sanitizer import sanitize_user_input

logger = structlog.get_logger()


class ReviewAnalyzer:
    """
    Aspect-Based Sentiment Analysis engine for product reviews.
    
    SerpApi'den gelen reviews_results verisini analiz ederek
    her yorum için aspect etiketleri ve genel sentiment_score üretir.
    """

    def __init__(self):
        self._settings = None
        self._hollow_pattern = None

    @property
    def settings(self):
        """Lazy-load settings to avoid import-time side effects."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    @property
    def hollow_pattern(self) -> re.Pattern:
        """Compiled regex for hollow/generic review detection."""
        if self._hollow_pattern is None:
            self._hollow_pattern = re.compile(
                self.settings.review_hollow_patterns,
                re.IGNORECASE,
            )
        return self._hollow_pattern

    # ------------------------------------------------------------------
    # 1. Parse
    # ------------------------------------------------------------------

    def parse_reviews(self, reviews_results: list) -> list[dict]:
        """
        SerpApi reviews_results formatından yapılandırılmış review listesi çıkar.

        Args:
            reviews_results: SerpApi'den gelen ham review listesi.
                Her eleman: { "rating": 4, "snippet": "...", "title": "...", ... }

        Returns:
            Normalize edilmiş review dict listesi.
        """
        if not reviews_results:
            return []

        parsed: list[dict] = []
        for raw in reviews_results:
            if not isinstance(raw, dict):
                continue

            rating = self._normalize_rating(raw.get("rating"))
            snippet = (raw.get("snippet") or "").strip()
            title = (raw.get("title") or "").strip()

            parsed.append({
                "rating": rating,
                "snippet": snippet,
                "title": title,
                "source": raw.get("source", ""),
                "date": raw.get("date", ""),
            })

        logger.debug("reviews_parsed", count=len(parsed))
        return parsed

    # ------------------------------------------------------------------
    # 2. Filter
    # ------------------------------------------------------------------

    def filter_reviews(self, reviews: list[dict]) -> list[dict]:
        """
        Sahte, boş veya aşırı taraflı yorumları filtreler.

        Filtreleme kriterleri:
        - Snippet çok kısa (< review_min_snippet_length)
        - İçi boş / jenerik yorumlar (sadece "çok iyi", "harika" vs.)
        - Uç puanlı ama kısa yorumlar (5★ veya 1★ ama < 20 karakter)
        - Mükerrer (duplicate) snippet'lar
        """
        if not reviews:
            return []

        min_len = self.settings.review_min_snippet_length
        filtered: list[dict] = []
        seen_snippets: set[str] = set()

        for review in reviews:
            snippet = review.get("snippet", "")
            rating = review.get("rating")

            # 1) Çok kısa snippet — anlamsız
            if len(snippet) < min_len:
                logger.debug("review_filtered", reason="too_short", snippet=snippet[:30])
                continue

            # 2) İçi boş / jenerik yorum (tüm metin sadece bir jenerik kalıp)
            if self._is_hollow(snippet):
                logger.debug("review_filtered", reason="hollow", snippet=snippet[:30])
                continue

            # 3) Uç puan + kısa metin — spam riski
            if rating is not None and rating in (1, 5) and len(snippet) < 20:
                logger.debug("review_filtered", reason="extreme_short", rating=rating)
                continue

            # 4) Mükerrer yorum
            norm = snippet.lower().strip()
            if norm in seen_snippets:
                logger.debug("review_filtered", reason="duplicate")
                continue
            seen_snippets.add(norm)

            filtered.append(review)

        logger.info(
            "reviews_filtered",
            original=len(reviews),
            kept=len(filtered),
            removed=len(reviews) - len(filtered),
        )
        return filtered

    # ------------------------------------------------------------------
    # 3. Analyze
    # ------------------------------------------------------------------

    async def analyze_sentiment(
        self,
        reviews_results: list,
        use_llm: bool = True,
    ) -> dict:
        """
        Tam analiz pipeline'ı: parse → filter → ABSA.

        Args:
            reviews_results: SerpApi'den gelen ham review listesi.
            use_llm: True ise LLM ile analiz, False ise rule-based.

        Returns:
            {
                "overall_sentiment_score": float (0.0-1.0),
                "aspects": [
                    {"aspect": "Pil Ömrü", "score": 1, "mention_count": 3},
                    ...
                ],
                "review_count": int,
                "filtered_count": int,
                "confidence": float,
            }
        """
        parsed = self.parse_reviews(reviews_results)
        filtered = self.filter_reviews(parsed)

        total_parsed = len(parsed)
        total_filtered = total_parsed - len(filtered)

        if not filtered:
            return self._empty_result(total_parsed, total_filtered)

        # Batch limit
        batch = filtered[: self.settings.review_max_batch_size]

        if use_llm:
            try:
                result = await self._analyze_with_llm(batch)
                result["review_count"] = len(batch)
                result["filtered_count"] = total_filtered
                return result
            except Exception as exc:
                logger.warning("llm_absa_failed", error=str(exc))
                # Fall through to rule-based

        result = self._rule_based_fallback(batch)
        result["review_count"] = len(batch)
        result["filtered_count"] = total_filtered
        return result

    # ------------------------------------------------------------------
    # LLM-powered ABSA
    # ------------------------------------------------------------------

    async def _analyze_with_llm(self, reviews: list[dict]) -> dict:
        """AdvancedLLMProvider ile ABSA analizi yapar."""
        from src.llm.advanced_provider import get_advanced_llm
        from src.llm.prompts import PromptTemplates

        advanced_llm = get_advanced_llm()
        prompts = PromptTemplates()

        # Sanitize review texts before sending to LLM
        safe_reviews = []
        for r in reviews:
            safe_reviews.append({
                "rating": r.get("rating"),
                "snippet": sanitize_user_input(r.get("snippet", "")),
                "title": sanitize_user_input(r.get("title", "")),
            })

        prompt = prompts.review_absa_prompt(safe_reviews)

        schema = {
            "overall_sentiment_score": 0.78,
            "aspects": [
                {"aspect": "Pil Ömrü", "score": 1, "mention_count": 3},
                {"aspect": "Ekran", "score": -1, "mention_count": 2},
            ],
            "confidence": 0.85,
        }

        data = await advanced_llm.generate_structured(
            prompt=prompt,
            schema=schema,
            system_prompt=prompts.system_prompt_turkish(),
        )

        # Validate and clamp
        sentiment_score = self._clamp_01(data.get("overall_sentiment_score", 0.5))
        aspects = self._validate_aspects(data.get("aspects", []))
        confidence = self._clamp_01(data.get("confidence", 0.7))

        return {
            "overall_sentiment_score": sentiment_score,
            "aspects": aspects,
            "confidence": confidence,
            "analysis_type": "llm_absa",
        }

    # ------------------------------------------------------------------
    # Rule-based fallback
    # ------------------------------------------------------------------

    # Keyword → (aspect, polarity) mappings — Turkish
    _ASPECT_KEYWORDS: dict[str, list[tuple[str, int]]] = {
        # Battery
        "pil": [("Pil Ömrü", 0)],
        "batarya": [("Pil Ömrü", 0)],
        "şarj": [("Pil Ömrü", 0)],
        # Screen
        "ekran": [("Ekran", 0)],
        "görüntü": [("Ekran", 0)],
        "parlaklık": [("Ekran", 0)],
        # Camera
        "kamera": [("Kamera", 0)],
        "fotoğraf": [("Kamera", 0)],
        "çekim": [("Kamera", 0)],
        # Performance
        "hız": [("Performans", 0)],
        "performans": [("Performans", 0)],
        "kasma": [("Performans", -1)],
        "yavaş": [("Performans", -1)],
        "hızlı": [("Performans", 1)],
        # Build quality
        "tasarım": [("Tasarım", 0)],
        "kalite": [("Yapı Kalitesi", 0)],
        "malzeme": [("Yapı Kalitesi", 0)],
        # Price
        "fiyat": [("Fiyat/Performans", 0)],
        "pahalı": [("Fiyat/Performans", -1)],
        "uygun": [("Fiyat/Performans", 1)],
        "değer": [("Fiyat/Performans", 0)],
    }

    # Simple polarity words
    _POSITIVE_WORDS = {
        "iyi", "güzel", "harika", "mükemmel", "süper", "muhteşem",
        "kaliteli", "başarılı", "beğendim", "memnun", "tatmin",
        "parlak", "net", "keskin", "uzun", "dayanıklı",
    }

    _NEGATIVE_WORDS = {
        "kötü", "berbat", "vasat", "yetersiz", "düşük", "zayıf",
        "sorunlu", "pişman", "hayal kırıklığı", "rezalet",
        "donma", "kasma", "yavaş", "çizik", "kırık",
    }

    def _rule_based_fallback(self, reviews: list[dict]) -> dict:
        """Keyword tabanlı basit ABSA — LLM kullanılamadığında."""
        aspect_scores: dict[str, list[int]] = {}
        total_positive = 0
        total_negative = 0

        for review in reviews:
            text = (review.get("snippet", "") + " " + review.get("title", "")).lower()
            rating = review.get("rating")

            # Determine review-level polarity from rating
            if rating is not None:
                if rating >= 4:
                    total_positive += 1
                elif rating <= 2:
                    total_negative += 1
            
            review_polarity = self._text_polarity(text, rating)

            # Extract aspects mentioned
            for keyword, mappings in self._ASPECT_KEYWORDS.items():
                if keyword in text:
                    for aspect_name, forced_polarity in mappings:
                        polarity = forced_polarity if forced_polarity != 0 else review_polarity
                        aspect_scores.setdefault(aspect_name, []).append(polarity)

        # Build aspect list
        aspects = []
        for aspect_name, polarities in aspect_scores.items():
            avg = sum(polarities) / len(polarities) if polarities else 0
            if avg > 0.2:
                score = 1
            elif avg < -0.2:
                score = -1
            else:
                score = 0
            aspects.append({
                "aspect": aspect_name,
                "score": score,
                "mention_count": len(polarities),
            })

        # Sort by mention count descending
        aspects.sort(key=lambda a: a["mention_count"], reverse=True)

        # Overall sentiment score
        total = len(reviews)
        if total > 0:
            sentiment_score = (total_positive - total_negative) / total * 0.5 + 0.5
        else:
            sentiment_score = 0.5

        return {
            "overall_sentiment_score": round(max(0.0, min(1.0, sentiment_score)), 2),
            "aspects": aspects,
            "confidence": 0.5,  # Lower confidence for rule-based
            "analysis_type": "rule_based",
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _text_polarity(self, text: str, rating: Optional[int] = None) -> int:
        """Determine polarity of a text snippet (-1, 0, +1)."""
        pos_count = sum(1 for w in self._POSITIVE_WORDS if w in text)
        neg_count = sum(1 for w in self._NEGATIVE_WORDS if w in text)

        # Rating override
        if rating is not None:
            if rating >= 4:
                pos_count += 2
            elif rating <= 2:
                neg_count += 2

        if pos_count > neg_count:
            return 1
        elif neg_count > pos_count:
            return -1
        return 0

    def _is_hollow(self, snippet: str) -> bool:
        """Check if a review is hollow/generic (entire text is just a pattern)."""
        cleaned = snippet.strip()
        # If the whole text (ignoring punctuation) matches a hollow pattern, it's hollow
        text_without_punct = re.sub(r"[^\w\s]", "", cleaned).strip()
        if len(text_without_punct) == 0:
            return True
        # Full-match check: the entire text is just a generic phrase
        return bool(self.hollow_pattern.fullmatch(text_without_punct))

    @staticmethod
    def _normalize_rating(raw_rating) -> Optional[int]:
        """Normalize any rating to 1-5 scale."""
        if raw_rating is None:
            return None
        try:
            val = float(raw_rating)
        except (ValueError, TypeError):
            return None

        # If scale is 1-10, divide by 2
        if val > 5:
            val = val / 2

        return max(1, min(5, round(val)))

    @staticmethod
    def _clamp_01(value) -> float:
        """Clamp a numeric value to [0.0, 1.0]."""
        try:
            v = float(value)
        except (ValueError, TypeError):
            return 0.5
        return round(max(0.0, min(1.0, v)), 2)

    @staticmethod
    def _validate_aspects(aspects: list) -> list[dict]:
        """Validate and clean aspect list from LLM output."""
        if not isinstance(aspects, list):
            return []

        valid = []
        for a in aspects:
            if not isinstance(a, dict):
                continue
            name = a.get("aspect", "")
            if not name:
                continue
            score = a.get("score", 0)
            if score not in (-1, 0, 1):
                score = 1 if score > 0 else (-1 if score < 0 else 0)
            mention_count = a.get("mention_count", 1)
            if not isinstance(mention_count, int) or mention_count < 0:
                mention_count = 1
            valid.append({
                "aspect": str(name),
                "score": score,
                "mention_count": mention_count,
            })
        return valid

    @staticmethod
    def _empty_result(review_count: int = 0, filtered_count: int = 0) -> dict:
        """Return an empty/neutral result when no reviews are available."""
        return {
            "overall_sentiment_score": 0.5,
            "aspects": [],
            "review_count": review_count,
            "filtered_count": filtered_count,
            "confidence": 0.0,
            "analysis_type": "no_data",
        }
