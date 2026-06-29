"""
SustainaQuant AI – API Route'ları
===================================
REST API endpoint'leri: Tekil analiz, toplu analiz, şirket listesi.
B2B SaaS dashboard'u ve DaaS API'sini besleyen tek backend.
"""

from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.schemas import (
    AnalysisRequest, AnalysisResponse,
    BatchAnalysisRequest, BatchAnalysisResponse,
    CompanyAnalysisRequest, CompanyListResponse, CompanyInfo,
    PortfolioSummary, HealthResponse, HeatmapResponse, HeatmapCell,
    SimilarityDetail, SentimentDetail, AnomalyItem, ESGBreakdown,
)
from api.auth import verify_api_key, optional_api_key
from data.esg_dataset import get_companies, get_esg_dataset
from nlp.analyzer import GreenwashingAnalyzer

router = APIRouter(prefix="/api/v1", tags=["SustainaQuant AI"])

# Global analyzer instance (startup'ta initialize edilir)
_analyzer = None


def get_analyzer() -> GreenwashingAnalyzer:
    """Analyzer singleton'ını döndürür."""
    global _analyzer
    if _analyzer is None:
        _analyzer = GreenwashingAnalyzer()
    return _analyzer


def _format_response(result: dict) -> AnalysisResponse:
    """Analiz sonucunu API yanıt formatına dönüştürür."""
    # Similarity detay
    sim = result.get("similarity", {})
    similarity_detail = SimilarityDetail(
        similarity=sim.get("similarity", 0),
        distance=sim.get("distance", 0),
        risk_score=sim.get("risk_score", 0),
        interpretation=sim.get("interpretation", ""),
    ) if sim else None

    # Sentiment detay
    sent = result.get("sentiment", {})
    sentiment_detail = None
    if sent:
        soylem_sent = sent.get("soylem_sentiment", {})
        eylem_sent = sent.get("eylem_sentiment", {})
        sentiment_detail = SentimentDetail(
            soylem_label=soylem_sent.get("label", "neutral"),
            soylem_polarity=soylem_sent.get("polarity", 0),
            eylem_label=eylem_sent.get("label", "neutral"),
            eylem_polarity=eylem_sent.get("polarity", 0),
            sentiment_gap=sent.get("sentiment_gap", 0),
            risk_contribution=sent.get("risk_contribution", 0),
            interpretation=sent.get("interpretation", ""),
        )

    esg = result.get("esg_breakdown", {})
    esg_detail = ESGBreakdown(**esg) if esg else None

    anomalies = [
        AnomalyItem(**a) for a in result.get("anomalies", [])
    ]

    return AnalysisResponse(
        company_name=result["company_name"],
        bist_code=result.get("bist_code", ""),
        category=result["category"],
        risk_score=result["risk_score"],
        anomaly_status=result["anomaly_status"],
        summary=result["summary"],
        trigger=result["trigger"],
        formatted_report=result["formatted_report"],
        similarity=similarity_detail,
        sentiment=sentiment_detail,
        esg_breakdown=esg_detail,
        anomalies=anomalies,
        source=result.get("source", ""),
        analyzed_at=result.get("analyzed_at", datetime.now().isoformat()),
    )


# ── DaaS Endpoint'leri (Pay-as-you-go) ──────────────────────

@router.post("/analyze", response_model=AnalysisResponse,
             summary="Tekil Söylem-Eylem Analizi",
             description="Bir şirketin söylem ve eylem metinlerini karşılaştırıp Yeşil Aklama Risk Skoru üretir.")
async def analyze(request: AnalysisRequest, auth: dict = Depends(verify_api_key)):
    """
    Tekil söylem-eylem karşılaştırma analizi.
    DaaS modeli: $0.02/sorgu
    """
    analyzer = get_analyzer()
    result = analyzer.analyze_custom(
        company_name=request.company_name,
        category=request.category,
        soylem=request.soylem,
        eylem=request.eylem,
    )
    return _format_response(result)


