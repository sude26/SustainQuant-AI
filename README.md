# SustainQuant AI

NLP tabanli ESG Risk ve Yesil Aklama (Greenwashing) Tespit Motoru — Teknofest FinTech 2026

**Takim ID:** 918431

## Hizli Baslangic

```bash
cd SustainQuant-AI
python run.py setup      # ilk kurulum (bir kez)
python run.py web        # dashboard → http://localhost:8501
python run.py all        # API + Dashboard (WebSocket alarmlar)
```

> Anaconda `base` kullanmayin. Proje `.venv` ile calisir.

## Mimari

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Streamlit  │────▶│   FastAPI    │────▶│  NLP Motoru     │
│  Terminal   │     │   REST/WS    │     │  Say-Do Gap     │
└─────────────┘     └──────────────┘     └─────────────────┘
       │                    │                     │
       ▼                    ▼                     ▼
  Juri Demo            /ws/alerts           Kosinus + Duygu
  PDF Export           KAP / Haber          Entity Extract
```

### Katmanlar

| Katman | Dosya | Gorev |
|--------|-------|-------|
| Veri | `data/` | 15 BIST sirketi, KAP, PDF, RSS |
| NLP | `nlp/` | Say-Do Gap, Lite/Full mod |
| API | `api/` | DaaS + SaaS endpointleri |
| UI | `app.py` | B2B Finans Terminali |

## Say-Do Gap Algoritmasi

1. **Soylem** (rapor iddiasi) ve **Eylem** (bagimsiz kaynak) metinleri vektorlestirilir
2. **Kosinus benzerligi** olculur (%65 agirlik)
3. **Duygu boslugu** hesaplanir (%35 agirlik)
4. **Entity extraction** ile sayisal celiskiler taranir
5. **Risk skoru** (0-100) ve anomali sinifi uretilir

## Modlar

| Mod | Aciklama |
|-----|----------|
| Lite (varsayilan) | Offline, hizli, juri demosu icin guvenli |
| Full | FinBERT + Sentence Transformers (`SQ_NLP_MODE=full`) |

## API

- Docs: http://localhost:8000/docs
- WebSocket: `ws://localhost:8000/api/v1/ws/alerts`
- Demo API Key: `sq-demo-2026-teknofest`

## Lisans

Teknofest Finansal Teknolojiler Yarismasi 2026 — SustainQuant AI
