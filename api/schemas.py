"""
SustainaQuant AI – Pydantic Şemaları
======================================
API istekleri ve yanıtları için veri doğrulama şemaları.
Otomatik OpenAPI (Swagger) dokümantasyonu üretir.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── İstek Şemaları ───────────────────────────────────────────

class AnalysisRequest(BaseModel):
    """Tekil söylem-eylem karşılaştırma analiz isteği."""
    company_name: str = Field(..., description="Şirket adı", examples=["Tüpraş"])
    category: str = Field(..., description="ESG kategorisi", examples=["Enerji Verimliliği"])
    soylem: str = Field(..., description="Şirketin ESG raporundaki iddia metni")
    eylem: str = Field(..., description="Bağımsız kaynaklardan doğrulanan gerçek eylem metni")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "company_name": "Tüpraş",
                    "category": "Enerji Verimliliği",
                    "soylem": "112 adet enerji verimliliği projesi hayata geçirilmiş; 2.448 TJ enerji tasarrufu sağlanmıştır.",
                    "eylem": "EPDK verilerine göre rafinerinin toplam enerji tüketimi bir önceki yıla kıyasla %3,2 artış göstermiştir."
                }
            ]
        }
    }


class BatchAnalysisRequest(BaseModel):
    """Toplu portföy tarama analiz isteği."""
    analyses: List[AnalysisRequest] = Field(
        ..., description="Analiz edilecek söylem-eylem çiftlerinin listesi"
    )


class CompanyAnalysisRequest(BaseModel):
    """Kayıtlı şirket için hızlı analiz isteği."""
    company_name: str = Field(..., description="Analiz edilecek şirket adı")


# ── Yanıt Şemaları ───────────────────────────────────────────

class SimilarityDetail(BaseModel):
    """Kosinüs benzerliği detayları."""
    similarity: float = Field(..., description="Kosinüs benzerlik skoru (-1 ile 1)")
    distance: float = Field(..., description="Kosinüs mesafesi (0 ile 2)")
    risk_score: float = Field(..., description="Benzerlik tabanlı risk skoru (0-100)")
    interpretation: str = Field(..., description="Benzerlik yorumu")


class SentimentDetail(BaseModel):
    """Duygu analizi detayları."""
    soylem_label: str = Field(..., description="Söylem duygu etiketi")
    soylem_polarity: float = Field(..., description="Söylem polaritesi (-1 ile +1)")
    eylem_label: str = Field(..., description="Eylem duygu etiketi")
    eylem_polarity: float = Field(..., description="Eylem polaritesi (-1 ile +1)")
    sentiment_gap: float = Field(..., description="Duygu boşluğu (0-1)")
    risk_contribution: float = Field(..., description="Duygu tabanlı risk katkısı (0-100)")
    interpretation: str = Field(..., description="Duygu karşılaştırma yorumu")


class AnalysisResponse(BaseModel):
    """
    Tekil analiz yanıtı.
    Master System Prompt formatında yapılandırılmış çıktı.
    """
    company_name: str
    bist_code: str
    category: str
    risk_score: float = Field(..., description="Yeşil Aklama Risk Skoru (0-100)")
    anomaly_status: str = Field(..., description="Anomali Durumu")
    summary: str = Field(..., description="Özet Gerekçe")
    trigger: str = Field(..., description="Eksik/İzlenmesi Gereken Tetikleyici")
    formatted_report: str = Field(..., description="Master System Prompt formatında tam rapor")
    similarity: Optional[SimilarityDetail] = None
    sentiment: Optional[SentimentDetail] = None
    source: str = ""
    analyzed_at: str = ""


class BatchAnalysisResponse(BaseModel):
    """Toplu analiz yanıtı."""
    total_analyses: int
    avg_risk_score: float
    high_risk_count: int
    results: List[AnalysisResponse]


class CompanyInfo(BaseModel):
    """Şirket bilgisi."""
    sirket_adi: str
    sektor: str
    bist_kodu: str


class CompanyListResponse(BaseModel):
    """Şirket listesi yanıtı."""
    total: int
    companies: List[CompanyInfo]


class PortfolioSummary(BaseModel):
    """Dashboard özet istatistikleri."""
    total_companies: int
    total_analyses: int
    avg_risk_score: float
    high_risk_count: int
    max_risk_score: float
    min_risk_score: float


class HealthResponse(BaseModel):
    """Sistem sağlık kontrolü yanıtı."""
    status: str = "healthy"
    version: str = "1.0.0-mvp"
    models_loaded: bool = False
    database_ready: bool = False
    timestamp: str = ""
