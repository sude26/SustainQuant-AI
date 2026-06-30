"""
SustainaQuant AI – Canlı Doğrulama Orkestratörü
=================================================
KAP + haber + veri seti kaynaklarını birleştirip analiz eder.

Söylem = şirket iddiası (dataset veya KAP sürdürülebilirlik bildirimi)
Eylem  = bağımsız doğrulama (dataset resmi kaynak + haber RSS)
"""

from __future__ import annotations

from data.kap_fetcher import get_kap_fetcher
from data.news_matcher import get_news_matcher
from data.pdf_extractor import extract_esg_claims
from services.verification import assess_sources, merge_action_sources
from services.timeline import analyze_timeline


def _resolve_soylem(dataset_soylem: str, kap: dict | None) -> tuple[str, str]:
    """Söylem metnini dataset veya KAP bildiriminden üretir."""
    if (dataset_soylem or "").strip():
        return dataset_soylem.strip(), "Dataset (şirket iddiası)"

    if kap and not kap.get("error") and kap.get("eylem_text"):
        raw = kap["eylem_text"]
        claims = extract_esg_claims(raw, max_chars=2000)
        text = claims if claims.strip() else raw[:2000]
        subject = kap.get("subject") or "KAP bildirimi"
        return text, f"KAP — {subject}"

    return "", ""


def fetch_live_context(
    company_name: str,
    bist_code: str,
    category: str = "",
    dataset_soylem: str = "",
    dataset_eylem: str = "",
    include_kap: bool = True,
    include_news: bool = True,
) -> dict:
    """KAP ve haber kaynaklarını çeker; söylem + eylem metinlerini ayırır."""
    kap = None
    news = []

    if include_kap and bist_code:
        try:
            kap = get_kap_fetcher().fetch_latest_esg_disclosure(bist_code, company_name)
        except Exception as exc:
            kap = {"error": str(exc)}

    if include_news:
        try:
            news = get_news_matcher().search(company_name, bist_code or "")
        except Exception:
            news = []

    merged_soylem, soylem_source = _resolve_soylem(dataset_soylem, kap)

    # Eylem: bağımsız kaynaklar — KAP sürdürülebilirlik metni söyleme gider, eyleme karışmaz
    merged_eylem, eylem_sources = merge_action_sources(
        None,
        news,
        dataset_eylem,
    )

    all_sources = list(eylem_sources)
    if merged_soylem:
        if (dataset_soylem or "").strip():
            all_sources.insert(0, {
                "source": "Dataset (Söylem)",
                "source_url": "",
                "text": merged_soylem[:500],
                "type": "soylem_dataset",
                "trusted": True,
            })
        elif kap and kap.get("source_url"):
            all_sources.insert(0, {
                "source": kap.get("source", "KAP Sürdürülebilirlik"),
                "source_url": kap.get("source_url", ""),
                "text": merged_soylem[:500],
                "type": "soylem_kap",
                "trusted": True,
                "publish_date": kap.get("publish_date"),
            })

    verification = assess_sources(eylem_sources)

    eylem_date = None
    news_dates = [n.get("published_datetime") for n in news if n.get("published_datetime")]
    if news_dates:
        eylem_date = max(news_dates)
    elif dataset_eylem:
        eylem_date = None

    return {
        "kap": kap,
        "news": news,
        "sources": all_sources,
        "eylem_sources": eylem_sources,
        "merged_soylem": merged_soylem,
        "soylem_source": soylem_source,
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
    if live_context.get("merged_soylem"):
        record["soylem"] = live_context["merged_soylem"]
    if live_context.get("merged_eylem"):
        record["eylem"] = live_context["merged_eylem"]
    record["sources"] = live_context.get("sources", [])
    record["verification"] = live_context.get("verification", {})
    record["live_kap"] = live_context.get("kap")
    record["live_news"] = live_context.get("live_news", live_context.get("news", []))

    if soylem_tarihi:
        record["soylem_tarihi"] = soylem_tarihi
    elif not record.get("soylem_tarihi"):
        record["soylem_tarihi"] = "2025-01-01"

    kap = live_context.get("kap") or {}
    if kap.get("publish_date") and not record.get("soylem_tarihi"):
        record["soylem_tarihi"] = str(kap["publish_date"])[:10]

    if live_context.get("eylem_date_hint") and not record.get("eylem_tarihi"):
        hint = live_context["eylem_date_hint"]
        record["eylem_tarihi"] = hint.strftime("%Y-%m-%d") if hasattr(hint, "strftime") else str(hint)

    record["timeline"] = analyze_timeline(
        record.get("soylem_tarihi"),
        record.get("eylem_tarihi"),
        record.get("esg_kategorisi", ""),
    )
    return record
