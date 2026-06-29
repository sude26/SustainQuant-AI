"""
SustainaQuant AI – Kosinüs Benzerliği Motoru
===============================================
Rapor §3: "İddia ve gerçeklik arasındaki sapma (risk skoru), bilimsel olarak
           Kosinüs Benzerliği formülü ile hesaplanmaktadır; skor düştükçe
           şirket beyanı ile eylemi arasındaki çelişki matematiksel olarak
           ispatlanmış olur."

Formül:
    similarity = cos(θ) = (A · B) / (||A|| × ||B||)
    risk_score = (1 - similarity) × 100
"""

import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nlp.models import create_nlp_engine


class CosineSimilarityEngine:
    """
    Kosinüs Benzerliği hesaplama motoru.
    Rapordaki "Söylem-Eylem Boşluğu" algoritmasının matematiksel çekirdeği.
    """

    def __init__(self, nlp_model=None):
        self.nlp = nlp_model or create_nlp_engine()

    def compute_vectors(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        İki vektör arasındaki kosinüs benzerliğini hesaplar.

        cos(θ) = (A · B) / (||A|| × ||B||)

        Args:
            vec_a: Birinci vektör (söylem embedding)
            vec_b: İkinci vektör (eylem embedding)

        Returns:
            float: -1 ile 1 arası benzerlik skoru
                   1 = tam uyum, 0 = ilişkisiz, -1 = tam zıt
        """
        # Vektörleri 2D'ye çevir (sklearn gereksinimleri)
        a = vec_a.reshape(1, -1)
        b = vec_b.reshape(1, -1)
        similarity = sklearn_cosine(a, b)[0][0]
        return float(similarity)

    def compute(self, text_a: str, text_b: str, lang: str = None) -> dict:
        """
        İki metin arasındaki kosinüs benzerliğini hesaplar.

        Rapor §3: "şirketin raporundaki iddiasını anlamsal bir vektöre dönüştürür
                    ve dış kaynaklardan gelen bağımsız haberi de vektörel olarak
                    analiz edip, iki veri seti arasındaki anlamsal çelişkiyi
                    'Yeşil Aklama Anomalisi' olarak etiketler."

        Args:
            text_a: Söylem metni (rapordaki iddia)
            text_b: Eylem metni (bağımsız kaynak bulgusu)
            lang: Dil kodu. None ise otomatik algılanır.

        Returns:
            {
                "similarity": float (-1 ile 1),
                "distance": float (0 ile 2),
                "risk_score": float (0-100),
                "interpretation": str
            }
        """
        # Metinleri vektörlere dönüştür
        vec_a = self.nlp.embed(text_a, lang=lang)
        vec_b = self.nlp.embed(text_b, lang=lang)

        # Kosinüs benzerliği hesapla
        similarity = self.compute_vectors(vec_a, vec_b)

        # Risk skoru: benzerlik düştükçe risk artar
        # similarity 1 ise → risk 0 (tam uyum)
        # similarity 0 ise → risk 100 (tamamen ilişkisiz)
        # similarity negatif ise → risk 100 (zıt anlam)
        risk_score = max(0, min(100, (1 - similarity) * 100))

        # Kosinüs mesafesi
        distance = 1 - similarity

        # Yorumlama
        if similarity >= 0.75:
            interpretation = "Yüksek anlamsal uyum. Söylem eylemle tutarlı."
        elif similarity >= 0.50:
            interpretation = "Orta düzeyde uyum. Bazı kapsam farklılıkları mevcut."
        elif similarity >= 0.25:
            interpretation = "Düşük uyum. Söylem ve eylem farklı konulara odaklanıyor."
        else:
            interpretation = "Anlamsal çelişki tespit edildi. Yüksek yeşil aklama riski."

        return {
            "similarity": round(similarity, 4),
            "distance": round(distance, 4),
            "risk_score": round(risk_score, 2),
            "interpretation": interpretation,
            "vector_dim": vec_a.shape[0],
        }

    def compute_batch(self, pairs: list, lang: str = None) -> list:
        """
        Birden fazla metin çifti için toplu benzerlik hesaplar.

        Args:
            pairs: [(text_a, text_b), ...] formatında metin çiftleri
            lang: Dil kodu

        Returns:
            Liste: Her çift için compute() sonucu
        """
        results = []
        for text_a, text_b in pairs:
            result = self.compute(text_a, text_b, lang=lang)
            results.append(result)
        return results

    def compute_matrix(self, texts_a: list, texts_b: list, lang: str = None) -> np.ndarray:
        """
        İki metin listesi arasındaki çapraz benzerlik matrisini hesaplar.
        Portföy tarama (batch analiz) için kullanılır.

        Args:
            texts_a: Söylem metinleri listesi
            texts_b: Eylem metinleri listesi

        Returns:
            numpy ndarray: (len(texts_a), len(texts_b)) boyutunda benzerlik matrisi
        """
        embeddings_a = self.nlp.embed_batch(texts_a, lang=lang)
        embeddings_b = self.nlp.embed_batch(texts_b, lang=lang)
        matrix = sklearn_cosine(embeddings_a, embeddings_b)
        return matrix
