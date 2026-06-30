"""
SustainaQuant AI – Ana Başlatıcı
==================================
Tek komutla tüm sistemi başlatan entry point.

Kullanım:
    python run.py init       → Veritabanı kurulumu + veri yükleme
    python run.py api        → FastAPI sunucusu (uvicorn)
    python run.py dashboard  → Streamlit dashboard (website)
    python run.py web        → Dashboard kısayolu
    python run.py analyze    → Hızlı CLI analizi (3 şirketi tarar)
    python run.py demo       → Teknofest demo modu (API + Dashboard bilgisi)
"""

import sys
import os
from pathlib import Path

# Windows konsol encoding düzeltmesi
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Proje kök dizinini ekle
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"


def _use_project_venv():
    """Varsa proje sanal ortamındaki Python'u kullan (Anaconda sorunlarını önler)."""
    if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])


_use_project_venv()


def cmd_init():
    """Veritabanı kurulumu ve veri yükleme."""
    from data.ingestion import DataIngestionPipeline
    pipeline = DataIngestionPipeline()
    pipeline.run_full_pipeline()


def cmd_analyze():
    """Tüm şirketleri hızlıca analiz eder (CLI)."""
    print("=" * 60)
    print("🧠 SUSTAINQUANT AI – HIZLI ANALİZ (CLI)")
    print("=" * 60)
    print()

    from nlp.analyzer import GreenwashingAnalyzer
    analyzer = GreenwashingAnalyzer()

    print("📥 NLP modelleri yükleniyor...")
    analyzer.nlp.warmup()
    print()

    # Tüm şirketleri analiz et
    summary = analyzer.get_portfolio_summary()

    print("=" * 60)
    print(f"📊 PORTFÖY ÖZETİ")
    print(f"   Toplam Şirket: {summary['total_companies']}")
    print(f"   Ortalama Risk: {summary['avg_risk_score']:.1f}/100")
    print(f"   Yüksek Risk: {summary['high_risk_count']} şirket")
    print("=" * 60)
    print()

    for result in summary["results"]:
        print(result["formatted_report"])
        print()
        print("-" * 60)
        print()


def cmd_api():
    """FastAPI sunucusunu başlatır."""
    import uvicorn
    from config import API_HOST, API_PORT

    print(f"🌐 API başlatılıyor: http://{API_HOST}:{API_PORT}")
    print(f"📖 Swagger Docs: http://localhost:{API_PORT}/docs")
    print()

    uvicorn.run(
        "api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="info",
    )


def cmd_setup():
    """Sanal ortam oluşturur ve bağımlılıkları kurar."""
    import subprocess
    import shutil

    if not VENV_PYTHON.exists():
        print("📦 Sanal ortam oluşturuluyor (.venv)...")
        py = shutil.which("python3") or sys.executable
        subprocess.run([py, "-m", "venv", str(PROJECT_ROOT / ".venv")], check=True)

    print("📥 Bağımlılıklar kuruluyor (birkaç dakika sürebilir)...")
    subprocess.run(
        [str(VENV_PYTHON), "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=str(PROJECT_ROOT),
        check=True,
    )
    print("✅ Kurulum tamam! Şimdi çalıştırın: python run.py web")


def cmd_download_models():
    """
    Tam NLP modelleri — YALNIZCA isteğe bağlı.
    Demo için gerekmez; lightweight mod zaten çalışır.
    """
    if "--full" not in sys.argv:
        print("=" * 60)
        print("ℹ️  BU KOMUTA GEREK YOK — Demo için Lite mod yeterli")
        print("=" * 60)
        print()
        print("Siteyi açmak için şunu çalıştırın:")
        print()
        print("    python run.py web")
        print()
        print("Sonra tarayıcıda:  http://localhost:8501")
        print()
        print("Tam FinBERT modellerini indirmek istiyorsanız (isteğe bağlı):")
        print("    python run.py models --full")
        print()
        return

    from nlp.models import SustainaQuantNLP

    print("🧠 Tam NLP modelleri indiriliyor… (2-10 dk, stabil internet gerekir)")
    print("   Takılırsa Ctrl+C — Lite mod zaten çalışıyor.")
    nlp = SustainaQuantNLP()
    ok = nlp.warmup()
    if ok:
        print("✅ Tam modeller hazır.")
        print("   config.py içinde NLP_MODE = 'full' yapın.")
    else:
        print("⚠️ İndirme tamamlanamadı. Lite mod kullanın: python run.py web")


DASHBOARD_PORT = 8501


def _port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def cmd_stop():
    """Arka planda kalan Streamlit sürecini durdurur."""
    import subprocess
    import time

    print("🛑 Eski dashboard süreci kapatılıyor...")
    subprocess.run(["pkill", "-f", "streamlit run app.py"], check=False)
    time.sleep(1)
    if _port_in_use(DASHBOARD_PORT):
        print(f"⚠️  Port {DASHBOARD_PORT} hâlâ dolu. Bilgisayarı yeniden başlatmayı deneyin.")
    else:
        print(f"✅ Port {DASHBOARD_PORT} serbest. Şimdi: python run.py web")


def cmd_dashboard():
    """Streamlit dashboard'unu başlatır."""
    import subprocess
    import os
    from config import NLP_MODE

    if _port_in_use(DASHBOARD_PORT):
        print("⚠️  Port 8501 zaten kullanımda — dashboard muhtemelen ZATEN AÇIK.")
        print("   Tarayıcıda dene:  http://localhost:8501")
        print("   Yeniden başlatmak için:")
        print("       python run.py stop")
        print("       python run.py web")
        return

    print("📊 Dashboard başlatılıyor...")
    print("   URL: http://localhost:8501")
    if NLP_MODE == "lightweight":
        print("   Mod: Lite (internet gerekmez, hemen açılır)")
    else:
        print("   Mod: Full FinBERT")
    print("   (Terminal açık kalsın — kapatırsan site kapanır)")
    print()
    
    env = os.environ.copy()
    env["STREAMLIT_EMAIL"] = ""
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", str(DASHBOARD_PORT),
        "--browser.gatherUsageStats", "false",
        "--server.headless", "true",
        "--server.address", "localhost",
    ], cwd=str(PROJECT_ROOT), env=env)


