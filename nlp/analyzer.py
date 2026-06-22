"""
SustainaQuant AI – Yeşil Aklama Analiz Motoru (Say-Do Gap Algoritması)
========================================================================
Rapor §3: "Söylem-Eylem Boşluğu (Say-Do Gap) algoritması adı verilen özgün yöntem"

Bu modül, tüm NLP bileşenlerini (embedding, similarity, sentiment) birleştirerek
nihai Yeşil Aklama Risk Skoru'nu üretir ve Master System Prompt formatında
yapılandırılmış rapor çıktısı verir.
"""

from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    MASTER_SYSTEM_PROMPT,
    REPORT_TEMPLATE,
    ANOMALY_THRESHOLDS,
    ANOMALY_LABELS,
    SIMILARITY_WEIGHT,
    SENTIMENT_WEIGHT,
)
from nlp.models import SustainaQuantNLP
from nlp.similarity import CosineSimilarityEngine
from nlp.sentiment import SentimentAnalyzer
from data.esg_dataset import get_esg_dataset


class GreenwashingAnalyzer:
    """
    Ana Yeşil Aklama Analiz Motoru.
    Rapordaki "Söylem-Eylem Boşluğu" algoritmasının tam orkestratörü.

    Pipeline:
    1. Söylem metnini al → embedding'e çevir + duygu analizi yap
    2. Eylem metnini al → embedding'e çevir + duygu analizi yap
    3. Cosine Similarity ile anlamsal mesafeyi hesapla
    4. Duygu uyumsuzluğunu hesapla
    5. İki skoru ağırlıklı ortalamayla birleştir → Risk Skoru (0-100)
    6. Anomali sınıflandır ve rapor formatında çıktı üret
    """

    def __init__(self, nlp_model: SustainaQuantNLP = None):
        self.nlp = nlp_model or SustainaQuantNLP()
        self.similarity_engine = CosineSimilarityEngine(self.nlp)
        self.sentiment_analyzer = SentimentAnalyzer(self.nlp)
        self.system_prompt = MASTER_SYSTEM_PROMPT

    def classify_anomaly(self, risk_score: float) -> str:
        """
        Risk skoruna göre anomali durumunu sınıflandırır.

        0-25:  Tam Uyum
        26-50: Kapsam Uyuşmazlığı
        51-75: Doğrudan Çelişki
        76-100: Veri Yetersizliği
        """
        for key, (low, high) in ANOMALY_THRESHOLDS.items():
            if low <= risk_score <= high:
                return ANOMALY_LABELS[key]
        return ANOMALY_LABELS["veri_yetersizligi"]

    def get_anomaly_key(self, risk_score: float) -> str:
        """Anomali durumunun anahtar kodunu döndürür (renklendirme için)."""
        for key, (low, high) in ANOMALY_THRESHOLDS.items():
            if low <= risk_score <= high:
                return key
        return "veri_yetersizligi"

    def generate_summary(self, similarity_result: dict, sentiment_result: dict,
                          risk_score: float, anomaly: str) -> str:
        """Analiz için özet gerekçe metni üretir."""
        parts = []

        # Similarity yorumu
        sim = similarity_result["similarity"]
        if sim >= 0.75:
            parts.append(
                f"Söylem ve eylem metinleri arasında yüksek anlamsal uyum tespit edildi "
                f"(benzerlik: {sim:.2%})."
            )
        elif sim >= 0.50:
            parts.append(
                f"Söylem ve eylem metinleri arasında orta düzeyde anlamsal uyum mevcut "
                f"(benzerlik: {sim:.2%}). Kapsam veya ölçek farklılıkları gözlemlendi."
            )
        else:
            parts.append(
                f"Söylem ve eylem metinleri arasında düşük anlamsal uyum tespit edildi "
                f"(benzerlik: {sim:.2%}). Bu durum potansiyel yeşil aklama sinyali olabilir."
            )

        # Sentiment yorumu
        gap = sentiment_result["sentiment_gap"]
        if gap > 0.3:
            parts.append(
                f"Duygu analizi, söylemin eylemden belirgin şekilde daha pozitif olduğunu "
                f"göstermektedir (duygu boşluğu: {gap:.2f})."
            )

        # Genel değerlendirme
        if risk_score >= 51:
            parts.append(
                "Bu bulgular, şirketin ESG taahhütleri ile gerçekleşen eylemler arasında "
                "anlamlı bir tutarsızlık olduğuna işaret etmektedir."
            )

        return " ".join(parts)

    def generate_trigger(self, similarity_result: dict, sentiment_result: dict,
                          company_data: dict) -> str:
        """İzlenmesi gereken tetikleyici/eksik bilgileri belirler."""
        triggers = []

        sim = similarity_result["similarity"]
        if sim < 0.5:
            triggers.append("Bağımsız dış kaynaklardan güncel doğrulama verileri toplanmalı")

        gap = sentiment_result["sentiment_gap"]
        if gap > 0.4:
            triggers.append("Şirketin gelecek dönem raporlarında taahhüt-gerçekleşme oranı izlenmeli")

        kaynak = company_data.get("kaynak", "")
        if "ÇED" in kaynak:
            triggers.append("ÇED süreçlerinin güncel durumu takip edilmeli")
        if "İSU" in kaynak or "su" in company_data.get("esg_kategorisi", "").lower():
            triggers.append("Mutlak su ayak izi (toplam tüketim) trendi izlenmeli")
        if "GES" in company_data.get("soylem", "") or "yenilenebilir" in company_data.get("esg_kategorisi", "").lower():
            triggers.append("Yenilenebilir enerji projesinin fiziksel ilerleme durumu kontrol edilmeli")

        return "; ".join(triggers) if triggers else "Düzenli periyodik izleme yeterli."

    def calculate_say_do_gap(self, soylem: str, eylem: str) -> dict:
        """
        Söylem-Eylem Boşluğu (Say-Do Gap) algoritması.

        Rapor §3: "iki veri seti arasındaki anlamsal çelişkiyi
                    'Yeşil Aklama Anomalisi' olarak etiketler."

        Args:
            soylem: Şirketin ESG raporundaki iddia metni
            eylem: Bağımsız kaynaklardan doğrulanan gerçek eylem metni

        Returns:
            {
                "risk_score": float (0-100),
                "anomaly_status": str,
                "anomaly_key": str,
                "similarity_result": dict,
                "sentiment_result": dict,
                "combined_analysis": dict
            }
        """
        # ── Adım 1-2: Metinleri vektöre çevir + duygu analizi ──
        similarity_result = self.similarity_engine.compute(soylem, eylem)
        sentiment_result = self.sentiment_analyzer.compare_sentiments(soylem, eylem)

        # ── Adım 3-4: Ağırlıklı birleştirme ──
        # Similarity risk katkısı (0-100)
        sim_risk = similarity_result["risk_score"]

        # Sentiment risk katkısı (0-100)
        sent_risk = sentiment_result["risk_contribution"]

        # ── Adım 5: Nihai risk skoru ──
        # Ağırlıklı ortalama: %65 benzerlik + %35 duygu
        risk_score = (SIMILARITY_WEIGHT * sim_risk) + (SENTIMENT_WEIGHT * sent_risk)
        risk_score = round(min(100, max(0, risk_score)), 1)

        # ── Adım 6: Anomali sınıflandırma ──
        anomaly_status = self.classify_anomaly(risk_score)
        anomaly_key = self.get_anomaly_key(risk_score)

        return {
            "risk_score": risk_score,
            "anomaly_status": anomaly_status,
            "anomaly_key": anomaly_key,
            "similarity_result": similarity_result,
            "sentiment_result": sentiment_result,
            "combined_analysis": {
                "similarity_risk": round(sim_risk, 2),
                "sentiment_risk": round(sent_risk, 2),
                "similarity_weight": SIMILARITY_WEIGHT,
                "sentiment_weight": SENTIMENT_WEIGHT,
            },
        }

    def analyze_record(self, record: dict) -> dict:
        """
        Tek bir ESG kaydını (söylem + eylem) analiz eder ve
        Master System Prompt formatında rapor üretir.

        Args:
            record: esg_dataset'ten gelen bir kayıt sözlüğü

        Returns:
            Tam analiz sonucu + formatlanmış rapor
        """
        soylem = record["soylem"]
        eylem = record["eylem"]

        # Say-Do Gap hesapla
        gap_result = self.calculate_say_do_gap(soylem, eylem)

        # Özet gerekçe üret
        summary = self.generate_summary(
            gap_result["similarity_result"],
            gap_result["sentiment_result"],
            gap_result["risk_score"],
            gap_result["anomaly_status"]
        )

        # Tetikleyici üret
        trigger = self.generate_trigger(
            gap_result["similarity_result"],
            gap_result["sentiment_result"],
            record
        )

        # Master System Prompt formatında rapor
        formatted_report = REPORT_TEMPLATE.format(
            company_name=record["sirket_adi"],
            category=record["esg_kategorisi"],
            risk_score=gap_result["risk_score"],
            anomaly_status=gap_result["anomaly_status"],
            summary=summary,
            trigger=trigger,
        )

        return {
            "company_name": record["sirket_adi"],
            "bist_code": record.get("bist_kodu", ""),
            "category": record["esg_kategorisi"],
            "risk_score": gap_result["risk_score"],
            "anomaly_status": gap_result["anomaly_status"],
            "anomaly_key": gap_result["anomaly_key"],
            "similarity": gap_result["similarity_result"],
            "sentiment": gap_result["sentiment_result"],
            "combined": gap_result["combined_analysis"],
            "summary": summary,
            "trigger": trigger,
            "formatted_report": formatted_report,
            "source": record.get("kaynak", ""),
            "analyzed_at": datetime.now().isoformat(),
        }

    def analyze_company(self, company_name: str) -> list:
        """
        Belirli bir şirketin tüm ESG kategorilerini analiz eder.

        Args:
            company_name: Şirket adı (örn: "Tüpraş")

        Returns:
            Liste: Her ESG kategorisi için analiz sonucu
        """
        dataset = get_esg_dataset()
        company_records = [r for r in dataset if r["sirket_adi"] == company_name]

        results = []
        for record in company_records:
            result = self.analyze_record(record)
            results.append(result)

        return results

    def analyze_all(self) -> list:
        """
        Tüm şirketleri toplu olarak analiz eder.
        Portföy tarama (batch analiz) için kullanılır.

        Returns:
            Liste: Tüm şirketler ve kategoriler için analiz sonuçları
        """
        dataset = get_esg_dataset()
        results = []

        for record in dataset:
            result = self.analyze_record(record)
            results.append(result)

        return results

    def analyze_custom(self, company_name: str, category: str,
                        soylem: str, eylem: str) -> dict:
        """
        Kullanıcı tanımlı söylem-eylem çifti için analiz yapar.
        API ve dashboard'dan gelen özel girişler için kullanılır.

        Args:
            company_name: Şirket adı
            category: ESG kategorisi
            soylem: Söylem metni
            eylem: Eylem metni

        Returns:
            Tam analiz sonucu
        """
        record = {
            "sirket_adi": company_name,
            "bist_kodu": "",
            "esg_kategorisi": category,
            "soylem": soylem,
            "eylem": eylem,
            "kaynak": "Manuel Giriş",
        }
        return self.analyze_record(record)

    def get_portfolio_summary(self) -> dict:
        """
        Tüm portföy için özet istatistikler üretir.
        Dashboard ana sayfası için kullanılır.

        Returns:
            {
                "total_companies": int,
                "avg_risk_score": float,
                "high_risk_count": int,
                "results": list
            }
        """
        results = self.analyze_all()

        risk_scores = [r["risk_score"] for r in results]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        high_risk = sum(1 for s in risk_scores if s > 50)

        return {
            "total_companies": len(set(r["company_name"] for r in results)),
            "total_analyses": len(results),
            "avg_risk_score": round(avg_risk, 1),
            "high_risk_count": high_risk,
            "max_risk_score": max(risk_scores) if risk_scores else 0,
            "min_risk_score": min(risk_scores) if risk_scores else 0,
            "results": results,
        }
