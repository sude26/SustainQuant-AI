"""
SustainaQuant AI – Hafif NLP Motoru (İnternet gerektirmez)
==========================================================
HuggingFace modelleri indirilemediğinde veya yavaş ağda
TF-IDF + kelime tabanlı duygu analizi ile çalışır.
"""

import re
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer


_POSITIVE = {
    "başarı", "tasarruf", "azaltım", "azalma", "yenilenebilir", "sürdürülebilir",
    "olumlu", "hedef", "iyileşme", "verimlilik", "positive", "growth", "reduction",
    "savings", "renewable", "sustainable", "achieved", "improved",
}
_NEGATIVE = {
    "artış", "artmaya", "gecikme", "ihlal", "ceza", "olumsuz", "risk", "çelişki", "yetersiz",
    "askıda", "tamamlanmamış", "düşüş", "olumsuz", "negative", "delay", "violation", "increase",
    "failed", "pending", "contradiction", "insufficient", "ancak", "devam etmekte",
}


class LightweightNLP:
    """İnternet indirmesi olmadan çalışan NLP motoru."""

    def __init__(self):
        self._vectorizer = HashingVectorizer(
            n_features=384,
            alternate_sign=False,
            norm="l2",
            ngram_range=(1, 2),
        )
        self._is_initialized = False
        self.mode_label = "SQ-Detect Lite (offline)"

    def detect_language(self, text: str) -> str:
        turkish_chars = set("çğıöşüÇĞİÖŞÜ")
        if any(c in turkish_chars for c in text):
            return "tr"
        return "en"

    def _tokenize(self, text: str) -> set:
        tokens = re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]+", text.lower())
        return set(tokens)

    def embed(self, text: str, lang: str = None) -> np.ndarray:
        vec = self._vectorizer.transform([text]).toarray()[0]
        return vec.astype(np.float64)

    def embed_batch(self, texts: list, lang: str = None) -> np.ndarray:
        return self._vectorizer.transform(texts).toarray().astype(np.float64)

    def _polarity_score(self, text: str) -> float:
        """Metin polaritesi: -1 (olumsuz) ile +1 (olumlu) arası."""
        text_lower = text.lower()
        pos = sum(1 for w in _POSITIVE if w in text_lower)
        neg = sum(1 for w in _NEGATIVE if w in text_lower)
        tokens = self._tokenize(text)
        pos += len(tokens & _POSITIVE)
        neg += len(tokens & _NEGATIVE)
        if pos + neg == 0:
            return 0.0
        return max(-1.0, min(1.0, (pos - neg) / (pos + neg)))

    def get_finbert_sentiment(self, text: str) -> dict:
        polarity = self._polarity_score(text)
        if polarity > 0.15:
            label, score = "positive", min(0.95, 0.55 + polarity * 0.4)
            scores = {"positive": score, "negative": 1 - score}
        elif polarity < -0.15:
            label, score = "negative", min(0.95, 0.55 + abs(polarity) * 0.4)
            scores = {"negative": score, "positive": 1 - score}
        else:
            label, score = "neutral", 0.5
            scores = {"neutral": 1.0, "positive": 0.33, "negative": 0.33}
        return {"label": label, "score": score, "all_scores": scores, "polarity": polarity}

    def warmup(self):
        self.embed("SustainQuant test metni", lang="tr")
        self._is_initialized = True
        print("✅ Hafif NLP motoru hazır (internet gerekmez).")
        return True

    @property
    def is_ready(self):
        return self._is_initialized
