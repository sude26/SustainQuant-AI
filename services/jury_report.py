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


def build_score_audit_pdf(result: dict) -> bytes:
    """Uzman incelemesi için skor hesaplama denetim raporu (metodoloji + ara değerler)."""
    from fpdf import FPDF
    from config import ANOMALY_THRESHOLDS, SIMILARITY_WEIGHT, SENTIMENT_WEIGHT

    sim = result.get("similarity", {})
    sent = result.get("sentiment", {})
    comb = result.get("combined", {})
    entity = result.get("entity_gap", {}) or {}
    inputs = result.get("inputs", {})
    verification = result.get("verification") or {}
    evidence = result.get("evidence") or []

    sim_risk = comb.get("similarity_risk", sim.get("risk_score", 0))
    sent_risk = comb.get("sentiment_risk", sent.get("risk_contribution", 0))
    weighted = (SIMILARITY_WEIGHT * sim_risk) + (SENTIMENT_WEIGHT * sent_risk)
    final_score = result.get("risk_score", weighted)

    soylem_excerpt = escape((inputs.get("soylem") or "")[:900])
    eylem_excerpt = escape((inputs.get("eylem") or "")[:900])

    entity_lines = ""
    for c in entity.get("conflicts", []):
        entity_lines += f"<li><b>{escape(c.get('title', ''))}</b>: {escape(c.get('description', ''))}</li>"
    if not entity_lines:
        entity_lines = f"<li>{escape(entity.get('summary', 'Sayisal celiski tespit edilmedi.'))}</li>"

    evidence_lines = ""
    for ev in evidence[:8]:
        evidence_lines += (
            f"<li>{escape(ev.get('source', ''))} ({escape(ev.get('type', ''))}) "
            f"- {escape(ev.get('date', ''))}</li>"
        )

    threshold_lines = ""
    for key, (lo, hi) in ANOMALY_THRESHOLDS.items():
        threshold_lines += f"<li>{escape(key)}: {lo}-{hi}</li>"

    html = f"""
    <h1>Skor Denetim Raporu</h1>
    <p>SustainQuant AI - Uzman dogrulama dosyasi - Takim ID: 918431</p>
    <hr>
    <h2>1. Analiz Ozeti</h2>
    <p><b>Sirket:</b> {escape(result.get('company_name', ''))} ({escape(result.get('bist_code', ''))})<br>
    <b>Kategori:</b> {escape(result.get('category', ''))}<br>
    <b>Nihai Risk Skoru:</b> {final_score:.1f} / 100<br>
    <b>Anomali Sinifi:</b> {escape(result.get('anomaly_status', ''))}<br>
    <b>Tarih:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>

    <h2>2. Kullanilan Girdiler</h2>
    <p><b>Soylem (iddia metni):</b><br>{soylem_excerpt}</p>
    <p><b>Eylem (dogrulama metni):</b><br>{eylem_excerpt}</p>

    <h2>3. Hesaplama Formulu</h2>
    <p>Risk Skoru = (Benzerlik Riski x {SIMILARITY_WEIGHT:.0%}) + (Duygu Riski x {SENTIMENT_WEIGHT:.0%})</p>
    <p><b>Hesap:</b> ({sim_risk:.2f} x {SIMILARITY_WEIGHT}) + ({sent_risk:.2f} x {SENTIMENT_WEIGHT})
    = <b>{weighted:.1f}</b> (yuvarlanmis: {final_score:.1f})</p>

    <h2>4. Benzerlik Katmani (Agirlik %{SIMILARITY_WEIGHT * 100:.0f})</h2>
    <ul>
      <li>Kosinus benzerligi: {sim.get('similarity', 0):.4f} ({sim.get('similarity', 0):.2%})</li>
      <li>Benzerlik risk skoru: {sim_risk:.2f} / 100</li>
      <li>Yorum: Dusuk benzerlik = soylem ile eylem arasinda anlamsal uyumsuzluk</li>
    </ul>

    <h2>5. Duygu Katmani (Agirlik %{SENTIMENT_WEIGHT * 100:.0f})</h2>
    <ul>
      <li>Soylem duygu skoru: {sent.get('soylem_score', sent.get('claim_sentiment', '—'))}</li>
      <li>Eylem duygu skoru: {sent.get('eylem_score', sent.get('action_sentiment', '—'))}</li>
      <li>Duygu boslugu: {sent.get('sentiment_gap', 0):.4f}</li>
      <li>Duygu risk katkisi: {sent_risk:.2f} / 100</li>
      <li>Yorum: Soylem eylemden daha iyimser ise yesil aklama sinyali guclenir</li>
    </ul>

    <h2>6. Sayisal Iddia Analizi (Mini-NER)</h2>
    <ul>{entity_lines}</ul>

    <h2>7. Kaynak ve Kanit Zinciri</h2>
    <ul>
      <li>Coklu kaynak teyidi: {escape(verification.get('label', 'Dataset modu'))}</li>
      <li>Kaynak sayisi: {verification.get('source_count', len(evidence))}</li>
      {evidence_lines}
    </ul>

    <h2>8. Anomali Esikleri</h2>
    <ul>{threshold_lines}</ul>

    <h2>9. AI Gerekcesi (Cikti Ozeti)</h2>
    <p>{escape(result.get('summary', ''))}</p>

    <h2>10. Uzman Kontrol Listesi</h2>
    <ul>
      <li>Soylem metni dogru mu cikarildi / secildi?</li>
      <li>Eylem kaynagi bagimsiz ve guncel mi?</li>
      <li>Benzerlik ve duygu metrikleri girdilerle tutarli mi?</li>
      <li>Sayisal iddialar (%, MW, ton) celiskili mi?</li>
      <li>Nihai skor is kararina uygun mu? (Human-in-the-loop)</li>
    </ul>
    <hr>
    <p>Bu dosya otomatik uretilmistir; nihai karar analist onayina tabidir.</p>
    """

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    unicode_ok = _setup_unicode_font(pdf)
    if not unicode_ok:
        html = _ascii_safe(html)
    html = html.replace("<b>", "").replace("</b>", "")
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
