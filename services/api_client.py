"""
SustainaQuant AI – API İstemcisi
=================================
Streamlit dashboard'un FastAPI backend'e bağlanması için.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from config import API_BASE_URL, DEMO_API_KEY


class SustainQuantAPIClient:
    """FastAPI backend istemcisi."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or API_BASE_URL).rstrip("/")
        self.api_key = api_key or DEMO_API_KEY
        self._timeout = 30.0

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["X-API-Key"] = self.api_key
        return h

    def health(self) -> dict:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{self.base_url}/api/v1/health")
            resp.raise_for_status()
            return resp.json()

    def is_available(self) -> bool:
        try:
            data = self.health()
            return data.get("status") == "healthy"
        except Exception:
            return False

    def analyze_custom(self, company_name: str, category: str, soylem: str, eylem: str) -> dict:
        payload = {
            "company_name": company_name,
            "category": category,
            "soylem": soylem,
            "eylem": eylem,
        }
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                f"{self.base_url}/api/v1/analyze",
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    def verify_live(self, company_name: str, bist_code: str, soylem: str,
                    category: str = "Genel ESG", **kwargs) -> dict:
        payload = {
            "company_name": company_name,
            "bist_code": bist_code,
            "category": category,
            "soylem": soylem,
            **kwargs,
        }
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                f"{self.base_url}/api/v1/verify/live",
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    def portfolio_summary(self) -> dict:
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.get(
                f"{self.base_url}/api/v1/dashboard/summary",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    def recent_alerts(self, limit: int = 10) -> list[dict]:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(
                f"{self.base_url}/api/v1/alerts",
                params={"limit": limit},
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json().get("alerts", [])

    def scan_news(self) -> dict:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{self.base_url}/api/v1/alerts/scan-news",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()


_default_client: SustainQuantAPIClient | None = None


def get_api_client() -> SustainQuantAPIClient:
    global _default_client
    if _default_client is None:
        _default_client = SustainQuantAPIClient()
    return _default_client


def use_api_backend() -> bool:
    from config import USE_API_BACKEND
    return USE_API_BACKEND or os.environ.get("SQ_USE_API", "false").lower() in ("1", "true", "yes")
