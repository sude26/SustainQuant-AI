"""
SustainaQuant AI – API Key Kimlik Doğrulama
=============================================
B2B SaaS ve DaaS müşterileri için API Key tabanlı auth.
Kullanım takibi (usage tracking) ile DaaS faturalandırma desteği.
"""

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DEMO_API_KEY
from data.database import Database

# API Key header tanımı
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Geçerli API anahtarları (MVP için basit in-memory)
VALID_API_KEYS = {
    DEMO_API_KEY: {
        "owner": "Teknofest Demo",
        "tier": "premium",
        "rate_limit": 1000,  # günlük istek limiti
    },
    "sq-test-key": {
        "owner": "Test User",
        "tier": "free",
        "rate_limit": 50,
    },
}


async def verify_api_key(api_key: str = Security(api_key_header)) -> dict:
    """
    API anahtarını doğrular ve kullanımı loglar.

    MVP'de basit in-memory doğrulama.
    Üretim ortamında veritabanı tabanlı olacak.
    """
    # API key zorunlu değil (demo modda)
    if api_key is None:
        return {"owner": "anonymous", "tier": "demo", "rate_limit": 10}

    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=403,
            detail="Geçersiz API anahtarı. Erişim reddedildi."
        )

    key_info = VALID_API_KEYS[api_key]

    # Kullanımı logla (DaaS faturalandırma için)
    try:
        db = Database()
        db.log_api_usage(api_key, "api_call")
    except Exception:
        pass  # Loglama hatası API'yi engellememeli

    return key_info


async def optional_api_key(api_key: str = Security(api_key_header)) -> dict:
    """
    Opsiyonel API key kontrolü.
    Dashboard iç kullanımı için key gerekmez.
    """
    if api_key and api_key in VALID_API_KEYS:
        return VALID_API_KEYS[api_key]
    return {"owner": "internal", "tier": "dashboard", "rate_limit": -1}
