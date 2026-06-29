"""
SustainaQuant AI – Canlı Alarm Bus
====================================
WebSocket ve REST için paylaşımlı anomali alarm kuyruğu.
"""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime
from typing import Any

_MAX_ALERTS = 100
_alerts: deque[dict] = deque(maxlen=_MAX_ALERTS)
_subscribers: set[asyncio.Queue] = set()


def publish_alert(
    title: str,
    message: str,
    severity: str = "med",
    company_name: str = "",
    bist_code: str = "",
    risk_score: float | None = None,
    source: str = "system",
) -> dict:
    """Yeni alarm yayınlar."""
    alert = {
        "id": f"{datetime.now().timestamp():.0f}",
        "title": title,
        "message": message,
        "severity": severity,
        "company_name": company_name,
        "bist_code": bist_code,
        "risk_score": risk_score,
        "source": source,
        "timestamp": datetime.now().isoformat(),
    }
    _alerts.appendleft(alert)
    for queue in list(_subscribers):
        try:
            queue.put_nowait(alert)
        except Exception:
            pass
    return alert


def get_recent_alerts(limit: int = 20) -> list[dict]:
    return list(_alerts)[:limit]


def subscribe() -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    _subscribers.add(queue)
    return queue


def unsubscribe(queue: asyncio.Queue):
    _subscribers.discard(queue)


def alert_from_analysis(result: dict, source: str = "analysis") -> dict | None:
    """Yüksek riskli analiz sonucundan alarm üretir."""
    risk = result.get("risk_score", 0)
    if risk < 40:
        return None
    severity = "high" if risk > 50 else "med"
    return publish_alert(
        title=f"Yeşil Aklama Sinyali — {result.get('company_name', '')}",
        message=result.get("summary", "")[:300],
        severity=severity,
        company_name=result.get("company_name", ""),
        bist_code=result.get("bist_code", ""),
        risk_score=risk,
        source=source,
    )
