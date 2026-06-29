"""
SustainaQuant AI – Duygu Analizi (Sentiment Analysis)
======================================================
Rapor §3: "NLP motorunda Duygu Analizi (Sentiment Analysis) işlemine tabi tutulur"

Söylem ve eylem metinlerinin duygusal tonunu karşılaştırarak
ek bir risk boyutu ekler. Söylem çok pozitif ama eylem negatif ise
→ yüksek yeşil aklama riski.
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nlp.models import create_nlp_engine


class SentimentAnalyzer:
    """
    Duygu Analizi motoru.
    Söylem vs. eylem duygusal ton karşılaştırması yapar.
    """

    def __init__(self, nlp_model=None):
        self.nlp = nlp_model or create_nlp_engine()

    def analyze_sentiment(self, text: str) -> dict:
        """
        Metin için duygu analizi yapar.

        Returns:
            {
                "label": "positive/negative/neutral",
                "score": float (0-1),
                "polarity": float (-1 ile +1 arası)
            }
        """
        result = self.nlp.get_finbert_sentiment(text)

        # Polarite: modelden geldiyse kullan, yoksa skorlardan hesapla
        all_scores = result.get("all_scores", {})
        if "polarity" in result:
            polarity = result["polarity"]
        else:
            positive = all_scores.get("positive", 0.33)
            negative = all_scores.get("negative", 0.33)
            polarity = positive - negative

        return {
            "label": result["label"],
            "score": result["score"],
            "polarity": polarity,
            "all_scores": all_scores,
        }

    def compare_sentiments(self, soylem: str, eylem: str) -> dict:
        """
        Söylem ve eylem arasındaki duygu uyumsuzluğunu hesaplar.

        Mantık:
        - Söylem pozitif + Eylem pozitif → Uyum (düşük risk)
        - Söylem pozitif + Eylem negatif → Yüksek çelişki (yüksek risk)
        - Söylem nötr + Eylem negatif → Orta risk
        - Söylem negatif + Eylem pozitif → Düşük risk (şirket kendini kötülüyor)

        Returns:
            {
                "soylem_sentiment": dict,
                "eylem_sentiment": dict,
                "sentiment_gap": float (0-1, uyumsuzluk miktarı),
                "risk_contribution": float (0-100),
                "interpretation": str
            }
        """
        soylem_sent = self.analyze_sentiment(soylem)
        eylem_sent = self.analyze_sentiment(eylem)

        # Duygu boşluğu: söylem ve eylem polaritesi arasındaki fark
        # Söylem çok pozitif ama eylem negatif → büyük boşluk
        polarity_gap = soylem_sent["polarity"] - eylem_sent["polarity"]

        # Tek yönlü gap: sadece söylem > eylem olduğunda risk oluşur
        # (Söylem negatif, eylem pozitif ise risk düşük)
        directional_gap = min(1.0, max(0, polarity_gap))

        # 0-100 arası risk katkısına normalize et
        risk_contribution = min(100, directional_gap * 50)

        # Yorumlama
        if directional_gap < 0.2:
            interpretation = "Söylem ve eylem duygusal tonu uyumlu."
        elif directional_gap < 0.5:
            interpretation = "Söylem eylemden daha iyimser bir ton taşıyor."
        elif directional_gap < 0.8:
            interpretation = "Söylem ile eylem arasında belirgin duygusal çelişki var."
        else:
            interpretation = "Söylem son derece pozitif ancak eylem olumsuz; güçlü yeşil aklama sinyali."

        return {
            "soylem_sentiment": soylem_sent,
            "eylem_sentiment": eylem_sent,
            "sentiment_gap": directional_gap,
            "risk_contribution": round(risk_contribution, 2),
            "interpretation": interpretation,
        }
