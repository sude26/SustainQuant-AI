"""
SustainaQuant AI – WebSocket Alarm Kanalı
==========================================
Anomali bildirimlerini gerçek zamanlı iletir (Faz C).
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.alert_bus import subscribe, unsubscribe, get_recent_alerts

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
  """
  Canlı anomali alarm akışı.
  Bağlantı kurulunca son alarmlar gönderilir, yenileri anlık iletilir.
  """
  await websocket.accept()
  queue = subscribe()
  try:
      for alert in reversed(get_recent_alerts(15)):
          await websocket.send_json(alert)
      while True:
          alert = await queue.get()
          await websocket.send_json(alert)
  except WebSocketDisconnect:
      pass
  finally:
      unsubscribe(queue)
