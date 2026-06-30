# SustainQuant AI

NLP tabanlı ESG Risk ve Yeşil Aklama (Greenwashing) Tespit Motoru — **Teknofest FinTech 2026**

| | |
|---|---|
| **Takım** | SustainQuant AI |
| **Takım ID** | 918431 |
| **Repo** | https://github.com/sude26/SustainQuant-AI |

---

## Önemli: `localhost` linkleri GitHub'dan açılmaz

README'deki `http://localhost:8501` gibi adresler **yalnızca kendi bilgisayarınızda** uygulamayı çalıştırdıktan sonra tarayıcıda açılır. GitHub sayfasındaki linke tıklamak çalışmaz — önce aşağıdaki kurulumu yapıp sunucuyu başlatmanız gerekir.

---

## Hızlı başlangıç

### 1. Repoyu indirin

```bash
git clone https://github.com/sude26/SustainQuant-AI.git
cd SustainQuant-AI
```

### 2. İlk kurulum (yalnızca bir kez)

```bash
python run.py setup
```

> **Not:** Anaconda `base` kullanmayın. Proje otomatik olarak `.venv` sanal ortamını kullanır.

### 3. Uygulamayı başlatın

```bash
python run.py stop    # eski süreç varsa kapatır
python run.py web     # dashboard başlatır
```

Terminal açık kalsın. Şu satırı görünce hazırsınız:

```
URL: http://localhost:8501
```

### 4. Tarayıcıda açın

Adres çubuğuna **elle** yazın veya Terminal'deki linke Cmd+tık yapın:

```
http://localhost:8501
```

Sayfa eski görünürse: **Cmd+Shift+R** (sert yenile)

---

## Komutlar (`run.py`)

| Komut | Ne yapar |
|-------|----------|
| `python run.py setup` | İlk kurulum (venv + bağımlılıklar) |
| `python run.py web` | **Dashboard** → port `8501` |
| `python run.py stop` | Dashboard'u kapatır |
| `python run.py all` | API (`8000`) + Dashboard (`8501`) birlikte |
| `python run.py api` | Yalnızca FastAPI sunucusu |
| `python run.py analyze` | CLI hızlı portföy analizi |

---

## Dashboard modları (sunum)

Uygulama açıldıktan sonra sol menüden mod seçin:

| Mod | Kullanım |
|-----|----------|
| **Jüri Demo** | 30 sn canlı demo — 3 flagship şirket, en güvenli sunum |
| **Kayıtlı Şirket** | 15 BIST şirketi, tam söylem+eylem dataset |
| **Canlı Doğrulama** | KAP + haber RSS; serbest BIST kodu (örn. `SASA`, `THYAO`) |
| **PDF Rapor Yükle** | Sürdürülebilirlik PDF'inden söylem çıkarma |
| **Portföy Tarama** | Tüm şirketler + anomali ısı haritası |
| **Manuel Giriş** | Serbest metin analizi |

### Sunum önerisi (5 dk)

1. **Jüri Demo** → `SUNUMU BAŞLAT`
2. **Canlı Doğrulama** → `SASA` → izleme modu / Takibe Alınmalı
3. **Kayıtlı Şirket** → Tüpraş → Doğrudan Çelişki örneği
4. Analiz sonrası → **Skor Denetim Dosyası** PDF indir

---

## PDF raporları (uygulama içinden)

Analiz tamamlandıktan sonra sonuç ekranının altında:

- **Jüri PDF Raporu** — şirket analiz özeti
- **Skor Denetim Dosyası** — risk skorunun adım adım hesabı (teknik jüri soruları için)

Portföy özeti: **Portföy Tarama** → `TÜM ŞİRKETLERİ TARA` → `Jüri PDF Özeti İndir`

---

## Mimari

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Streamlit  │────▶│   FastAPI    │────▶│  NLP Motoru     │
│  Terminal   │     │   REST/WS    │     │  Say-Do Gap     │
└─────────────┘     └──────────────┘     └─────────────────┘
       │                    │                     │
       ▼                    ▼                     ▼
  Jüri Demo            /ws/alerts           Kosinüs + Duygu
  PDF Export           KAP / Haber          Entity Extract
```

| Katman | Dizin | Görev |
|--------|-------|-------|
| Veri | `data/` | 15 BIST şirketi, KAP, PDF, RSS |
| NLP | `nlp/` | Say-Do Gap, Lite/Full mod |
| API | `api/` | DaaS + SaaS endpoint'leri |
| UI | `app.py` | B2B Finans Terminali |

---

## Say-Do Gap algoritması

1. **Söylem** (şirket iddiası) ve **Eylem** (bağımsız kaynak) vektörleştirilir
2. **Kosinüs benzerliği** ölçülür (%65 ağırlık)
3. **Duygu boşluğu** hesaplanır (%35 ağırlık)
4. **Entity extraction** ile sayısal çelişkiler taranır
5. **Risk skoru** (0–100) ve anomali sınıfı üretilir

| Skor | Anomali |
|------|---------|
| 0–25 | Tam Uyum |
| 26–50 | Kapsam Uyuşmazlığı |
| 51–75 | Doğrudan Çelişki |
| 76–100 | Veri Yetersizliği / Takibe Alınmalı |

---

## NLP modları

| Mod | Açıklama |
|-----|----------|
| **Lite** (varsayılan) | Offline, hızlı, jüri demosu için güvenli |
| **Full** | FinBERT + Sentence Transformers — `SQ_NLP_MODE=full` |

---

## API (yerel — `python run.py all` sonrası)

> Bu adresler de yalnızca kendi makinenizde çalışır.

| Servis | Adres |
|--------|-------|
| Swagger docs | http://localhost:8000/docs |
| WebSocket alarmlar | `ws://localhost:8000/api/v1/ws/alerts` |
| Demo API Key | `sq-demo-2026-teknofest` |

Dashboard'da **API Backend (FastAPI)** kutusunu işaretleyerek terminali API'ye bağlayabilirsiniz.

---

## Takım arkadaşı için güncelleme

```bash
git pull origin main
python run.py stop
python run.py web
```

---

## Bilinen sınırlar

- Dataset'te **15 şirket** tam çapraz doğrulama; diğerleri (örn. SASA) **izleme modu**
- Canlı KAP/haber için internet gerekir
- Arayüz Streamlit (rapordaki React hedefi MVP'de Streamlit terminal ile karşılandı)

---

## Lisans

Teknofest Finansal Teknolojiler Yarışması 2026 — SustainQuant AI
