"""
SustainaQuant AI – Jüri PDF Raporu
====================================
Analiz sonuçlarını jüri sunumu için PDF olarak üretir.
"""

from datetime import datetime
from html import escape
from pathlib import Path


def _setup_unicode_font(pdf):
    """Türkçe karakter desteği için sistem fontu."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            pdf.add_font("UniFont", "", path)
            pdf.set_font("UniFont", size=11)
            return True
    pdf.set_font("Helvetica", size=11)
    return False


def _ascii_safe(text: str) -> str:
    """Font bulunamazsa Türkçe karakterleri sadeleştirir."""
    replacements = {
        "ş": "s", "Ş": "S", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I",
        "ö": "o", "Ö": "O", "ü": "u", "Ü": "U", "ç": "c", "Ç": "C",
        "—": "-", "·": ".",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def build_analysis_pdf(result: dict) -> bytes:
    """Tekil analiz için PDF baytları üretir."""
    from fpdf import FPDF

    anomalies_html = ""
    for a in result.get("anomalies", []):
        title = escape(a.get("title", a.get("baslik", "")))
        desc = escape(a.get("description", a.get("aciklama", "")))
        anomalies_html += f"<li><b>{title}</b><br>{desc}</li>"

    esg = result.get("esg_breakdown", {})
    sim = result.get("similarity", {})
    sent = result.get("sentiment", {})
    entity = result.get("entity_gap", {})

    html = f"""
    <h1>SustainQuant AI - ESG Denetim Raporu</h1>
    <p><i>Teknofest Finansal Teknolojiler 2026 - Takim ID: 918431</i></p>
    <hr>
    <h2>Sirket Bilgisi</h2>
    <p><b>Sirket:</b> {escape(result.get('company_name', ''))}<br>
    <b>BIST:</b> {escape(result.get('bist_code', '—'))}<br>
    <b>Kategori:</b> {escape(result.get('category', ''))}<br>
    <b>Tarih:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
    <h2>Yesil Aklama Risk Skoru</h2>
    <p style="font-size:18px"><b>{result.get('risk_score', 0):.1f} / 100</b> -
    {escape(result.get('anomaly_status', ''))}</p>
    <h2>AI Gerekcesi</h2>
    <p>{escape(result.get('summary', ''))}</p>
    <h2>Say-Do Gap Metrikleri</h2>
    <ul>
      <li>Anlamsal Benzerlik: {sim.get('similarity', 0):.2%}</li>
      <li>Duygu Boslugu: {sent.get('sentiment_gap', 0):.2f}</li>
      <li>Entity Analizi: {escape(entity.get('summary', '—'))}</li>
      <li>E-Skor: {esg.get('environmental', '—')}</li>
      <li>S-Skor: {esg.get('social', '—')}</li>
      <li>G-Skor: {esg.get('governance', '—')}</li>
    </ul>
    <h2>Anomaliler</h2>
    <ul>{anomalies_html}</ul>
    <h2>Izleme Tetikleyicisi</h2>
    <p>{escape(result.get('trigger', ''))}</p>
    <hr>
    <p><i>Powered by Say-Do Gap - Kosinus Benzerligi - SQ-Detect</i></p>
    """

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    if not _setup_unicode_font(pdf):
        html = _ascii_safe(html)
    pdf.write_html(html)
    return bytes(pdf.output())


def build_portfolio_pdf(summary: dict) -> bytes:
    """Portföy tarama özeti PDF."""
    from fpdf import FPDF

    rows = ""
    for r in summary.get("results", []):
        rows += (
            f"<tr><td>{escape(r['company_name'])}</td>"
            f"<td>{escape(r.get('bist_code', ''))}</td>"
            f"<td>{r['risk_score']:.1f}</td>"
            f"<td>{escape(r['anomaly_status'])}</td></tr>"
        )

    html = f"""
    <h1>SustainQuant AI - Portfoy Risk Ozeti</h1>
    <p>Toplam sirket: {summary.get('total_companies', 0)} |
    Ort. risk: {summary.get('avg_risk_score', 0):.1f} |
    Yuksek risk: {summary.get('high_risk_count', 0)}</p>
    <table border="1" cellpadding="4">
      <tr><th>Sirket</th><th>BIST</th><th>Risk</th><th>Anomali</th></tr>
      {rows}
    </table>
  """
    pdf = FPDF()
    pdf.add_page()
    if not _setup_unicode_font(pdf):
        html = _ascii_safe(html)
    pdf.write_html(html)
    return bytes(pdf.output())
