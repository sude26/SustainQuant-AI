"""
SustainaQuant AI – Jüri PDF Raporu
====================================
Analiz sonuçlarını jüri sunumu için PDF olarak üretir.
"""

from datetime import datetime
from html import escape


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

    html = f"""
    <h1>SustainQuant AI — ESG Denetim Raporu</h1>
    <p><i>Teknofest Finansal Teknolojiler 2026 · Takım ID: 918431</i></p>
    <hr>
    <h2>Şirket Bilgisi</h2>
    <p><b>Şirket:</b> {escape(result.get('company_name', ''))}<br>
    <b>BIST:</b> {escape(result.get('bist_code', '—'))}<br>
    <b>Kategori:</b> {escape(result.get('category', ''))}<br>
    <b>Tarih:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
    <h2>Yeşil Aklama Risk Skoru</h2>
    <p style="font-size:18px"><b>{result.get('risk_score', 0):.1f} / 100</b> —
    {escape(result.get('anomaly_status', ''))}</p>
    <h2>AI Gerekçesi</h2>
    <p>{escape(result.get('summary', ''))}</p>
    <h2>Say-Do Gap Metrikleri</h2>
    <ul>
      <li>Anlamsal Benzerlik: {sim.get('similarity', 0):.2%}</li>
      <li>Duygu Boşluğu: {sent.get('sentiment_gap', 0):.2f}</li>
      <li>E-Skor: {esg.get('environmental', '—')}</li>
      <li>S-Skor: {esg.get('social', '—')}</li>
      <li>G-Skor: {esg.get('governance', '—')}</li>
    </ul>
    <h2>Anomaliler</h2>
    <ul>{anomalies_html}</ul>
    <h2>İzleme Tetikleyicisi</h2>
    <p>{escape(result.get('trigger', ''))}</p>
    <hr>
    <p><i>Powered by Say-Do Gap · Kosinüs Benzerliği · SQ-Detect Lite</i></p>
    """

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
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
    <h1>SustainQuant AI — Portföy Risk Özeti</h1>
    <p>Toplam şirket: {summary.get('total_companies', 0)} |
    Ort. risk: {summary.get('avg_risk_score', 0):.1f} |
    Yüksek risk: {summary.get('high_risk_count', 0)}</p>
    <table border="1" cellpadding="4">
      <tr><th>Şirket</th><th>BIST</th><th>Risk</th><th>Anomali</th></tr>
      {rows}
    </table>
  """
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(html)
    return bytes(pdf.output())
