"""
SustainaQuant AI – Lite Entity Extraction (Mini-NER)
=====================================================
Söylem ve eylem metinlerinden sayısal iddiaları çıkarır ve karşılaştırır.
"""

from __future__ import annotations

import re


_UNIT_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*"
    r"(%|ton(?:\s*CO2e?)?|TJ|MWm?|m³|m3|milyon|adet|TL|bin)?",
    re.IGNORECASE,
)

_POSITIVE_CLAIM = ("azalt", "tasarruf", "düşür", "dusur", "verimlilik", "iyileş", "hedef")
_NEGATIVE_ACTION = ("artış", "artis", "arttı", "artti", "artmış", "gecik", "henüz", "yetersiz", "gerisinde")


def _normalize_num(raw: str) -> float:
    return float(raw.replace(",", "."))


def extract_metrics(text: str) -> list[dict]:
    """Metinden sayı + birim çiftleri çıkarır."""
    metrics = []
    seen = set()
    for match in _UNIT_PATTERN.finditer(text):
        value = match.group(1)
        unit = (match.group(2) or "").strip()
        key = (value, unit.lower())
        if key in seen:
            continue
        seen.add(key)
        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 40)
        context = text[start:end].strip()
        metrics.append({
            "value": _normalize_num(value),
            "unit": unit,
            "raw": match.group(0).strip(),
            "context": context,
        })
    return metrics[:12]


def analyze_entity_gap(soylem: str, eylem: str) -> dict:
    """
    Söylem vs eylem sayısal ve yönsel çelişki analizi.
    """
    soylem_m = extract_metrics(soylem)
    eylem_m = extract_metrics(eylem)
    conflicts = []

    sl, el = soylem.lower(), eylem.lower()
    claim_positive = any(k in sl for k in _POSITIVE_CLAIM)
    action_negative = any(k in el for k in _NEGATIVE_ACTION)

    if claim_positive and action_negative:
        conflicts.append({
            "type": "directional",
            "title": "Yönsel Çelişki",
            "description": (
                "Söylem iyileşme/azalım iddia ederken eylem metninde artış, "
                "gecikme veya yetersizlik sinyalleri tespit edildi."
            ),
            "severity": "high",
        })

    # Yüzde karşılaştırma
    soylem_pcts = [m for m in soylem_m if m["unit"] == "%"]
    eylem_pcts = [m for m in eylem_m if m["unit"] == "%"]
    for sp in soylem_pcts[:3]:
        for ep in eylem_pcts[:3]:
            if abs(sp["value"] - ep["value"]) > 5 and "azalt" in sl and "art" in el:
                conflicts.append({
                    "type": "numeric",
                    "title": "Sayısal Sapma",
                    "description": (
                        f"Söylem %{sp['value']:.1f} iddiası; eylem metninde %{ep['value']:.1f} "
                        f"değeri — tutarsızlık sinyali."
                    ),
                    "severity": "med",
                })

    summary_parts = []
    if conflicts:
        summary_parts.append(f"{len(conflicts)} sayısal/yönsel çelişki tespit edildi.")
    else:
        summary_parts.append("Belirgin sayısal çelişki tespit edilmedi.")
    summary_parts.append(f"Söylem: {len(soylem_m)} metrik, Eylem: {len(eylem_m)} metrik çıkarıldı.")

    return {
        "soylem_metrics": soylem_m,
        "eylem_metrics": eylem_m,
        "conflicts": conflicts,
        "has_conflict": len(conflicts) > 0,
        "summary": " ".join(summary_parts),
    }
