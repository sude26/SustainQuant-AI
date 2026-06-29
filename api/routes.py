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
    LiveVerificationRequest, KAPDisclosureResponse,
    VerificationDetail, TimelineDetail, SourceDetail,
    AlertsResponse, AlertItem, NewsScanResponse,
)
from api.auth import verify_api_key, optional_api_key
from data.esg_dataset import get_companies, get_esg_dataset, get_company_data
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

    verification = None
    if result.get("verification"):
        v = result["verification"]
        verification = VerificationDetail(
            **{**v, "details": [SourceDetail(**d) for d in v.get("details", [])]}
        )

    timeline = TimelineDetail(**result["timeline"]) if result.get("timeline") else None

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
        verification=verification,
        timeline=timeline,
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
    _maybe_publish_alert(result)
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


# ── Faz B: Canlı Doğrulama ──────────────────────────────────

@router.get("/kap/{bist_code}/latest", response_model=KAPDisclosureResponse,
            summary="KAP Son ESG Bildirimi",
            description="Şirketin KAP'taki en güncel ESG bildirimini çeker.")
async def kap_latest(bist_code: str, auth: dict = Depends(optional_api_key)):
    from data.kap_fetcher import get_kap_fetcher
    try:
        result = get_kap_fetcher().fetch_latest_esg_action(bist_code.upper())
        if not result:
            return KAPDisclosureResponse(
                bist_code=bist_code.upper(),
                error="ESG bildirimi bulunamadı",
            )
        return KAPDisclosureResponse(
            bist_code=result.get("bist_code", bist_code.upper()),
            company_name=result.get("company_name", ""),
            disclosure_index=result.get("disclosure_index"),
            subject=result.get("subject"),
            publish_date=result.get("publish_date"),
            eylem_text=result.get("eylem_text", ""),
            source_url=result.get("source_url"),
        )
    except Exception as exc:
        return KAPDisclosureResponse(bist_code=bist_code.upper(), error=str(exc))


@router.post("/verify/live", response_model=AnalysisResponse,
             summary="Canlı KAP + Haber Doğrulama",
             description="KAP ve RSS haber kaynaklarıyla çapraz doğrulama analizi.")
async def verify_live(request: LiveVerificationRequest, auth: dict = Depends(optional_api_key)):
    analyzer = get_analyzer()
    dataset_eylem = ""
    records = get_company_data(request.company_name) if request.use_dataset_eylem else []
    if records:
        dataset_eylem = records[0].get("eylem", "")

    record = {
        "sirket_adi": request.company_name,
        "bist_kodu": request.bist_code.upper(),
        "esg_kategorisi": request.category,
        "soylem": request.soylem,
        "eylem": dataset_eylem,
        "eylem_tarihi": records[0].get("eylem_tarihi") if records else None,
        "kaynak": "Canlı Doğrulama",
    }
    result = analyzer.analyze_live(
        record,
        include_kap=request.include_kap,
        include_news=request.include_news,
        soylem_tarihi=request.soylem_tarihi,
    )
    _maybe_publish_alert(result)
    return _format_response(result)


# ── Faz C: Canlı Alarmlar & Haber Tarama ────────────────────

def _maybe_publish_alert(result: dict):
    try:
        from services.alert_bus import alert_from_analysis
        alert_from_analysis(result)
    except Exception:
        pass


@router.get("/alerts", response_model=AlertsResponse,
            summary="Son Anomali Alarmları",
            description="WebSocket ile de iletilen canlı alarm geçmişi.")
async def list_alerts(limit: int = 20, auth: dict = Depends(optional_api_key)):
    from services.alert_bus import get_recent_alerts
    alerts = get_recent_alerts(limit)
    return AlertsResponse(
        total=len(alerts),
        alerts=[AlertItem(**a) for a in alerts],
    )


@router.post("/alerts/scan-news", response_model=NewsScanResponse,
             summary="Portföy Haber Taraması",
             description="Tüm şirketler için RSS haber taraması yapar ve alarm üretir.")
async def trigger_news_scan(auth: dict = Depends(optional_api_key)):
    from services.news_scanner import scan_portfolio_news
    result = scan_portfolio_news()
    return NewsScanResponse(**result)
