"""
SustainaQuant AI – Çoklu Kaynak Teyidi
========================================
Rapordaki whitelist mantığı: 2+ bağımsız kaynak = yüksek güven.
"""

from __future__ import annotations

from config import SOURCE_WHITELIST


def _source_trusted(name: str) -> bool:
    name_lower = (name or "").lower()
    for src in SOURCE_WHITELIST:
        if src.lower() in name_lower or name_lower in src.lower():
            return True
    for token in ("kap", "reuters", "bloomberg", "anadolu", "aa", "epdk", "bakanlık", "bddk", "tcmb"):
        if token in name_lower:
            return True
    return False


def assess_sources(sources: list[dict]) -> dict:
    """
    Kaynak listesini değerlendirir.

    Her kaynak: {source, source_url, text, trusted (opsiyonel), type (opsiyonel)}
    """
    if not sources:
        return {
            "source_count": 0,
            "trusted_count": 0,
            "independent_count": 0,
            "confidence": "düşük",
            "confidence_score": 0,
            "label": "Kaynak yok",
            "details": [],
            "multi_source_verified": False,
        }

    details = []
    trusted_names = set()
    all_names = set()

    for src in sources:
        name = src.get("source") or src.get("name") or "Bilinmeyen"
        trusted = src.get("trusted")
        if trusted is None:
            trusted = _source_trusted(name)
        details.append({
            "source": name,
            "url": src.get("source_url") or src.get("url", ""),
            "type": src.get("type", "genel"),
            "trusted": trusted,
            "preview": (src.get("text") or "")[:200],
        })
        all_names.add(name.lower())
        if trusted:
            trusted_names.add(name.lower())

    trusted_count = len(trusted_names)
    independent_count = len(all_names)
    multi = independent_count >= 2 and trusted_count >= 1

    if multi and trusted_count >= 2:
        confidence, score, label = "yüksek", 85, "Çoklu kaynak teyitli"
    elif multi:
        confidence, score, label = "orta", 65, "Çoklu kaynak (kısmi teyit)"
    elif trusted_count == 1:
        confidence, score, label = "orta", 45, "Tek güvenilir kaynak"
    else:
        confidence, score, label = "düşük", 20, "Kaynak teyidi zayıf"

    return {
        "source_count": len(sources),
        "trusted_count": trusted_count,
        "independent_count": independent_count,
        "confidence": confidence,
        "confidence_score": score,
        "label": label,
        "details": details,
        "multi_source_verified": multi,
    }


def is_usable_action_text(text: str) -> bool:
    """KAP/XBRL placeholder veya çok kısa metinleri filtreler."""
    if not text or len(text.strip()) < 80:
        return False
    bracket_hits = text.count("[") + text.count("]")
    if bracket_hits >= 4:
        return False
    if "[" in text and "]" in text and bracket_hits / max(len(text), 1) > 0.02:
        return False
    return True


def merge_action_sources(kap: dict | None, news: list[dict], dataset_action: str = "") -> tuple[str, list[dict]]:
    """KAP, haber ve veri seti kaynaklarını birleştirir."""
    sources = []

    if kap and kap.get("eylem_text") and is_usable_action_text(kap["eylem_text"]):
        sources.append({
            "source": kap.get("source", "KAP"),
            "source_url": kap.get("source_url", ""),
            "text": kap["eylem_text"],
            "type": "kap",
            "trusted": True,
            "publish_date": kap.get("publish_date"),
        })

    for item in news:
        sources.append({
            "source": item.get("source", item.get("feed", "Haber")),
            "source_url": item.get("source_url", item.get("link", "")),
            "text": item.get("text", ""),
            "type": "haber",
            "trusted": item.get("trusted", False),
            "publish_date": item.get("published"),
        })

    if dataset_action:
        sources.append({
            "source": "Veri Seti (Resmi Kurum)",
            "source_url": "",
            "text": dataset_action,
            "type": "dataset",
            "trusted": True,
        })

    parts = [str(s["text"]).strip() for s in sources if s.get("text")]
    combined = "\n\n".join(p for p in parts if p)
    return combined, sources
