"""
SustainaQuant AI – KAP Bildirim Çekici
========================================
Kamuya açık KAP REST API üzerinden şirket bildirimlerini çeker.
Kaynak: https://www.kap.org.tr (auth gerektirmez)
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from html import unescape
from typing import Optional

import httpx

KAP_BASE = "https://www.kap.org.tr"
KAP_HEADERS = {
    "User-Agent": "SustainQuant-AI/1.0 (Teknofest FinTech 2026)",
    "Referer": f"{KAP_BASE}/tr/bildirim-sorgu",
    "Accept": "application/json",
}

ESG_SUBJECT_KEYWORDS = (
    "sürdürülebilir", "çevre", "esg", "emisyon", "enerji", "iklim",
    "karbon", "sorumluluk", "yeşil", "sera", "atık", "su ",
)

ESG_PRIORITY_SUBJECTS = (
    "Sürdürülebilirlik",
    "Özel Durum Açıklaması",
    "Kurumsal Yönetim",
    "Faaliyet Raporu",
)


def _strip_html(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_kap_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y", "%Y.%m.%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


class KAPFetcher:
    """KAP kamuya açık API istemcisi."""

    def __init__(self, timeout: float = 15.0, min_interval: float = 0.5):
        self.timeout = timeout
        self.min_interval = min_interval
        self._last_request = 0.0
        self._company_cache: dict[str, dict] | None = None

    def _throttle(self):
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request = time.monotonic()

    def _get(self, path: str, referer: str | None = None) -> httpx.Response:
        self._throttle()
        headers = {**KAP_HEADERS, "Referer": referer or KAP_HEADERS["Referer"]}
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            return client.get(f"{KAP_BASE}{path}", headers=headers)

    def _post(self, path: str, payload: dict) -> httpx.Response:
        self._throttle()
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            return client.post(
                f"{KAP_BASE}{path}",
                json=payload,
                headers={**KAP_HEADERS, "Content-Type": "application/json"},
            )

    def load_companies(self, refresh: bool = False) -> dict[str, dict]:
        """BIST şirketlerini ticker → şirket bilgisi olarak cache'ler."""
        if self._company_cache is not None and not refresh:
            return self._company_cache

        resp = self._get("/tr/api/company/items/IGS/A")
        resp.raise_for_status()
        mapping = {}
        for item in resp.json():
            code = (item.get("stockCode") or "").upper()
            if code:
                mapping[code] = item
        self._company_cache = mapping
        return mapping

    def get_company(self, bist_code: str) -> Optional[dict]:
        return self.load_companies().get(bist_code.upper())

    def list_disclosures(
        self,
        bist_code: str,
        days_back: int = 180,
        limit: int = 50,
    ) -> list[dict]:
        """Şirkete ait bildirim listesini döndürür."""
        company = self.get_company(bist_code)
        if not company:
            return []

        end = datetime.now()
        start = end - timedelta(days=days_back)
        payload = {
            "fromDate": start.strftime("%Y-%m-%d"),
            "toDate": end.strftime("%Y-%m-%d"),
            "mkkMemberOidList": [company["mkkMemberOid"]],
            "subjectList": [],
        }
        resp = self._post("/tr/api/disclosure/members/byCriteria", payload)
        resp.raise_for_status()
        items = resp.json() or []
        return items[:limit]

    def _score_disclosure(self, item: dict) -> int:
        subject = (item.get("subject") or "") + " " + (item.get("summary") or "")
        subject_lower = subject.lower()
        score = 0
        for kw in ESG_SUBJECT_KEYWORDS:
            if kw in subject_lower:
                score += 2
        for pri in ESG_PRIORITY_SUBJECTS:
            if pri.lower() in subject_lower:
                score += 5
        if "sürdürülebilirlik uyum" in subject_lower:
            score += 10
        return score

    def find_esg_disclosures(self, bist_code: str, days_back: int = 365) -> list[dict]:
        """ESG ile ilgili bildirimleri öncelik sırasına göre döndürür."""
        items = self.list_disclosures(bist_code, days_back=days_back, limit=200)
        scored = [(self._score_disclosure(x), x) for x in items]
        scored = [pair for pair in scored if pair[0] > 0]
        scored.sort(key=lambda p: p[0], reverse=True)
        return [item for _, item in scored]

    def get_disclosure_detail(self, disclosure_index: int) -> dict:
        """Bildirim detay metnini ve meta verisini döndürür."""
        referer = f"{KAP_BASE}/tr/Bildirim/{disclosure_index}"
        resp = self._get(f"/tr/api/notification/attachment-detail/{disclosure_index}", referer=referer)
        resp.raise_for_status()
        payload = resp.json()
        if not payload:
            return {}

        entry = payload[0]
        basic = entry.get("disclosure", {}).get("disclosureBasic", {})
        bodies = entry.get("disclosureBody") or []
        raw_html = bodies[0] if bodies else ""
        text = _strip_html(raw_html)

        return {
            "disclosure_index": disclosure_index,
            "title": basic.get("title") or entry.get("disclosure", {}).get("disclosureBasic", {}).get("summary"),
            "subject": basic.get("title"),
            "publish_date": basic.get("publishDate"),
            "publish_datetime": _parse_kap_date(basic.get("publishDate", "")),
            "stock_code": basic.get("stockCode"),
            "text": text,
            "text_preview": text[:1500],
            "source": "KAP (Kamuyu Aydınlatma Platformu)",
            "source_url": f"{KAP_BASE}/tr/Bildirim/{disclosure_index}",
            "attachment_count": basic.get("attachmentCount", 0),
        }

    def fetch_latest_esg_action(
        self,
        bist_code: str,
        company_name: str = "",
        max_chars: int = 2500,
    ) -> Optional[dict]:
        """
        Şirket için en güncel ESG bildirimini bulur ve eylem metni olarak döndürür.
        """
        disclosures = self.find_esg_disclosures(bist_code)
        if not disclosures:
            disclosures = self.list_disclosures(bist_code, days_back=90, limit=5)
        if not disclosures:
            return None

        best = disclosures[0]
        detail = self.get_disclosure_detail(best["disclosureIndex"])
        if not detail.get("text"):
            summary = best.get("summary") or best.get("subject") or ""
            detail["text"] = summary
            detail["text_preview"] = summary

        text = detail["text"][:max_chars]
        publish = detail.get("publish_date") or best.get("publishDate", "")

        return {
            "bist_code": bist_code.upper(),
            "company_name": company_name or best.get("kapTitle", ""),
            "disclosure_index": best["disclosureIndex"],
            "subject": best.get("subject") or best.get("summary"),
            "publish_date": publish,
            "publish_datetime": detail.get("publish_datetime") or _parse_kap_date(publish),
            "eylem_text": text,
            "source": "KAP (Kamuyu Aydınlatma Platformu)",
            "source_url": detail.get("source_url"),
            "trusted": True,
        }


_default_fetcher: KAPFetcher | None = None


def get_kap_fetcher() -> KAPFetcher:
    global _default_fetcher
    if _default_fetcher is None:
        _default_fetcher = KAPFetcher()
    return _default_fetcher
