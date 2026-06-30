# SustainQuant AI

NLP tabanlı ESG Risk ve Yeşil Aklama (Greenwashing) Tespit Motoru — **Teknofest FinTech 2026**

> Bu README, projeyi hiç kimseye sormadan kurup çalıştırmak, sunmak ve paylaşmak için yazıldı.

---

## Tüm linkler (tek bakışta)

| Ne | Link / bilgi |
|----|----------------|
| **GitHub repo** | https://github.com/sude26/SustainQuant-AI |
| **Takım adı** | SustainQuant AI |
| **Takım ID** | 918431 |
| **Başvuru ID** | 4896395 |
| **Dashboard** (yerel) | http://localhost:8501 — *aşağıdaki kurulumdan sonra* |
| **API docs** (yerel) | http://localhost:8000/docs — *`python run.py all` sonrası* |
| **Teknofest** | https://www.teknofest.org |
| **Proje raporu (metin)** | [`Proje rapor.txt`](Proje%20rapor.txt) |
| **Başvuru PDF** | [`R5udVDQlwN85dC7yPJbRgfUUCiSsUXQC.pdf`](R5udVDQlwN85dC7yPJbRgfUUCiSsUXQC.pdf) |

### Takım GitHub

| Üye | GitHub | Katkı alanı |
|-----|--------|-------------|
| sude26 | https://github.com/sude26 | UI, canlı KAP/haber, jüri demo, entegrasyon |
| dabilci | https://github.com/dabilci | NLP motoru, FastAPI, veri katmanı çekirdeği |

> LinkedIn profillerinize repo linkini ekleyin: `https://github.com/sude26/SustainQuant-AI`  
> Aşağıda hazır LinkedIn metni var — kopyalayıp yapıştırabilirsiniz.

---

## Önemli: `localhost` GitHub'dan açılmaz

`http://localhost:8501` **yalnızca kendi bilgisayarınızda** uygulamayı çalıştırdıktan sonra tarayıcıda açılır. GitHub README'deki linke tıklamak çalışmaz — bu bir hata değil, `localhost` her zaman "bu bilgisayar" demektir.

---

## Sıfırdan kurulum (5 adım)

### 1. Repoyu klonlayın

```bash
git clone https://github.com/sude26/SustainQuant-AI.git
cd SustainQuant-AI
```

### 2. İlk kurulum (yalnızca bir kez, 5–10 dk)

```bash
python run.py setup
```

- macOS / Linux: `python3 run.py setup` de çalışır
- **Anaconda `base` kullanmayın** — proje `.venv` ile çalışır

### 3. Sunucuyu başlatın

```bash
python run.py stop    # eski süreç varsa kapatır
python run.py web     # dashboard
```

Terminal **açık kalsın**. Şunu görünce hazırsınız:

```
URL: http://localhost:8501
```

### 4. Tarayıcıda açın

Adres çubuğuna **elle** yazın:

```
http://localhost:8501
```

### 5. Güncel kodu çekin (her oturum öncesi)

```bash
git pull origin main
python run.py stop
python run.py web
```

Sayfa eski görünürse: **Cmd+Shift+R** (Windows: Ctrl+Shift+R)

---

## Komutlar

| Komut | Ne yapar |
|-------|----------|
| `python run.py setup` | İlk kurulum |
| `python run.py web` | Dashboard → port `8501` |
| `python run.py stop` | Dashboard'u kapatır |
| `python run.py all` | API (`8000`) + Dashboard birlikte |
| `python run.py api` | Yalnızca FastAPI |
| `python run.py analyze` | CLI portföy analizi |

---

## Dashboard modları

| Mod | Ne için | Sunumda |
|-----|---------|---------|
| **Jüri Demo** | 3 şirket, otomatik akış | ⭐ En güvenli başlangıç |
| **Kayıtlı Şirket** | 15 BIST, tam dataset | Tüpraş çelişki örneği |
| **Canlı Doğrulama** | KAP + haber, serbest BIST | SASA izleme modu |
| **PDF Rapor Yükle** | PDF'den söylem çıkarma | İsteğe bağlı |
| **Portföy Tarama** | Isı haritası, tüm şirketler | Genel bakış |
| **Manuel Giriş** | Serbest metin | Yedek |

### 5 dakikalık sunum akışı

1. **Jüri Demo** → `SUNUMU BAŞLAT`
2. **Canlı Doğrulama** → BIST: `SASA` → **Takibe Alınmalı**
3. **Kayıtlı Şirket** → Tüpraş → **Doğrudan Çelişki**
4. Sonuç ekranı → **Skor Denetim Dosyası** indir

### Jüri Demo konuşma metni (sidebar → Sunum notları)

| Adım | Şirket | Jüriye söylenecek |
|------|--------|-------------------|
| 1 | Tüpraş | Enerji tasarrufu iddiası vs EPDK — tüketim artmış |
| 2 | ASELSAN | 113 MWm GES hedefi vs kurulu güç 0 MWm |
| 3 | Ford Otosan | Birim su düşüşü vs mutlak tüketim artışı |

---

## PDF raporları

Analiz sonrası sonuç ekranının altında:

- **Jüri PDF Raporu** — analiz özeti
- **Skor Denetim Dosyası** — skor hesabı (teknik jüri soruları)

Portföy: **Portföy Tarama** → `TÜM ŞİRKETLERİ TARA` → `Jüri PDF Özeti İndir`

---

## Proje dosya rehberi

