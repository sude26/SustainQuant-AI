"""
SustainaQuant AI – Jüri Demo Senaryosu
=======================================
30 saniyelik canlı sunum akışı (3 flagship şirket).
"""

DEMO_SCRIPT = [
    {
        "step": 1,
        "title": "Tüpraş — Enerji iddiası vs EPDK verisi",
        "company": "Tüpraş",
        "bist_code": "TUPRS",
        "duration_sec": 10,
        "jury_line": (
            "Şirket 112 enerji verimliliği projesi ve 2.448 TJ tasarruf iddia ediyor. "
            "Sistemimiz EPDK verileriyle çapraz kontrol ediyor — net tüketim artmış."
        ),
        "narration": (
            "Tüpraş 112 enerji verimliliği projesi ve 2.448 TJ tasarruf iddia ediyor. "
            "EPDK verileri ise net enerji tüketiminin arttığını gösteriyor."
        ),
        "hook": "Enerji tasarrufu iddiası ↔ artan tüketim",
        "category": "Enerji Verimliliği",
    },
    {
        "step": 2,
        "title": "ASELSAN — GES taahhüdü vs ruhsat gecikmesi",
        "company": "ASELSAN",
        "bist_code": "ASELS",
        "duration_sec": 10,
        "jury_line": (
            "ASELSAN 113 MWm GES hedefi koymuş. Resmi kayıtlarda kurulu güç hâlâ 0 MWm — "
            "fiziksel ilerleme taahhüdün gerisinde."
        ),
        "narration": (
            "ASELSAN 113 MWm GES hedefi koymuş; resmi kayıtlarda inşaat ruhsatı "
            "henüz alınmamış ve kurulu güç 0 MWm."
        ),
        "hook": "GES hedefi ↔ fiziksel kurulum yok",
        "category": "Yenilenebilir Enerji",
    },
    {
        "step": 3,
        "title": "Ford Otosan — Su verimliliği vs mutlak tüketim",
        "company": "Ford Otosan",
        "bist_code": "FROTO",
        "duration_sec": 10,
        "jury_line": (
            "Ford Otosan araç başına suyu düşürdüğünü bildiriyor. "
            "İSU verileri mutlak su ayak izinin arttığını doğruluyor — klasik yeşil aklama örneği."
        ),
        "narration": (
            "Ford Otosan araç başına su tüketimini düşürdüğünü bildiriyor; "
            "İSU verileri mutlak su ayak izinin arttığını doğruluyor."
        ),
        "hook": "Birim verimlilik ↔ toplam tüketim artışı",
        "category": "Su Kullanımı",
    },
]

DEMO_INTRO = (
    "SustainQuant AI, şirketin sürdürülebilirlik raporundaki iddiayı bağımsız kaynaklarla "
    "saniyeler içinde karşılaştırır ve Yeşil Aklama Risk Skoru üretir."
)


def get_demo_companies():
    return [s["company"] for s in DEMO_SCRIPT]
