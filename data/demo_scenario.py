"""
SustainaQuant AI – Jüri Demo Senaryosu
=======================================
30 saniyelik canlı sunum akışı (3 şirket).
"""

DEMO_SCRIPT = [
    {
        "step": 1,
        "title": "Tüpraş — Enerji iddiası vs EPDK verisi",
        "narration": (
            "Tüpraş 112 enerji verimliliği projesi ve 2.448 TJ tasarruf iddia ediyor. "
            "EPDK verileri ise net enerji tüketiminin arttığını gösteriyor."
        ),
        "company": "Tüpraş",
    },
    {
        "step": 2,
        "title": "ASELSAN — GES taahhüdü vs ruhsat gecikmesi",
        "narration": (
            "ASELSAN 113 MWm GES hedefi koymuş; resmi kayıtlarda inşaat ruhsatı "
            "henüz alınmamış ve kurulu güç 0 MWm."
        ),
        "company": "ASELSAN",
    },
    {
        "step": 3,
        "title": "Ford Otosan — Su verimliliği vs mutlak tüketim",
        "narration": (
            "Ford Otosan araç başına su tüketimini düşürdüğünü bildiriyor; "
            "İSU verileri mutlak su ayak izinin arttığını doğruluyor."
        ),
        "company": "Ford Otosan",
    },
]


def get_demo_companies():
    return [s["company"] for s in DEMO_SCRIPT]