| Dosya / klasör | İçerik |
|----------------|--------|
| `app.py` | Streamlit B2B terminali (ana UI) |
| `run.py` | Kurulum ve sunucu başlatıcı |
| `config.py` | Model, API, eşik ayarları |
| `data/esg_dataset.py` | 15 BIST şirket verisi |
| `data/kap_fetcher.py` | KAP bildirim çekici |
| `data/news_matcher.py` | Haber RSS eşleştirme |
| `nlp/analyzer.py` | Say-Do Gap ana motor |
| `services/live_verification.py` | Canlı doğrulama + izleme modu |
| `services/jury_report.py` | PDF rapor üretici |
| `api/` | FastAPI REST + WebSocket |
| `data/demo_scenario.py` | Jüri demo senaryosu |
| `Proje rapor.txt` | Teknofest ön değerlendirme raporu |
| `R5udVDQlwN85dC7yPJbRgfUUCiSsUXQC.pdf` | Başvuru PDF |

---

## Mimari

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Streamlit  │────▶│   FastAPI    │────▶│  NLP Motoru     │
│  Terminal   │     │   REST/WS    │     │  Say-Do Gap     │
└─────────────┘     └──────────────┘     └─────────────────┘
```

| Katman | Dizin | Görev |
|--------|-------|-------|
| Veri | `data/` | Dataset, KAP, PDF, RSS |
| NLP | `nlp/` | Say-Do Gap, Lite/Full |
| API | `api/` | DaaS + SaaS |
| UI | `app.py` | B2B terminal |

---

## Say-Do Gap algoritması

1. Söylem + Eylem vektörleştirilir
2. Kosinüs benzerliği (%65)
3. Duygu boşluğu (%35)
4. Entity extraction (sayısal çelişki)
5. Risk skoru 0–100 + anomali sınıfı

| Skor | Anomali |
|------|---------|
| 0–25 | Tam Uyum |
| 26–50 | Kapsam Uyuşmazlığı |
| 51–75 | Doğrudan Çelişki |
| 76–100 | Veri Yetersizliği / Takibe Alınmalı |

---

## API (yerel)

`python run.py all` sonrası:

| Servis | Adres |
|--------|-------|
| Swagger | http://localhost:8000/docs |
| WebSocket | `ws://localhost:8000/api/v1/ws/alerts` |
| API Key | `sq-demo-2026-teknofest` |

Dashboard → **API Backend (FastAPI)** kutusunu işaretleyin.

---

## Sorun giderme

| Sorun | Çözüm |
|-------|--------|
| Sayfa açılmıyor | `python run.py stop` → `python run.py web` |
| Eski arayüz | Cmd+Shift+R |
| Port 8501 meşgul | `python run.py stop` |
| SASA eylem boş | `git pull` + sunucu restart |
| Analiz sonucu kayboluyor | Güncel `main` branch — `git pull` |
| PDF indirilmiyor | Güncel kod; analiz bitince butonlar altta çıkar |
| KAP/haber çalışmıyor | İnternet bağlantısı gerekir |

---

## Bilinen sınırlar

- 15 şirket tam doğrulama; diğerleri (SASA vb.) **izleme modu**
- Lite NLP varsayılan (sunum için yeterli); Full: `SQ_NLP_MODE=full`
- Arayüz Streamlit (MVP); rapordaki React hedefi sonraki faz

---

## LinkedIn için hazır metin

Aşağıyı kopyalayıp LinkedIn'de **Proje / Deneyim** veya gönderi olarak paylaşabilirsiniz. `localhost` linki ekleme — yerine GitHub repo linkini koyun.

### Türkçe (kısa)

```
SustainQuant AI — Teknofest FinTech 2026 | Takım ID: 918431

Yatırım portföyleri için NLP tabanlı ESG risk ve yeşil aklama (greenwashing) tespit motoru.

Şirketlerin sürdürülebilirlik iddialarını (söylem) bağımsız kaynaklarla (eylem) saniyeler içinde karşılaştırıyoruz. Özgün "Say-Do Gap" algoritması: kosinüs benzerliği + duygu analizi + entity extraction → 0-100 risk skoru.

Stack: Python, FastAPI, Streamlit, KAP entegrasyonu, haber RSS, WebSocket alarmlar.

GitHub: https://github.com/sude26/SustainQuant-AI
```

### English (short)

```
SustainQuant AI — Teknofest FinTech 2026 | Team ID: 918431

NLP-based ESG risk and greenwashing detection for investment portfolios.

We cross-check corporate sustainability claims against independent sources in seconds using our Say-Do Gap algorithm (cosine similarity + sentiment gap + entity extraction).

Stack: Python, FastAPI, Streamlit, live KAP/news verification.

GitHub: https://github.com/sude26/SustainQuant-AI
```

### LinkedIn'de yapılacaklar (checklist)

- [ ] Profilde **Öne çıkan** veya **Projeler** bölümüne repo linki ekle
- [ ] Proje adı: `SustainQuant AI`
- [ ] URL: `https://github.com/sude26/SustainQuant-AI`
- [ ] Teknolojiler: Python, NLP, FastAPI, Streamlit, FinTech, ESG
- [ ] Takım arkadaşını **iş birliği** veya gönderide etiketle
- [ ] Canlı demo için: "Demo yerel çalışır — repo README'de kurulum adımları var"

---

## Katkı ve geliştirme

```bash
git pull origin main          # güncel kod
git checkout -b feature/xyz   # yeni özellik
# ... değişiklik ...
git add .
git commit -m "Açıklama"
git push origin feature/xyz
```

`main` branch'e merge için PR açın veya takım içi anlaşmaya göre doğrudan push.

---

## Lisans

Teknofest Finansal Teknolojiler Yarışması 2026 — SustainQuant AI
