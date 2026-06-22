"""
SustainaQuant AI – Genişletilmiş ESG Veri Seti
================================================
Tüpraş, ASELSAN ve Ford Otosan için hem söylem (rapordaki iddialar)
hem de eylem (bağımsız kaynaklardan doğrulanan gerçek veriler) içerir.

Kaynak Felsefesi (Rapor §6 – Risk Önlemi):
  Yalnızca güvenilirliği kanıtlanmış (whitelist) resmi kurumlar,
  ajanslar ve STK'lar kullanılır.
"""


def get_esg_dataset():
    """
    MVP için tam entegre ESG veri setini döndürür.
    Her kayıt: şirket adı, ESG kategorisi, söylem (rapordaki iddia),
    eylem (bağımsız kaynak bulgusu), kaynak bilgisi ve tarih içerir.
    """
    return [
        # ──────────────────────────────────────────────────────
        # TÜPRAŞ – Enerji Verimliliği
        # ──────────────────────────────────────────────────────
        {
            "sirket_adi": "Tüpraş",
            "sektor": "Enerji / Rafineri",
            "bist_kodu": "TUPRS",
            "esg_kategorisi": "Enerji Verimliliği",
            "soylem": (
                "2025 yılında 112 adet enerji verimliliği projesi hayata "
                "geçirilmiş; 2.448 TJ enerji tasarrufu ve 142.940 ton CO2e "
                "emisyon azaltımı sağlanmıştır."
            ),
            "eylem": (
                "T.C. Çevre, Şehircilik ve İklim Değişikliği Bakanlığı'nın "
                "2025 yılı ÇED (Çevresel Etki Değerlendirmesi) kararlarına göre "
                "Tüpraş İzmit Rafinerisi'nin kapasite artırım projesi için "
                "'ÇED Olumlu' kararı verilmiştir. Ancak EPDK verilerine göre "
                "rafinerinin toplam enerji tüketimi bir önceki yıla kıyasla "
                "%3,2 artış göstermiştir. Enerji verimliliği projelerinin "
                "tasarruf etkisi, artan üretim kapasitesi nedeniyle net "
                "emisyon düşüşüne tam olarak yansımamıştır."
            ),
            "eylem_tarihi": "2025-03-15",
            "kaynak": "T.C. Çevre Bakanlığı ÇED Kararları & EPDK Sektör Raporu",
            "kaynak_tipi": "Resmi Kurum",
            "kaynak_url": "https://ced.csb.gov.tr",
            "guvenilirlik": "Yüksek",
        },

        # ──────────────────────────────────────────────────────
        # ASELSAN – Yenilenebilir Enerji
        # ──────────────────────────────────────────────────────
        {
            "sirket_adi": "ASELSAN",
            "sektor": "Savunma Sanayi / Teknoloji",
            "bist_kodu": "ASELS",
            "esg_kategorisi": "Yenilenebilir Enerji",
            "soylem": (
                "Niğde ve Şanlıurfa'da 2026 yılı sonunda devreye alınması "
                "planlanan 113 MWm kurulu güçte GES inşa edilecektir. Yıllık "
                "yaklaşık 185 milyon kWh elektrik üretimi öngörülmektedir."
            ),
            "eylem": (
                "TEDAŞ ve Enerji Bakanlığı açık verilerine göre ASELSAN'ın "
                "Niğde GES projesi için arazi tahsis süreci 2025 Q2 itibarıyla "
                "tamamlanmış, ancak inşaat ruhsatı henüz alınmamıştır. "
                "Şanlıurfa lokasyonunda ise ÇED süreci devam etmektedir. "
                "Projenin 2026 sonu hedefine yetişme riski bulunmaktadır. "
                "Mevcut durumda kurulu güç 0 MWm'dir; fiziksel ilerleme "
                "taahhüdün gerisinde kalmaktadır."
            ),
            "eylem_tarihi": "2025-06-01",
            "kaynak": "TEDAŞ & Enerji Bakanlığı Açık Verileri",
            "kaynak_tipi": "Resmi Kurum",
            "kaynak_url": "https://www.enerji.gov.tr",
            "guvenilirlik": "Yüksek",
        },

        # ──────────────────────────────────────────────────────
        # FORD OTOSAN – Su Kullanımı
        # ──────────────────────────────────────────────────────
        {
            "sirket_adi": "Ford Otosan",
            "sektor": "Otomotiv",
            "bist_kodu": "FROTO",
            "esg_kategorisi": "Su Kullanımı",
            "soylem": (
                "Üretilen araç başına temiz su kullanımı 2024 yılında "
                "2,99 m³/araç iken 2025 yılında 2,51 m³/araç olarak "
                "azaltılmıştır."
            ),
            "eylem": (
                "Kocaeli İSU (Su ve Kanalizasyon İdaresi) ile Ford Otosan "
                "arasında imzalanan 2025 yılı Su Protokolü verilerine göre "
                "Gölcük fabrikasının toplam su tüketimi 1,82 milyon m³ olarak "
                "gerçekleşmiştir. Araç başına su kullanımı 2,51 m³ değeri "
                "doğrulanmıştır. Ancak İSU raporunda fabrika çevresindeki "
                "yeraltı su seviyelerinde %7 düşüş kaydedilmiş olup, "
                "mutlak su ayak izi (toplam tüketim) artmaya devam etmektedir."
            ),
            "eylem_tarihi": "2025-04-20",
            "kaynak": "Kocaeli İSU Su Protokolü & Çevresel İzleme Raporu",
            "kaynak_tipi": "Resmi Kurum",
            "kaynak_url": "https://www.isu.gov.tr",
            "guvenilirlik": "Yüksek",
        },
    ]


def get_companies():
    """Benzersiz şirket listesini döndürür."""
    dataset = get_esg_dataset()
    companies = {}
    for record in dataset:
        name = record["sirket_adi"]
        if name not in companies:
            companies[name] = {
                "sirket_adi": name,
                "sektor": record["sektor"],
                "bist_kodu": record["bist_kodu"],
            }
    return list(companies.values())


def get_company_data(company_name: str):
    """Belirli bir şirketin tüm ESG verilerini döndürür."""
    dataset = get_esg_dataset()
    return [r for r in dataset if r["sirket_adi"] == company_name]


def validate_dataset():
    """Veri setinin bütünlüğünü kontrol eder."""
    dataset = get_esg_dataset()
    errors = []

    required_fields = [
        "sirket_adi", "sektor", "bist_kodu", "esg_kategorisi",
        "soylem", "eylem", "eylem_tarihi", "kaynak", "kaynak_tipi",
    ]

    for i, record in enumerate(dataset):
        for field in required_fields:
            if field not in record or not record[field]:
                errors.append(f"Kayıt {i}: '{field}' alanı eksik veya boş")
            if record.get(field) == "Bekleniyor":
                errors.append(f"Kayıt {i}: '{field}' hâlâ 'Bekleniyor' durumunda")

    return {"valid": len(errors) == 0, "errors": errors, "record_count": len(dataset)}
