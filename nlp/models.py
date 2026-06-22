"""
SustainaQuant AI – NLP Model Yönetimi
=======================================
FinBERT (Finansal İngilizce) ve BERTürk (Türkçe) model entegrasyonu.
Sentence Transformers ile metin → vektör dönüşümü.

Rapor §3: "Finansal terminolojiye göre ince ayarı yapılmış büyük dil modelleri"
Rapor §3: "Türkçe doğal dil işleme modelleri (BERTürk) ile entegre"
"""

import numpy as np
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    FINBERT_MODEL_ID,
    SENTENCE_TRANSFORMER_EN,
    SENTENCE_TRANSFORMER_TR,
    MODEL_CACHE_DIR,
)


class SustainaQuantNLP:
    """
    Ana NLP model yönetim sınıfı.
    Lazy loading ile modeller sadece ihtiyaç duyulduğunda yüklenir.
    """

    def __init__(self):
        self._sentence_model_tr = None
        self._sentence_model_en = None
        self._finbert_pipeline = None
        self._is_initialized = False

        # Cache dizinini oluştur
        MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def sentence_model_tr(self):
        """Türkçe Sentence Transformer – Lazy loading."""
        if self._sentence_model_tr is None:
            print(f"📥 Türkçe model yükleniyor: {SENTENCE_TRANSFORMER_TR}...")
            from sentence_transformers import SentenceTransformer
            try:
                self._sentence_model_tr = SentenceTransformer(
                    SENTENCE_TRANSFORMER_TR,
                    cache_folder=str(MODEL_CACHE_DIR)
                )
                print("✅ Türkçe model hazır.")
            except Exception as e:
                print(f"⚠️ Türkçe model yüklenemedi ({e}), fallback: {SENTENCE_TRANSFORMER_EN}")
                self._sentence_model_tr = self.sentence_model_en
        return self._sentence_model_tr

    @property
    def sentence_model_en(self):
        """İngilizce/Genel Sentence Transformer – Lazy loading."""
        if self._sentence_model_en is None:
            print(f"📥 Genel model yükleniyor: {SENTENCE_TRANSFORMER_EN}...")
            from sentence_transformers import SentenceTransformer
            self._sentence_model_en = SentenceTransformer(
                SENTENCE_TRANSFORMER_EN,
                cache_folder=str(MODEL_CACHE_DIR)
            )
            print("✅ Genel model hazır.")
        return self._sentence_model_en

    @property
    def finbert_pipeline(self):
        """FinBERT duygu analizi pipeline'ı – Lazy loading."""
        if self._finbert_pipeline is None:
            print(f"📥 FinBERT yükleniyor: {FINBERT_MODEL_ID}...")
            from transformers import pipeline as hf_pipeline
            try:
                self._finbert_pipeline = hf_pipeline(
                    "sentiment-analysis",
                    model=FINBERT_MODEL_ID,
                    top_k=None,
                    truncation=True,
                    max_length=512,
                )
                print("✅ FinBERT hazır.")
            except Exception as e:
                print(f"⚠️ FinBERT yüklenemedi: {e}")
                self._finbert_pipeline = None
        return self._finbert_pipeline

    def detect_language(self, text: str) -> str:
        """Metin dilini algılar."""
        try:
            from langdetect import detect
            lang = detect(text)
            return "tr" if lang == "tr" else "en"
        except Exception:
            # Basit Türkçe karakter kontrolü
            turkish_chars = set("çğıöşüÇĞİÖŞÜ")
            if any(c in turkish_chars for c in text):
                return "tr"
            return "en"

    def get_model_for_language(self, lang: str):
        """Dile göre uygun Sentence Transformer modelini döndürür."""
        if lang == "tr":
            return self.sentence_model_tr
        return self.sentence_model_en

    def embed(self, text: str, lang: str = None) -> np.ndarray:
        """
        Metni vektöre dönüştürür (embedding).

        Rapor §3: "Şirketin raporundaki iddiasını anlamsal bir vektöre dönüştürür"

        Args:
            text: Vektöre çevrilecek metin
            lang: Dil kodu ('tr' veya 'en'). None ise otomatik algılanır.

        Returns:
            numpy ndarray – Metin vektörü
        """
        if lang is None:
            lang = self.detect_language(text)

        model = self.get_model_for_language(lang)
        embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding

    def embed_batch(self, texts: list, lang: str = None) -> np.ndarray:
        """
        Birden fazla metni toplu olarak vektöre dönüştürür.

        Args:
            texts: Metin listesi
            lang: Dil kodu. None ise ilk metinden otomatik algılanır.

        Returns:
            numpy ndarray – (N, embedding_dim) boyutunda matris
        """
        if lang is None and texts:
            lang = self.detect_language(texts[0])

        model = self.get_model_for_language(lang)
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings

    def get_finbert_sentiment(self, text: str) -> dict:
        """
        FinBERT ile finansal duygu analizi yapar.

        Rapor §3: "Duygu Analizi (Sentiment Analysis)"

        Returns:
            {"label": "positive/negative/neutral", "score": float, "all_scores": dict}
        """
        pipeline = self.finbert_pipeline
        if pipeline is None:
            return {"label": "neutral", "score": 0.5, "all_scores": {}}

        try:
            # FinBERT max 512 token kabul eder
            truncated = text[:1500]
            results = pipeline(truncated)

            # top_k=None ile results: list[dict] döner
            # Her dict: {"label": "positive", "score": 0.95}
            scores_list = results if isinstance(results[0], dict) else results[0]
            all_scores = {r["label"]: r["score"] for r in scores_list}

            # En yüksek skorlu etiketi bul
            best = max(scores_list, key=lambda x: x["score"])
            return {
                "label": best["label"],
                "score": best["score"],
                "all_scores": all_scores,
            }
        except Exception as e:
            print(f"⚠️ FinBERT analiz hatası: {e}")
            return {"label": "neutral", "score": 0.5, "all_scores": {}}

    def warmup(self):
        """
        Tüm modelleri önceden yükler (startup sırasında).
        Dashboard veya API başlatılırken çağrılır.
        """
        print("🔥 Model ısınma (warmup) başlatılıyor...")
        _ = self.sentence_model_tr
        _ = self.sentence_model_en
        _ = self.finbert_pipeline

        # Test embedding
        test_vec = self.embed("Test metni", lang="tr")
        print(f"   Embedding boyutu: {test_vec.shape}")

        self._is_initialized = True
        print("✅ Tüm modeller hazır ve yüklendi.")
        return True

    @property
    def is_ready(self):
        """Modellerin yüklenip yüklenmediğini kontrol eder."""
        return self._is_initialized
