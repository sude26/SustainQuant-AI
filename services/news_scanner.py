"""
SustainaQuant AI – Otomatik Haber Tarama
==========================================
Portföy şirketleri için periyodik RSS taraması ve alarm üretimi.
"""

from __future__ import annotations

from data.esg_dataset import get_companies
from data.news_matcher import get_news_matcher
from services.alert_bus import publish_alert

_seen_urls: set[str] = set()


def scan_portfolio_news(max_per_company: int = 2) -> dict:
    """
    Tüm kayıtlı şirketler için haber tarar.
    Yeni eşleşmelerde alarm üretir.
    """
    matcher = get_news_matcher()
    companies = get_companies()
    total_matches = 0
    new_alerts = 0

    for company in companies:
        name = company["sirket_adi"]
        code = company["bist_kodu"]
        try:
            matches = matcher.search(name, code, max_results=max_per_company)
        except Exception:
            continue

        for item in matches:
            total_matches += 1
            url = item.get("link") or item.get("title", "")
            if url in _seen_urls:
                continue
            _seen_urls.add(url)
            new_alerts += 1
            publish_alert(
                title=f"ESG Haber Eşleşmesi — {name}",
                message=item.get("title", "")[:200],
                severity="med",
                company_name=name,
                bist_code=code,
                source=item.get("feed", "RSS"),
            )

    return {
        "companies_scanned": len(companies),
        "total_matches": total_matches,
        "new_alerts": new_alerts,
    }


def reset_seen_cache():
    _seen_urls.clear()
