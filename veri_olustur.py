"""
SustainaQuant AI – Tam Entegre Veri Seti Üretici (Güncellenmiş)
================================================================
Orijinal veri_olustur.py'nin genişletilmiş versiyonu.
Artık hem söylem hem eylem verilerini içeren tam CSV üretir.
"""

import pandas as pd
import sys
from pathlib import Path

# Proje kök dizinini ekle
sys.path.insert(0, str(Path(__file__).resolve().parent))

from data.esg_dataset import get_esg_dataset


def main():
    print("=" * 60)
    print("🚀 SUSTAINQUANT AI – TAM ENTEGRE VERİ SETİ ÜRETİCİ")
    print("=" * 60)
    print()

    # Genişletilmiş veri setini al
    dataset = get_esg_dataset()

    # DataFrame oluştur
    rows = []
    for record in dataset:
        rows.append({
            "Sirket_Adi": record["sirket_adi"],
            "BIST_Kodu": record["bist_kodu"],
            "Sektor": record["sektor"],
            "ESG_Kategorisi": record["esg_kategorisi"],
            "Rapordaki_Iddia": record["soylem"],
            "Gerceklesen_Eylem": record["eylem"],
            "Eylem_Tarihi": record.get("eylem_tarihi", ""),
            "Kaynak": record.get("kaynak", ""),
            "Kaynak_Tipi": record.get("kaynak_tipi", ""),
            "Kaynak_URL": record.get("kaynak_url", ""),
            "Guvenilirlik": record.get("guvenilirlik", ""),
        })

    df = pd.DataFrame(rows)

    # Tam entegre CSV olarak kaydet
    csv_dosya_adi = "sustainaquant_mvp_gercek_veri.csv"
    df.to_csv(csv_dosya_adi, index=False, encoding="utf-8-sig")

    print(f"✅ SUSTAINQUANT AI - {len(dataset)} ŞİRKETLİK TAM ENTEGRE VERİ SETİ HAZIR!")
    print(f"📄 Veriler '{csv_dosya_adi}' olarak kaydedildi.")
    print()
    print("📊 Veri Seti Özeti:")
    print(f"   Şirket Sayısı: {len(set(r['sirket_adi'] for r in dataset))}")
    print(f"   Kayıt Sayısı: {len(dataset)}")
    print(f"   Sütun Sayısı: {len(df.columns)}")
    print()

    # Tabloyu göster
    print(df[["Sirket_Adi", "ESG_Kategorisi", "Kaynak_Tipi"]].to_string(index=False))
    print()

    # Eski format CSV'yi de güncelle (geriye uyumluluk)
    eski_csv = "sustainaquant_mvp_soylem_verisi.csv"
    eski_df = df[["Sirket_Adi", "ESG_Kategorisi", "Rapordaki_Iddia",
                   "Eylem_Tarihi", "Gerceklesen_Eylem", "Kaynak_URL"]]
    eski_df.columns = ["Sirket_Adi", "ESG_Kategorisi", "Rapordaki_Iddia",
                        "Haber_Tarihi", "Gerceklesen_Haber_Metni", "Kaynak_URL"]
    eski_df.to_csv(eski_csv, index=False, encoding="utf-8-sig")
    print(f"📄 Eski format da güncellendi: '{eski_csv}'")


if __name__ == "__main__":
    main()