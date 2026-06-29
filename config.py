"""
SustainaQuant AI – Merkezi Konfigürasyon
=========================================
Tüm sistem ayarları, model yolları, Master System Prompt ve
sabitler tek merkezden yönetilir.
"""

import os
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# PROJE YOLLARI
# ──────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "sustainquant.db"
CSV_OUTPUT_PATH = BASE_DIR / "sustainaquant_mvp_gercek_veri.csv"
LOGO_PATH = BASE_DIR / "sustainquant_logo.png"

# ──────────────────────────────────────────────────────────────
# NLP MODEL KONFİGÜRASYONU
# ──────────────────────────────────────────────────────────────

# FinBERT – Finansal terminolojiye fine-tuned (İngilizce)
FINBERT_MODEL_ID = "ProsusAI/finbert"

# BERTürk – Türkçe NLP (BIST/KAP lokalizasyonu)
BERTURK_MODEL_ID = "dbmdz/bert-base-turkish-cased"

# Sentence Transformers – Anlamsal benzerlik
SENTENCE_TRANSFORMER_EN = "all-MiniLM-L6-v2"
SENTENCE_TRANSFORMER_TR = "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"

# Model cache dizini
MODEL_CACHE_DIR = BASE_DIR / ".model_cache"

# NLP modu: "lightweight" = internet gerektirmez (varsayılan, hızlı)
#            "full"        = FinBERT + Sentence Transformers (internet gerekir)
NLP_MODE = "lightweight"

# ──────────────────────────────────────────────────────────────
# MASTER SYSTEM PROMPT
# ──────────────────────────────────────────────────────────────

MASTER_SYSTEM_PROMPT = """Sen SustainaQuant AI ESG denetim motorusun. Sana verilen Söylem ve Eylem metinlerini karşılaştırıp 0-100 arası bir Yeşil Aklama Risk Skoru belirle. Çıktıyı SADECE şu şablonda ver:

[ANALİZ RAPORU]
Şirket Adı:
Analiz Edilen Kategori:
Yeşil Aklama Risk Skoru:
Anomali Durumu: (Tam Uyum/Kapsam Uyuşmazlığı/Doğrudan Çelişki/Veri Yetersizliği)
Özet Gerekçe:
Eksik/İzlenmesi Gereken Tetikleyici:"""

# Analiz raporu çıktı şablonu
REPORT_TEMPLATE = """[ANALİZ RAPORU]
Şirket Adı: {company_name}
Analiz Edilen Kategori: {category}
Yeşil Aklama Risk Skoru: {risk_score}/100
Anomali Durumu: {anomaly_status}
Özet Gerekçe: {summary}
Eksik/İzlenmesi Gereken Tetikleyici: {trigger}"""

# ──────────────────────────────────────────────────────────────
# RİSK SKORU EŞİK DEĞERLERİ & ANOMALİ KURALLARI
# ──────────────────────────────────────────────────────────────

ANOMALY_THRESHOLDS = {
    "tam_uyum": (0, 25),           # Söylem ve eylem anlamsal olarak uyumlu
    "kapsam_uyusmazligi": (26, 50), # Kısmi uyum var ama kapsam/ölçek farklı
    "dogrudan_celiski": (51, 75),   # Söylem ile eylem birbiriyle çelişiyor
    "veri_yetersizligi": (76, 100), # Yeterli çapraz doğrulama verisi bulunamadı
}

ANOMALY_LABELS = {
    "tam_uyum": "Tam Uyum",
    "kapsam_uyusmazligi": "Kapsam Uyuşmazlığı",
    "dogrudan_celiski": "Doğrudan Çelişki",
    "veri_yetersizligi": "Veri Yetersizliği",
}

ANOMALY_COLORS = {
    "tam_uyum": "#00ff88",          # Yeşil
    "kapsam_uyusmazligi": "#ffcc00", # Sarı
    "dogrudan_celiski": "#ff6b35",   # Turuncu
    "veri_yetersizligi": "#ff0054",  # Kırmızı
}

# Risk skoru hesaplamada ağırlıklar
SIMILARITY_WEIGHT = 0.65   # Kosinüs benzerliği ağırlığı
SENTIMENT_WEIGHT = 0.35    # Duygu analizi ağırlığı

# ──────────────────────────────────────────────────────────────
# WHITELIST KAYNAKLAR (Rapor §6 – Risk Önlemi)
# ──────────────────────────────────────────────────────────────
# Yalnızca güvenilirliği kanıtlanmış resmi kurumlar kullanılır.

SOURCE_WHITELIST = [
    # Türkiye Resmi Kurumları
    "KAP (Kamuyu Aydınlatma Platformu)",
    "T.C. Çevre, Şehircilik ve İklim Değişikliği Bakanlığı",
    "EPDK (Enerji Piyasası Düzenleme Kurumu)",
    "SPK (Sermaye Piyasası Kurulu)",
    "TEDAŞ",
    "İSU (Kocaeli Su ve Kanalizasyon İdaresi)",
    "BIST (Borsa İstanbul)",

    # Uluslararası Resmi Kurumlar
    "SEC (U.S. Securities and Exchange Commission)",
    "SEC EDGAR",
    "European Commission (SFDR)",

    # Güvenilir Haber Ajansları
    "Reuters",
    "Bloomberg",
    "Anadolu Ajansı (AA)",

    # STK ve Bağımsız Kuruluşlar
    "CDP (Carbon Disclosure Project)",
    "GRI (Global Reporting Initiative)",
    "SASB (Sustainability Accounting Standards Board)",
]

# ──────────────────────────────────────────────────────────────
# API KONFİGÜRASYONU
# ──────────────────────────────────────────────────────────────

API_HOST = "0.0.0.0"
API_PORT = 8000
API_VERSION = "v1"
API_TITLE = "SustainaQuant AI – ESG Risk & Greenwashing Detection API"
API_DESCRIPTION = """
Yatırım Portföyleri İçin NLP Tabanlı ESG Risk ve Yeşil Aklama Tespit Motoru.

**İş Modeli:**
- B2B SaaS Abonelik: $450/ay (Premium Dashboard Erişimi)
- DaaS API: $0.02/sorgu (Pay-as-you-go)
"""

# Demo API anahtarı (MVP için)
DEMO_API_KEY = "sq-demo-2026-teknofest"

# CORS ayarları
CORS_ORIGINS = [
    "http://localhost:8501",   # Streamlit
    "http://localhost:3000",   # React (ileride)
    "http://localhost:8000",   # FastAPI docs
]

# ──────────────────────────────────────────────────────────────
# STREAMLIT DASHBOARD KONFİGÜRASYONU
# ──────────────────────────────────────────────────────────────

DASHBOARD_TITLE = "📊 SustainaQuant AI | ESG Risk Terminali"
DASHBOARD_PAGE_TITLE = "SustainaQuant AI"
DASHBOARD_LAYOUT = "wide"

# Kurumsal koyu tema renkleri (B2B Finans Terminali — IBM Plex paleti)
THEME = {
    "bg_primary": "#08111E",
    "bg_secondary": "#0B1626",
    "bg_card": "#0E1C2E",
    "accent_green": "#14E08A",
    "accent_blue": "#3b82f6",
    "accent_orange": "#FFB23E",
    "accent_red": "#FF5C5C",
    "text_primary": "#E8EEF4",
    "text_secondary": "#8AA0B4",
    "border": "#1B2E44",
}