@router.post("/batch", response_model=BatchAnalysisResponse,
             summary="Toplu Portföy Tarama",
             description="Birden fazla şirket için toplu analiz yapar. Portföy yöneticileri için idealdir.")
async def batch_analyze(request: BatchAnalysisRequest, auth: dict = Depends(verify_api_key)):
    """
    Toplu portföy analizi.
    Rapor §4: "Bankaların kendi algoritmik ticaret sistemlerine doğrudan skor akışı"
    """
    analyzer = get_analyzer()
    results = []

    for item in request.analyses:
        result = analyzer.analyze_custom(
            company_name=item.company_name,
            category=item.category,
            soylem=item.soylem,
            eylem=item.eylem,
        )
        results.append(_format_response(result))

    risk_scores = [r.risk_score for r in results]
    avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0

    return BatchAnalysisResponse(
        total_analyses=len(results),
        avg_risk_score=round(avg_risk, 1),
        high_risk_count=sum(1 for s in risk_scores if s > 50),
        results=results,
    )


# ── SaaS Endpoint'leri (Dashboard) ──────────────────────────

@router.get("/companies", response_model=CompanyListResponse,
            summary="Kayıtlı Şirket Listesi",
            description="Veri setindeki tüm şirketlerin listesini döndürür.")
async def list_companies(auth: dict = Depends(optional_api_key)):
    """Kayıtlı şirket listesi."""
    companies = get_companies()
    return CompanyListResponse(
        total=len(companies),
        companies=[CompanyInfo(**c) for c in companies],
    )


@router.post("/companies/analyze", response_model=list[AnalysisResponse],
             summary="Kayıtlı Şirket Analizi",
             description="Veri setindeki kayıtlı bir şirketin tüm ESG kategorilerini analiz eder.")
async def analyze_company(request: CompanyAnalysisRequest, auth: dict = Depends(optional_api_key)):
    """Kayıtlı şirketin tüm ESG kategorilerini analiz eder."""
    analyzer = get_analyzer()
    results = analyzer.analyze_company(request.company_name)

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"Şirket bulunamadı: {request.company_name}"
        )

    return [_format_response(r) for r in results]


@router.get("/dashboard/summary", response_model=PortfolioSummary,
            summary="Dashboard Özet İstatistikler",
            description="Tüm portföy için özet risk istatistiklerini döndürür.")
async def dashboard_summary(auth: dict = Depends(optional_api_key)):
    """Dashboard ana sayfa istatistikleri."""
    analyzer = get_analyzer()
    summary = analyzer.get_portfolio_summary()
    return PortfolioSummary(
        total_companies=summary["total_companies"],
        total_analyses=summary["total_analyses"],
        avg_risk_score=summary["avg_risk_score"],
        high_risk_count=summary["high_risk_count"],
        max_risk_score=summary["max_risk_score"],
        min_risk_score=summary["min_risk_score"],
    )


@router.get("/dashboard/heatmap", response_model=HeatmapResponse,
            summary="Anomali Isı Haritası",
            description="Şirket × ESG kategori risk matrisini döndürür.")
async def dashboard_heatmap(auth: dict = Depends(optional_api_key)):
    """Portföy anomali ısı haritası verisi."""
    analyzer = get_analyzer()
    data = analyzer.get_heatmap_data()
    return HeatmapResponse(
        companies=data["companies"],
        categories=data["categories"],
        matrix=data["matrix"],
        cells=[HeatmapCell(**c) for c in data["cells"]],
    )


@router.get("/health", response_model=HealthResponse,
            summary="Sistem Sağlık Kontrolü")
async def health_check():
    """Sistem durumunu kontrol eder."""
    analyzer = get_analyzer()
    return HealthResponse(
        status="healthy",
        version="1.0.0-mvp",
        models_loaded=analyzer.nlp.is_ready,
        database_ready=True,
        timestamp=datetime.now().isoformat(),
    )
