"""
SustainaQuant AI – Canlı Doğrulama Orkestratörü
=================================================
KAP + haber + veri seti kaynaklarını birleştirip analiz eder.
"""

from __future__ import annotations

from data.kap_fetcher import get_kap_fetcher
from data.news_matcher import get_news_matcher
from services.verification import assess_sources, merge_action_sources
from services.timeline import analyze_timeline


def fetch_live_context(
    company_name: str,
    bist_code: str,
    category: str = "",
    dataset_eylem: str = "",
    include_kap: bool = True,
    include_news: bool = True,
) -> dict:
    """KAP ve haber kaynaklarını çeker, birleştirir."""
    kap = None
    news = []

    if include_kap and bist_code:
        try:
            kap = get_kap_fetcher().fetch_latest_esg_action(bist_code, company_name)
        except Exception as exc:
            kap = {"error": str(exc)}

    if include_news:
        try:
            news = get_news_matcher().search(company_name, bist_code or "")
        except Exception:
            news = []

    merged_eylem, sources = merge_action_sources(
        kap if kap and not kap.get("error") else None,
        news,
        dataset_eylem,
    )

    verification = assess_sources(sources)

    eylem_date = None
    if kap and kap.get("publish_datetime"):
        eylem_date = kap["publish_datetime"]
    elif kap and kap.get("publish_date"):
        eylem_date = kap.get("publish_date")
    news_dates = [n.get("published_datetime") for n in news if n.get("published_datetime")]
    if news_dates:
        eylem_date = max(news_dates)

    return {
        "kap": kap,
        "news": news,
        "sources": sources,
        "merged_eylem": merged_eylem,
        "verification": verification,
        "eylem_date_hint": eylem_date,
    }


def build_enriched_record(
    base_record: dict,
    live_context: dict,
    soylem_tarihi: str | None = None,
) -> dict:
    """Canlı kaynaklarla zenginleştirilmiş analiz kaydı."""
    record = {**base_record}
    if live_context.get("merged_eylem"):
        record["eylem"] = live_context["merged_eylem"]
    record["sources"] = live_context.get("sources", [])
    record["verification"] = live_context.get("verification", {})
    record["live_kap"] = live_context.get("kap")
    record["live_news"] = live_context.get("news", [])

    if soylem_tarihi:
        record["soylem_tarihi"] = soylem_tarihi
    elif not record.get("soylem_tarihi"):
        record["soylem_tarihi"] = "2025-01-01"

    if live_context.get("eylem_date_hint") and not record.get("eylem_tarihi"):
        hint = live_context["eylem_date_hint"]
        record["eylem_tarihi"] = hint.strftime("%Y-%m-%d") if hasattr(hint, "strftime") else str(hint)

    record["timeline"] = analyze_timeline(
        record.get("soylem_tarihi"),
        record.get("eylem_tarihi"),
        record.get("esg_kategorisi", ""),
    )
    return record
