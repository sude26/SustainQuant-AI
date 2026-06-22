"""
SustainaQuant AI – Data Ingestion Pipeline
============================================
Rapordaki Katman 1'in kodsal karşılığı.
CSV ve sözlük verilerini veritabanına aktarır,
veri temizleme ve normalizasyon yapar.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Windows konsol encoding düzeltmesi
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import CSV_OUTPUT_PATH
from data.database import Database
from data.esg_dataset import get_esg_dataset, validate_dataset


class DataIngestionPipeline:
    """
    Veri yükleme ve normalizasyon pipeline'ı.
    Rapordaki Data Ingestion katmanının implementasyonu.
    """

    def __init__(self, db=None):
        self.db = db or Database()

    def initialize_database(self):
        """Veritabanını oluşturur ve whitelist'i yükler."""
        print("📦 Veritabanı oluşturuluyor...")
        self.db.init()
        print("🔒 Whitelist kaynakları yükleniyor...")
        self.db.seed_whitelist()
        print("✅ Veritabanı hazır.")

    def validate_data(self):
        """Veri setinin bütünlüğünü kontrol eder."""
        print("🔍 Veri doğrulama çalıştırılıyor...")
        result = validate_dataset()
        if result["valid"]:
            print(f"✅ Veri seti geçerli. {result['record_count']} kayıt bulundu.")
        else:
            print(f"⚠️ Veri setinde {len(result['errors'])} hata bulundu:")
            for err in result["errors"]:
                print(f"   ❌ {err}")
        return result

    def load_dataset_to_db(self):
        """ESG veri setini veritabanına yükler."""
        dataset = get_esg_dataset()
        loaded = 0

        for record in dataset:
            # 1. Şirketi ekle
            company_id = self.db.insert_company(
                sirket_adi=record["sirket_adi"],
                sektor=record["sektor"],
                bist_kodu=record["bist_kodu"]
            )

            if not company_id:
                print(f"⚠️ Şirket eklenemedi: {record['sirket_adi']}")
                continue

            # 2. Söylemi ekle
            claim_id = self.db.insert_claim(
                company_id=company_id,
                esg_kategorisi=record["esg_kategorisi"],
                soylem_metni=record["soylem"],
                rapor_yili="2025"
            )

            # 3. Eylemi ekle
            self.db.insert_action(
                claim_id=claim_id,
                eylem_metni=record["eylem"],
                eylem_tarihi=record.get("eylem_tarihi"),
                kaynak=record.get("kaynak"),
                kaynak_tipi=record.get("kaynak_tipi"),
                kaynak_url=record.get("kaynak_url"),
                guvenilirlik=record.get("guvenilirlik", "Orta")
            )

            loaded += 1
            print(f"   ✅ {record['sirket_adi']} – {record['esg_kategorisi']} yüklendi.")

        print(f"\n📊 Toplam {loaded} kayıt veritabanına yüklendi.")
        return loaded

    def export_to_csv(self, output_path=None):
        """Tam entegre veri setini CSV olarak dışa aktarır."""
        output_path = output_path or str(CSV_OUTPUT_PATH)
        dataset = get_esg_dataset()

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
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"📄 CSV dışa aktarıldı: {output_path}")
        return df

    def run_full_pipeline(self):
        """Tam veri yükleme pipeline'ını çalıştırır."""
        print("=" * 60)
        print("🚀 SUSTAINQUANT AI – DATA INGESTION PIPELINE")
        print("=" * 60)
        print()

        # Adım 1: Doğrulama
        validation = self.validate_data()
        if not validation["valid"]:
            print("\n⛔ Veri doğrulama başarısız. Pipeline durduruluyor.")
            return False
        print()

        # Adım 2: Veritabanı kurulumu
        self.initialize_database()
        print()

        # Adım 3: Veri yükleme
        print("📥 Veriler veritabanına yükleniyor...")
        self.load_dataset_to_db()
        print()

        # Adım 4: CSV dışa aktarma
        print("📤 Tam entegre CSV oluşturuluyor...")
        self.export_to_csv()
        print()

        print("=" * 60)
        print("✅ DATA INGESTION PIPELINE TAMAMLANDI!")
        print("=" * 60)
        return True


if __name__ == "__main__":
    pipeline = DataIngestionPipeline()
    pipeline.run_full_pipeline()
