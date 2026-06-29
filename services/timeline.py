"""
SustainaQuant AI – Zaman Çizelgesi Analizi
============================================
Söylem tarihi ile eylem tarihi arasındaki boşluğu değerlendirir.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional


def _parse_date(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%Y %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def analyze_timeline(
    soylem_date,
    eylem_date,
    category: str = "",
) -> dict:
    """
    Zaman boşluğu anomalisi üretir.

    Returns:
        gap_days, anomaly flag, severity, description
    """
    s_dt = _parse_date(soylem_date)
    e_dt = _parse_date(eylem_date)

    if not s_dt or not e_dt:
        return {
            "soylem_date": str(soylem_date) if soylem_date else None,
            "eylem_date": str(eylem_date) if eylem_date else None,
            "gap_days": None,
            "has_anomaly": False,
            "severity": "low",
            "title": "Zaman verisi eksik",
            "description": "Söylem veya eylem tarihi belirtilmemiş; zaman analizi yapılamadı.",
        }

    gap = (e_dt - s_dt).days
    has_anomaly = False
    severity = "low"
    title = "Zaman uyumu normal"
    description = f"Eylem verisi söylemden {abs(gap)} gün sonra güncellenmiş."

    if gap < 0:
        has_anomaly = True
        severity = "high"
        title = "Zaman Paradoksu"
        description = (
            f"Eylem/haber tarihi ({e_dt.strftime('%d.%m.%Y')}), söylem tarihinden "
            f"({s_dt.strftime('%d.%m.%Y')}) önce — veri tutarsızlığı veya geriye dönük düzeltme sinyali."
        )
    elif gap > 365:
        has_anomaly = True
        severity = "med"
        title = "Uzun Zaman Boşluğu"
        description = (
            f"Söylem ile doğrulama arasında {gap} gün geçmiş. "
            "Taahhüt ile gerçekleşme arasındaki gecikme izlenmeli."
        )
    elif gap > 180:
        has_anomaly = True
        severity = "med"
        title = "Orta Zaman Boşluğu"
        description = (
            f"Söylem ({s_dt.strftime('%d.%m.%Y')}) ile eylem ({e_dt.strftime('%d.%m.%Y')}) "
            f"arasında {gap} gün var; periyodik güncelleme gecikmiş olabilir."
        )

    cat = category.lower()
    if has_anomaly and any(k in cat for k in ("ges", "yenilenebilir", "emisyon", "karbon")):
        description += " Enerji/emisyon taahhütleri için bu süre kritik olabilir."

    return {
        "soylem_date": s_dt.strftime("%Y-%m-%d"),
        "eylem_date": e_dt.strftime("%Y-%m-%d"),
        "gap_days": gap,
        "has_anomaly": has_anomaly,
        "severity": severity,
        "title": title,
        "description": description,
    }
