"""
SustainaQuant AI – SQLite Veritabanı Yönetimi
===============================================
MVP için hafif ve taşınabilir veritabanı katmanı.
Whitelist kaynak filtresi dahil (Rapor §6 – Risk Önlemi).
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_PATH, SOURCE_WHITELIST


class Database:
    """SQLite veritabanı yönetim sınıfı."""

    def __init__(self, db_path=None):
        self.db_path = db_path or str(DB_PATH)

    def _get_connection(self):
        """Veritabanı bağlantısı oluşturur."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init(self):
        """Veritabanı tablolarını oluşturur."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Şirketler tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sirket_adi TEXT NOT NULL UNIQUE,
                sektor TEXT,
                bist_kodu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Söylem verileri (rapordaki iddialar)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS esg_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                esg_kategorisi TEXT NOT NULL,
                soylem_metni TEXT NOT NULL,
                rapor_yili TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)

        # Eylem verileri (bağımsız kaynak bulguları)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS esg_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id INTEGER NOT NULL,
                eylem_metni TEXT NOT NULL,
                eylem_tarihi TEXT,
                kaynak TEXT,
                kaynak_tipi TEXT,
                kaynak_url TEXT,
                guvenilirlik TEXT DEFAULT 'Orta',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (claim_id) REFERENCES esg_claims(id)
            )
        """)

        # Analiz sonuçları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id INTEGER NOT NULL,
                action_id INTEGER NOT NULL,
                risk_skoru REAL NOT NULL,
                anomali_durumu TEXT NOT NULL,
                similarity_skoru REAL,
                sentiment_soylem REAL,
                sentiment_eylem REAL,
                ozet_gerekce TEXT,
                tetikleyici TEXT,
                guven_araligi REAL,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (claim_id) REFERENCES esg_claims(id),
                FOREIGN KEY (action_id) REFERENCES esg_actions(id)
            )
        """)

        # Güvenilir kaynak whitelist'i
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kaynak_adi TEXT NOT NULL UNIQUE,
                aktif INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # API kullanım takibi (DaaS faturalandırma için)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                request_count INTEGER DEFAULT 1,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        return True

    def seed_whitelist(self):
        """Whitelist kaynaklarını veritabanına yükler."""
        conn = self._get_connection()
        cursor = conn.cursor()
        for source in SOURCE_WHITELIST:
            cursor.execute(
                "INSERT OR IGNORE INTO source_whitelist (kaynak_adi) VALUES (?)",
                (source,)
            )
        conn.commit()
        conn.close()

    # ── Şirket CRUD ──────────────────────────────────────────

    def insert_company(self, sirket_adi, sektor=None, bist_kodu=None):
        """Yeni şirket ekler, varsa ID'sini döndürür."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO companies (sirket_adi, sektor, bist_kodu) VALUES (?, ?, ?)",
            (sirket_adi, sektor, bist_kodu)
        )
        conn.commit()
        # ID'yi al
        cursor.execute("SELECT id FROM companies WHERE sirket_adi = ?", (sirket_adi,))
        row = cursor.fetchone()
        conn.close()
        return row["id"] if row else None

    def get_companies(self):
        """Tüm şirketleri döndürür."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM companies ORDER BY sirket_adi")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_company_by_name(self, sirket_adi):
        """İsme göre şirket arar."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE sirket_adi = ?", (sirket_adi,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ── Söylem (Claim) CRUD ──────────────────────────────────

    def insert_claim(self, company_id, esg_kategorisi, soylem_metni, rapor_yili=None):
        """Yeni söylem kaydı ekler."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO esg_claims (company_id, esg_kategorisi, soylem_metni, rapor_yili) 
               VALUES (?, ?, ?, ?)""",
            (company_id, esg_kategorisi, soylem_metni, rapor_yili)
        )
        conn.commit()
        claim_id = cursor.lastrowid
        conn.close()
        return claim_id

    def get_claims_by_company(self, company_id):
        """Şirkete ait tüm söylemleri döndürür."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM esg_claims WHERE company_id = ?", (company_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ── Eylem (Action) CRUD ──────────────────────────────────

    def insert_action(self, claim_id, eylem_metni, eylem_tarihi=None,
                      kaynak=None, kaynak_tipi=None, kaynak_url=None, guvenilirlik="Orta"):
        """Yeni eylem kaydı ekler."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO esg_actions 
               (claim_id, eylem_metni, eylem_tarihi, kaynak, kaynak_tipi, kaynak_url, guvenilirlik) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (claim_id, eylem_metni, eylem_tarihi, kaynak, kaynak_tipi, kaynak_url, guvenilirlik)
        )
        conn.commit()
        action_id = cursor.lastrowid
        conn.close()
        return action_id

    def get_actions_by_claim(self, claim_id):
        """Söyleme ait tüm eylemleri döndürür."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM esg_actions WHERE claim_id = ?", (claim_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ── Analiz Sonuçları CRUD ────────────────────────────────

    def insert_analysis_result(self, claim_id, action_id, risk_skoru, anomali_durumu,
                                similarity_skoru=None, sentiment_soylem=None,
                                sentiment_eylem=None, ozet_gerekce=None,
                                tetikleyici=None, guven_araligi=None):
        """Analiz sonucunu kaydeder."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO analysis_results 
               (claim_id, action_id, risk_skoru, anomali_durumu, similarity_skoru,
                sentiment_soylem, sentiment_eylem, ozet_gerekce, tetikleyici, guven_araligi) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (claim_id, action_id, risk_skoru, anomali_durumu, similarity_skoru,
             sentiment_soylem, sentiment_eylem, ozet_gerekce, tetikleyici, guven_araligi)
        )
        conn.commit()
        result_id = cursor.lastrowid
        conn.close()
        return result_id

    def get_latest_results(self):
        """En son analiz sonuçlarını şirket bilgileriyle birlikte döndürür."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ar.*,
                c.sirket_adi,
                c.bist_kodu,
                ec.esg_kategorisi,
                ec.soylem_metni,
                ea.eylem_metni,
                ea.kaynak
            FROM analysis_results ar
            JOIN esg_claims ec ON ar.claim_id = ec.id
            JOIN esg_actions ea ON ar.action_id = ea.id
            JOIN companies c ON ec.company_id = c.id
            ORDER BY ar.analyzed_at DESC
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_results_by_company(self, sirket_adi):
        """Belirli bir şirketin analiz sonuçlarını döndürür."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ar.*,
                c.sirket_adi,
                c.bist_kodu,
                ec.esg_kategorisi,
                ec.soylem_metni,
                ea.eylem_metni,
                ea.kaynak
            FROM analysis_results ar
            JOIN esg_claims ec ON ar.claim_id = ec.id
            JOIN esg_actions ea ON ar.action_id = ea.id
            JOIN companies c ON ec.company_id = c.id
            WHERE c.sirket_adi = ?
            ORDER BY ar.analyzed_at DESC
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ── API Kullanım Takibi ──────────────────────────────────

    def log_api_usage(self, api_key, endpoint):
        """API kullanımını kaydeder (DaaS faturalandırma için)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO api_usage (api_key, endpoint) VALUES (?, ?)",
            (api_key, endpoint)
        )
        conn.commit()
        conn.close()

    def get_api_usage_count(self, api_key):
        """API anahtarının toplam kullanım sayısını döndürür."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as total FROM api_usage WHERE api_key = ?",
            (api_key,)
        )
        row = cursor.fetchone()
        conn.close()
        return row["total"] if row else 0

    # ── Whitelist Kontrolü ───────────────────────────────────

    def is_source_whitelisted(self, kaynak_adi):
        """Kaynağın whitelist'te olup olmadığını kontrol eder."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM source_whitelist WHERE kaynak_adi LIKE ? AND aktif = 1",
            (f"%{kaynak_adi}%",)
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None
