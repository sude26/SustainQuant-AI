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
from nlp.models import SustainaQuantNLP, create_nlp_engine
from nlp.similarity import CosineSimilarityEngine
from nlp.sentiment import SentimentAnalyzer
from nlp.entity_extract import analyze_entity_gap
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

    def __init__(self, nlp_model=None):
        self.nlp = nlp_model or create_nlp_engine()
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

    def _severity_from_risk(self, risk_score: float) -> str:
        if risk_score > 50:
            return "high"
        if risk_score > 25:
            return "med"
        return "low"

    def generate_esg_breakdown(self, gap_result: dict, record: dict) -> dict:
        """E/S/G kırılım skorlarını üretir (yüksek skor = düşük yeşil aklama riski)."""
        sim_risk = gap_result["combined_analysis"]["similarity_risk"]
        sent_risk = gap_result["combined_analysis"]["sentiment_risk"]
        risk = gap_result["risk_score"]
        cat = record.get("esg_kategorisi", record.get("category", "")).lower()

        environmental = round(max(0, min(100, 100 - sim_risk)), 0)
        social = round(max(0, min(100, 100 - sent_risk)), 0)
        governance = round(max(0, min(100, 100 - risk * 0.85)), 0)

        env_keys = ("enerji", "çevre", "emisyon", "su", "ges", "yenilenebilir", "karbon")
        soc_keys = ("sosyal", "iş güvenliği", "çalışan", "iş sağlığı")
        if any(k in cat for k in env_keys):
            environmental = round((environmental + (100 - risk)) / 2, 0)
        if any(k in cat for k in soc_keys):
            social = round((social + (100 - risk)) / 2, 0)

        return {
            "environmental": int(environmental),
            "social": int(social),
            "governance": int(governance),
        }

    def generate_anomalies(self, gap_result: dict, record: dict,
                           summary: str, trigger: str) -> list:
        """Çoklu anomali kartları listesi üretir."""
        anomalies = []
        risk = gap_result["risk_score"]
        sev = self._severity_from_risk(risk)

        anomalies.append({
            "title": gap_result["anomaly_status"],
            "description": summary,
            "severity": sev,
        })

        sent = gap_result["sentiment_result"]
        if sent["sentiment_gap"] > 0.25:
            anomalies.append({
                "title": "Duygu Uyumsuzluğu",
                "description": sent["interpretation"],
                "severity": "high" if sent["sentiment_gap"] > 0.4 else "med",
            })

        sim = gap_result["similarity_result"]
        if sim["similarity"] < 0.55:
            anomalies.append({
                "title": "Anlamsal Sapma",
                "description": sim["interpretation"],
                "severity": "high" if sim["similarity"] < 0.4 else "med",
            })

        if trigger and trigger != "Düzenli periyodik izleme yeterli.":
            anomalies.append({
                "title": "İzleme Tetikleyicisi",
                "description": trigger,
                "severity": "med",
            })

        timeline = record.get("timeline")
        if timeline and timeline.get("has_anomaly"):
            anomalies.append({
                "title": timeline.get("title", "Zaman Anomalisi"),
                "description": timeline.get("description", ""),
                "severity": timeline.get("severity", "med"),
            })

        verification = record.get("verification")
        if verification and verification.get("multi_source_verified"):
            anomalies.append({
                "title": "Çoklu Kaynak Teyidi",
                "description": (
                    f"{verification['independent_count']} bağımsız kaynak doğrulandı "
                    f"({verification['label']})."
                ),
                "severity": "low",
            })
        elif verification and verification.get("confidence") == "düşük":
            anomalies.append({
                "title": "Kaynak Teyidi Zayıf",
                "description": verification.get("label", "Yetersiz kaynak"),
                "severity": "med",
            })

        entity_gap = record.get("entity_gap")
        if entity_gap and entity_gap.get("has_conflict"):
            for c in entity_gap.get("conflicts", []):
                anomalies.append({
                    "title": c.get("title", "Sayısal Çelişki"),
                    "description": c.get("description", ""),
                    "severity": c.get("severity", "med"),
                })

        return anomalies

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

        esg_breakdown = self.generate_esg_breakdown(gap_result, record)
        entity_gap = analyze_entity_gap(soylem, eylem)
        record_enriched = {**record, "entity_gap": entity_gap}
        anomalies = self.generate_anomalies(gap_result, record_enriched, summary, trigger)

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
            "esg_breakdown": esg_breakdown,
            "anomalies": anomalies,
            "source": record.get("kaynak", ""),
            "analyzed_at": datetime.now().isoformat(),
            "verification": record.get("verification"),
            "timeline": record.get("timeline"),
            "live_sources": record.get("sources", []),
            "live_kap": record.get("live_kap"),
            "live_news": record.get("live_news", []),
            "entity_gap": entity_gap,
            "evidence": self._build_evidence(record),
            "kaynak": record.get("kaynak", ""),
            "kaynak_url": record.get("kaynak_url", ""),
            "eylem_tarihi": record.get("eylem_tarihi", ""),
            "soylem_tarihi": record.get("soylem_tarihi", ""),
        }

    def _build_evidence(self, record: dict) -> list[dict]:
        """Kanıt zinciri: kaynak, URL, tarih."""
        items = []
        if record.get("kaynak"):
            items.append({
                "source": record["kaynak"],
                "url": record.get("kaynak_url", ""),
                "type": "resmi_kurum",
                "date": record.get("eylem_tarihi", ""),
            })
        for src in record.get("sources", []):
            items.append({
                "source": src.get("source", ""),
                "url": src.get("source_url", ""),
                "type": src.get("type", ""),
                "date": src.get("publish_date", ""),
            })
        kap = record.get("live_kap")
        if kap and kap.get("source_url"):
            items.append({
                "source": "KAP",
                "url": kap["source_url"],
                "type": "kap",
                "date": kap.get("publish_date", ""),
            })
        return items

    def analyze_live(
        self,
        record: dict,
        include_kap: bool = True,
        include_news: bool = True,
        soylem_tarihi: str | None = None,
    ) -> dict:
        """KAP + haber kaynaklarıyla canlı doğrulama analizi."""
        from services.live_verification import fetch_live_context, build_enriched_record

        live = fetch_live_context(
            company_name=record["sirket_adi"],
            bist_code=record.get("bist_kodu", ""),
            category=record.get("esg_kategorisi", ""),
            dataset_eylem=record.get("eylem", ""),
            include_kap=include_kap,
            include_news=include_news,
        )
        enriched = build_enriched_record(record, live, soylem_tarihi=soylem_tarihi)
        return self.analyze_record(enriched)

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

    def get_heatmap_data(self) -> dict:
        """
        Şirket × ESG kategori risk matrisi (Anomali Isı Haritası için).
        """
        results = self.analyze_all()
        companies = sorted({r["company_name"] for r in results})
        categories = sorted({r["category"] for r in results})

        lookup = {(r["company_name"], r["category"]): r["risk_score"] for r in results}

        # En yüksek riskli şirket üstte
        max_risk = {}
        for r in results:
            name = r["company_name"]
            max_risk[name] = max(max_risk.get(name, 0), r["risk_score"])
        companies = sorted(companies, key=lambda c: max_risk.get(c, 0), reverse=True)
        matrix = []
        cells = []

        for company in companies:
            row = []
            for category in categories:
                score = lookup.get((company, category))
                row.append(score)
                if score is not None:
                    cells.append({
                        "company_name": company,
                        "category": category,
                        "risk_score": score,
                    })
            matrix.append(row)

        return {
            "companies": companies,
            "categories": categories,
            "matrix": matrix,
            "cells": cells,
        }
