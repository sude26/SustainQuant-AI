import pandas as pd

# SustainaQuant AI - Ana Veri Seti (MVP)
esg_data = {
    "Sirket_Adi": [
        "Tüpraş", 
        "ASELSAN", 
        "Ford Otosan"
    ],
    "ESG_Kategorisi": [
        "Enerji Verimliliği", 
        "Yenilenebilir Enerji", 
        "Su Kullanımı"
    ],
    "Rapordaki_Iddia": [
        "2025 yılında 112 adet enerji verimliliği projesi hayata geçirilmiş; 2.448 TJ enerji tasarrufu ve 142.940 ton CO2e emisyon azaltımı sağlanmıştır.",
        "Niğde ve Şanlıurfa'da 2026 yılı sonunda devreye alınması planlanan 113 MWm kurulu güçte GES inşa edilecektir. Yıllık yaklaşık 185 milyon kWh elektrik üretimi öngörülmektedir.",
        "Üretilen araç başına temiz su kullanımı 2024 yılında 2,99 m3/araç iken 2025 yılında 2,51 m3/araç olarak azaltılmıştır."
    ],
    "Haber_Tarihi": ["Bekleniyor", "Bekleniyor", "Bekleniyor"],
    "Gerceklesen_Haber_Metni": ["Bekleniyor", "Bekleniyor", "Bekleniyor"],
    "Kaynak_URL": ["Bekleniyor", "Bekleniyor", "Bekleniyor"]
}

df = pd.DataFrame(esg_data)

# Veriyi CS arka ucu (backend) için CSV olarak dışa aktarma
csv_dosya_adi = "sustainaquant_mvp_soylem_verisi.csv"
df.to_csv(csv_dosya_adi, index=False, encoding='utf-8-sig')

print("SUSTAINQUANT AI - 3 ŞİRKETLİK MVP VERİ SETİ HAZIR!")
print(f"Veriler '{csv_dosya_adi}' olarak başarıyla kaydedildi. Arkadaşına gönderebilirsin.\n")
print(df.to_string())