def cmd_all():
    """API + Dashboard birlikte başlatır (Faz C tam stack)."""
    import subprocess
    import os
    import time
    from config import API_PORT

    print("=" * 60)
    print("🚀 SUSTAINQUANT AI — TAM STACK (API + Dashboard)")
    print("=" * 60)
    print(f"   API:       http://localhost:{API_PORT}")
    print(f"   Dashboard: http://localhost:8501")
    print(f"   WebSocket: ws://localhost:{API_PORT}/api/v1/ws/alerts")
    print()

    api_proc = subprocess.Popen(
        [str(VENV_PYTHON if VENV_PYTHON.exists() else sys.executable),
         str(PROJECT_ROOT / "run.py"), "api"],
        cwd=str(PROJECT_ROOT),
    )
    time.sleep(2)

    env = os.environ.copy()
    env["STREAMLIT_EMAIL"] = ""
    env["SQ_USE_API"] = "true"
    try:
        subprocess.run([
            str(VENV_PYTHON if VENV_PYTHON.exists() else sys.executable),
            "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false",
            "--server.headless", "true",
            "--server.address", "localhost",
        ], cwd=str(PROJECT_ROOT), env=env)
    finally:
        api_proc.terminate()
        api_proc.wait(timeout=5)


def cmd_demo():
    """Teknofest demo bilgilerini gösterir."""
    from config import MASTER_SYSTEM_PROMPT

    print("=" * 60)
    print("🏆 SUSTAINQUANT AI – TEKNOFEST DEMO MODU")
    print("=" * 60)
    print()
    print("📋 Proje: Yatırım Portföyleri İçin NLP Tabanlı ESG Risk")
    print("         ve Yeşil Aklama (Greenwashing) Tespit Motoru")
    print()
    print("👥 Takım: SUSTAINQUANT AI | ID: 918431")
    print("📝 Başvuru ID: 4896395")
    print()
    print("─" * 60)
    print()
    print("🔧 SİSTEMİ BAŞLATMAK İÇİN:")
    print()
    print("  1. Veritabanını kur:     python run.py init")
    print("  2. Analiz yap (CLI):     python run.py analyze")
    print("  3. API başlat:           python run.py api")
    print("  4. Dashboard başlat:     python run.py dashboard")
    print()
    print("─" * 60)
    print()
    print("🧠 MASTER SYSTEM PROMPT:")
    print(MASTER_SYSTEM_PROMPT)
    print()
    print("─" * 60)
    print()
    print("💼 İŞ MODELİ:")
    print("  • B2B SaaS Abonelik:  $450/ay (Premium Dashboard)")
    print("  • DaaS API:           $0.02/sorgu (Pay-as-you-go)")
    print()
    print("🎯 HEDEF KİTLE:")
    print("  • Portföy Yönetim Şirketleri")
    print("  • ESG Yatırım Fonları")
    print("  • Yatırım Bankaları (Garanti BBVA vb.)")
    print()
    print("=" * 60)


def main():
    """Ana giriş noktası."""
    if len(sys.argv) < 2:
        print("SustainaQuant AI – Kullanım:")
        print()
        print("  python run.py init       Veritabanı kurulumu")
        print("  python run.py analyze    CLI analizi")
        print("  python run.py api        FastAPI sunucusu")
        print("  python run.py setup      İlk kurulum (bir kez)")
        print("  python run.py web        ★ Websiteyi aç (bunu kullanın)")
        print("  python run.py stop       Dashboard'u kapat (port 8501)")
        print("  python run.py all        ★ API + Dashboard birlikte")
        print("  python run.py models     Bilgi (indirme yapmaz)")
        print("  python run.py demo       Demo bilgileri")
        sys.exit(1)

    command = sys.argv[1].lower()

    commands = {
        "init": cmd_init,
        "setup": cmd_setup,
        "models": cmd_download_models,
        "download-models": cmd_download_models,
        "analyze": cmd_analyze,
        "api": cmd_api,
        "dashboard": cmd_dashboard,
        "web": cmd_dashboard,
        "stop": cmd_stop,
        "all": cmd_all,
        "demo": cmd_demo,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"❌ Bilinmeyen komut: {command}")
        print(f"   Geçerli komutlar: {', '.join(commands.keys())}")
        sys.exit(1)


if __name__ == "__main__":
    main()
