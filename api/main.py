"""
SustainaQuant AI – FastAPI Ana Uygulaması
==========================================
Rapor §3: "Yüksek performanslı asenkron veri işleme için FastAPI (Python)"

Asenkron backend: hem B2B SaaS dashboard'u hem DaaS API'sini besler.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    API_TITLE, API_DESCRIPTION, API_VERSION,
    CORS_ORIGINS, MASTER_SYSTEM_PROMPT,
)
from api.routes import router, get_analyzer
from data.ingestion import DataIngestionPipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Uygulama yaşam döngüsü yönetimi.
    Startup: Veritabanını hazırla, NLP modellerini yükle.
    Shutdown: Kaynakları temizle.
    """
    print("=" * 60)
    print("🚀 SUSTAINQUANT AI – API SUNUCUSU BAŞLATILIYOR")
    print("=" * 60)
    print()

    # Veritabanını hazırla
    pipeline = DataIngestionPipeline()
    pipeline.initialize_database()
    print()

    # NLP modellerini önceden yükle (warmup)
    print("🧠 NLP modelleri yükleniyor (bu işlem ilk seferde birkaç dakika sürebilir)...")
    analyzer = get_analyzer()
    try:
        analyzer.nlp.warmup()
    except Exception as e:
        print(f"⚠️ Model warmup sırasında hata: {e}")
        print("   Modeller ilk istekte yüklenecek (lazy loading).")
    print()

    print("=" * 60)
    print(f"✅ API hazır! Swagger dokümantasyonu: http://localhost:8000/docs")
    print("=" * 60)

    yield

    # Shutdown
    print("\n🛑 API sunucusu kapatılıyor...")


# FastAPI uygulaması
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version="1.0.0-mvp",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route'ları ekle
app.include_router(router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API kök endpoint'i – Sistem bilgisi."""
    return {
        "project": "SustainaQuant AI",
        "description": "NLP Tabanlı ESG Risk & Yeşil Aklama Tespit Motoru",
        "team": "SUSTAINQUANT AI | Takım ID: 918431",
        "version": "1.0.0-mvp",
        "docs": "/docs",
        "api_base": f"/api/{API_VERSION}",
        "system_prompt": MASTER_SYSTEM_PROMPT[:100] + "...",
        "timestamp": datetime.now().isoformat(),
    }
