"""
SustainaQuant AI – ESG Risk Terminali (Streamlit Dashboard)
=============================================================
B2B Finans Terminali arayüzü + gerçek NLP motoru entegrasyonu.
Rapordaki Katman 3 – Sunum katmanının implementasyonu.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as sq_config

from config import (
    DASHBOARD_PAGE_TITLE,
    DASHBOARD_LAYOUT,
    LOGO_PATH,
    SOURCE_WHITELIST,
    API_BASE_URL,
    WS_ALERTS_URL,
    USE_API_BACKEND,
)
NLP_MODE = getattr(sq_config, "NLP_MODE", "lightweight")
from data.esg_dataset import get_esg_dataset, get_companies, get_company_data
from data.pdf_extractor import (
    detect_company_from_pdf,
    extract_esg_claims,
    extract_text_from_pdf,
)
from data.demo_scenario import DEMO_SCRIPT
from services.jury_report import build_analysis_pdf, build_portfolio_pdf
from services.live_verification import fetch_live_context, build_enriched_record
from services.alert_bus import get_recent_alerts
from services.api_client import get_api_client
from services.news_scanner import scan_portfolio_news
from nlp.analyzer import GreenwashingAnalyzer

# ──────────────────────────────────────────────────────────────
# SAYFA KONFİGÜRASYONU
# ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="SustainQuant AI · ESG Denetim Motoru",
    page_icon="📊",
    layout=DASHBOARD_LAYOUT,
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# B2B FİNANS TERMİNALİ CSS (IBM Plex)
# ──────────────────────────────────────────────────────────────

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
html, body, [data-testid="stApp"] {
    background-color: #08111E !important;
    color: #E8EEF4 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
[data-testid="stSidebar"] {
    background-color: #0B1626 !important;
    border-right: 1px solid #16273B !important;
}
[data-testid="stSidebar"] * { color: #8AA0B4 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label {
    color: #5C7185 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: .14em !important;
}
.stButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #14E08A, #0DAE69) !important;
    color: #06231A !important;
    border: none !important;
    border-radius: 9px !important;
    padding: 14px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: .1em !important;
    box-shadow: 0 6px 22px rgba(20,224,138,0.22) !important;
    transition: all .15s !important;
}
.stButton > button:hover {
    filter: brightness(1.08) !important;
    transform: translateY(-1px) !important;
}
.stTextArea textarea, .stTextInput input {
    background-color: #0A1424 !important;
    border: 1px solid #1B2E44 !important;
    border-radius: 9px !important;
    color: #E8EEF4 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 13.5px !important;
    line-height: 1.55 !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #14E08A !important;
    box-shadow: 0 0 0 3px rgba(20,224,138,0.12) !important;
}
.stSelectbox div[data-baseweb="select"] > div {
    background-color: #0A1424 !important;
    border: 1px solid #1B2E44 !important;
    border-radius: 9px !important;
    color: #E8EEF4 !important;
}
[data-testid="stMetric"] {
    background: #0E1C2E !important;
    border: 1px solid #1B2E44 !important;
    border-radius: 12px !important;
    padding: 18px 20px !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: .14em !important;
    color: #5C7185 !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    color: #14E08A !important;
}
.sq-card {
    background: #0E1C2E;
    border: 1px solid #1B2E44;
    border-radius: 12px;
    padding: 22px 24px;
    margin-bottom: 16px;
}
.sq-card-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: .16em;
    color: #5C7185;
    margin-bottom: 14px;
    text-transform: uppercase;
}
.sq-band {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    border-radius: 8px;
    padding: 8px 14px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: .08em;
}
.sq-band-high   { color:#FF5C5C; background:rgba(255,92,92,0.12); border:1px solid #FF5C5C; }
.sq-band-medium { color:#FFB23E; background:rgba(255,178,62,0.12); border:1px solid #FFB23E; }
.sq-band-low    { color:#14E08A; background:rgba(20,224,138,0.12); border:1px solid #14E08A; }
.sq-anomaly {
    background: #0A1424;
    border: 1px solid #1B2E44;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border-left: 3px solid #FF5C5C;
}
.sq-anomaly-med { border-left-color: #FFB23E !important; }
.sq-anomaly-low { border-left-color: #14E08A !important; }
.report-output {
    background: #0A1424;
    border: 1px solid #1B2E44;
    border-radius: 10px;
    padding: 20px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    line-height: 1.7;
    white-space: pre-wrap;
    color: #14E08A;
}
@keyframes sq-pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.sq-live-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #14E08A;
    box-shadow: 0 0 8px #14E08A;
    animation: sq-pulse 2s infinite;
    vertical-align: middle;
    margin-right: 6px;
}
::-webkit-scrollbar { width: 8px }
::-webkit-scrollbar-track { background: #0A1424 }
::-webkit-scrollbar-thumb { background: #1E3349; border-radius: 6px }
#MainMenu, footer, header { visibility: hidden !important; }
.block-container { padding-top: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ──────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="NLP modelleri yükleniyor… (ilk seferde 1-2 dk sürebilir)")
def load_analyzer():
    """NLP analyzer'ı yükler ve cache'ler."""
    analyzer = GreenwashingAnalyzer()
    try:
        analyzer.nlp.warmup()
    except Exception as e:
        print(f"Model yükleme uyarısı: {e}")
    return analyzer


def risk_to_band(risk_score: float) -> str:
    if risk_score > 50:
        return "YÜKSEK"
    if risk_score > 25:
        return "ORTA"
    return "DÜŞÜK"


def band_style(band: str) -> tuple[str, str, str]:
    if band == "YÜKSEK":
        return "sq-band-high", "#FF5C5C", "high"
    if band == "ORTA":
        return "sq-band-medium", "#FFB23E", "med"
    return "sq-band-low", "#14E08A", "low"


def score_bar_color(value: float) -> str:
    return "#FF5C5C" if value < 45 else ("#FFB23E" if value < 65 else "#14E08A")


def risk_score_color(score: float) -> str:
    if score > 50:
        return "#FF5C5C"
    if score > 25:
        return "#FFB23E"
    return "#14E08A"


def derive_esg_scores(result: dict) -> dict:
    """Backend E/S/G kırılımını UI formatına çevirir."""
    esg = result.get("esg_breakdown", {})
    return {
        "e": esg.get("environmental", 0),
        "s": esg.get("social", 0),
        "g": esg.get("governance", 0),
    }


def derive_anomalies(result: dict) -> list:
    """Backend anomali listesini UI formatına çevirir."""
    items = []
    for a in result.get("anomalies", []):
        items.append({
            "baslik": a.get("title", a.get("baslik", "")),
            "aciklama": a.get("description", a.get("aciklama", "")),
            "seviye": a.get("severity", a.get("seviye", "med")),
        })
    return items


def company_watchlist_items(summary: dict) -> list:
    """Şirket bazında en yüksek risk skorunu döndürür."""
    by_company = {}
    for r in summary["results"]:
        name = r["company_name"]
        if name not in by_company or r["risk_score"] > by_company[name]["risk_score"]:
            by_company[name] = r
    return sorted(by_company.values(), key=lambda x: x["risk_score"], reverse=True)


def render_html(html: str):
    """HTML'i kod bloğu olarak değil, gerçek UI olarak render eder."""
    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)


def render_watchlist_panel(items: list, pending: bool = False):
    """İzleme listesi — native Streamlit (HTML kod bloğu sorunu yok)."""
    st.markdown(
        '<p style="font-family:IBM Plex Mono,monospace;font-size:10px;'
        'letter-spacing:.16em;color:#5C7185;margin-bottom:10px">İZLEME LİSTESİ</p>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        for r in items:
            left, right = st.columns([4, 1])
            with left:
                st.markdown(f"**{r['bist_code']}**")
                st.caption(r["company_name"])
            with right:
                score = r.get("risk_score")
                label = f"{score:.0f}" if score is not None else "—"
                color = risk_score_color(score) if score is not None else "#5C7185"
                st.markdown(
                    f'<p style="text-align:right;font-family:IBM Plex Mono,monospace;'
                    f'font-weight:700;color:{color};margin:8px 0 0">{label}</p>',
                    unsafe_allow_html=True,
                )
        if pending:
            st.caption("Skorlar için alttaki butona basın.")


def render_anomalies_panel(anomaliler: list):
    """Anomali kartları — HTML kod bloğu sorunu yok."""
    st.markdown(
        '<p style="font-family:IBM Plex Mono,monospace;font-size:10px;'
        'letter-spacing:.16em;color:#5C7185;margin-bottom:10px">ANOMALİLER</p>',
        unsafe_allow_html=True,
    )
    icons = {"high": "🔴", "med": "🟠", "low": "🟢"}
    with st.container(border=True):
        for a in anomaliler:
            icon = icons.get(a.get("seviye", a.get("severity", "med")), "🟠")
            title = a.get("baslik", a.get("title", ""))
            desc = a.get("aciklama", a.get("description", ""))
            st.markdown(f"**{icon} {title}**")
            st.caption(desc)


def placeholder_watchlist() -> list:
    return [{
        "bist_code": c["bist_kodu"],
        "company_name": c["sirket_adi"],
        "risk_score": None,
    } for c in get_companies()]


def sync_text_inputs(ctx_key: str, soylem: str, eylem: str):
    """Şirket/mod değişince metin alanlarını günceller (Streamlit key/value bug fix)."""
    if st.session_state.get("_text_ctx") != ctx_key:
        st.session_state["_text_ctx"] = ctx_key
        st.session_state["sq_soylem"] = soylem
        st.session_state["sq_eylem"] = eylem


def sync_pdf_inputs(file_ctx: str | None, company_ctx: str, soylem: str | None, eylem: str):
    """PDF modunda söylem/eylem alanlarını session state ile senkronize eder."""
    if file_ctx and st.session_state.get("_pdf_file_ctx") != file_ctx:
        st.session_state["_pdf_file_ctx"] = file_ctx
        st.session_state["pdf_soylem"] = soylem or ""
    if st.session_state.get("_pdf_company_ctx") != company_ctx:
        st.session_state["_pdf_company_ctx"] = company_ctx
        st.session_state["pdf_eylem"] = eylem


def resolve_pdf_eylem(record: dict | None) -> tuple[str, str]:
    """Seçili şirket için doğrulama (eylem) metnini dataset + canlı kaynaktan üretir."""
    if not record:
        return "", ""
    eylem = record.get("eylem", "")
    source_label = f"{record.get('kaynak', 'Dataset')} · {record.get('eylem_tarihi', '')}"
    if record.get("bist_kodu"):
        try:
            from services.live_verification import fetch_live_context
            live = fetch_live_context(
                company_name=record["sirket_adi"],
                bist_code=record["bist_kodu"],
                category=record.get("esg_kategorisi", ""),
                dataset_eylem=eylem,
                include_kap=True,
                include_news=True,
            )
            if live.get("merged_eylem"):
                eylem = live["merged_eylem"]
                verification = live.get("verification") or {}
                src_count = verification.get("source_count", 0)
                source_label = f"Dataset + KAP/haber · {src_count} kaynak"
        except Exception:
            pass
    return eylem, source_label


def render_jury_presenter_notes():
    """Sunum notları — sidebar'da, jüri ekranında görünmez."""
    from data.demo_scenario import DEMO_INTRO, DEMO_SCRIPT

    with st.expander("📝 Sunum notları (sadece prova)"):
        st.caption("Bu bölüm ekran paylaşımında jüriye gösterilmez; prova için.")
        st.markdown(f"**Giriş:** {DEMO_INTRO}")
        for step in DEMO_SCRIPT:
            line = step.get("jury_line", step["narration"])
            st.markdown(f"**Adım {step['step']} — {step['company']}:** {line}")


def run_company_analysis(analyzer, mode: str, record, soylem: str, eylem: str,
                         default_company: str, default_category: str) -> dict:
    """Analiz çalıştırır ve sonucu session state'e yazar."""
    if mode == "Kayıtlı Şirket" and record:
        analysis_record = {**record, "soylem": soylem, "eylem": eylem}
        result = analyzer.analyze_record(analysis_record)
    else:
        result = analyzer.analyze_custom(
            company_name=default_company,
            category=default_category,
            soylem=soylem,
            eylem=eylem,
        )
    st.session_state["analysis_result"] = result
    st.session_state["analysis_pending"] = False
    try:
        from services.alert_bus import alert_from_analysis
        alert_from_analysis(result)
    except Exception:
        pass
    return result


def render_alerts_sidebar():
    """Canlı anomali alarm paneli (Faz C)."""
    st.markdown(
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;'
        'letter-spacing:.14em;color:#5C7185;margin:16px 0 8px">CANLI ALARMLAR · WS</div>',
        unsafe_allow_html=True,
    )
    use_api = st.session_state.get("use_api_backend", USE_API_BACKEND)
    alerts = []
    if use_api:
        try:
            alerts = get_api_client().recent_alerts(6)
        except Exception:
            alerts = get_recent_alerts(6)
    else:
        alerts = get_recent_alerts(6)

    with st.container(border=True):
        if not alerts:
            st.caption("Alarm yok. Analiz veya haber taraması çalıştırın.")
        for a in alerts[:6]:
            sev = a.get("severity", "med")
            icon = "🔴" if sev == "high" else ("🟠" if sev == "med" else "🟢")
            title = a.get("title", "")[:50]
            st.markdown(f"{icon} **{title}**")
            msg = a.get("message", "")[:70]
            if msg:
                st.caption(msg)

    if st.button("📡  Haberleri Tara", key="btn_scan_news", use_container_width=True):
        with st.spinner("15 şirket taranıyor…"):
            if use_api:
                try:
                    r = get_api_client().scan_news()
                    st.toast(f"{r.get('new_alerts', 0)} yeni alarm", icon="📡")
                except Exception:
                    r = scan_portfolio_news()
                    st.toast(f"{r.get('new_alerts', 0)} yeni alarm (yerel)", icon="📡")
            else:
                r = scan_portfolio_news()
                st.toast(f"{r.get('new_alerts', 0)} yeni alarm", icon="📡")
        st.rerun()

    st.caption(f"WS: {WS_ALERTS_URL}")


def render_demo_score_reveal(result: dict, step: dict):
    """Jüri sunumu için büyük risk skoru kartı."""
    risk = result["risk_score"]
    band = risk_to_band(risk)
    _, band_color, _ = band_style(band)
    ticker = result.get("bist_code") or step.get("bist_code", "")
    render_html(f"""
    <div style="background:linear-gradient(135deg,#0E1C2E,#16293D);border:2px solid {band_color};
                border-radius:16px;padding:28px 32px;margin:16px 0;text-align:center">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.2em;color:#5C7185">
        ADIM {step['step']} · {ticker}
      </div>
      <div style="font-size:22px;font-weight:700;color:#E8EEF4;margin:12px 0">{result['company_name']}</div>
      <div style="font-family:'IBM Plex Mono',monospace;font-size:56px;font-weight:700;color:{band_color};
                  line-height:1;margin:16px 0">{risk:.0f}</div>
      <div style="font-size:13px;color:#8AA0B4;margin-bottom:8px">YEŞİL AKLAMA RİSK SKORU / 100</div>
      <div class="sq-band {'sq-band-high' if band=='YÜKSEK' else ('sq-band-medium' if band=='ORTA' else 'sq-band-low')}"
           style="display:inline-flex">{band} RİSK · {result['anomaly_status']}</div>
      <div style="font-size:13px;color:#CFE0EC;margin-top:18px;line-height:1.6">{step.get('hook','')}</div>
    </div>
    """)


def render_jury_demo():
    """Geliştirilmiş jüri sunum modu."""
    from data.demo_scenario import DEMO_SCRIPT, DEMO_INTRO

    st.markdown('<div class="sq-card-label">JÜRİ SUNUM MODU · 30 SANİYE CANLI DEMO</div>', unsafe_allow_html=True)

    if "demo_step" not in st.session_state:
        st.session_state.demo_step = 0
    if "demo_results" not in st.session_state:
        st.session_state.demo_results = []
    if "demo_playing" not in st.session_state:
        st.session_state.demo_playing = False

    total_steps = len(DEMO_SCRIPT)
    progress = st.session_state.demo_step / total_steps if total_steps else 0
    st.progress(progress, text=f"Sunum ilerlemesi · {st.session_state.demo_step}/{total_steps} adım")

    render_html(f"""
    <div style="background:#0A1424;border:1px solid #1B2E44;border-radius:12px;padding:18px 22px;margin-bottom:20px">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.16em;color:#14E08A;margin-bottom:8px">
        SAY-DO GAP · CANLI DEMO
      </div>
      <p style="font-size:14px;line-height:1.65;color:#CFE0EC;margin:0">{DEMO_INTRO}</p>
    </div>
    """)

    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        if st.button("▸  SUNUMU BAŞLAT", type="primary", use_container_width=True, key="demo_start"):
            st.session_state.demo_step = 0
            st.session_state.demo_results = []
            st.session_state.demo_playing = True
            st.rerun()
    with bc2:
        if st.button("▸  SONRAKİ VAKA", use_container_width=True, key="demo_next",
                     disabled=not st.session_state.demo_results):
            if st.session_state.demo_step < total_steps:
                st.session_state.demo_step += 1
            st.rerun()
    with bc3:
        if st.button("▸  TÜM VAKALARI TARA", use_container_width=True, key="demo_all"):
            with st.spinner("3 flagship şirket analiz ediliyor…"):
                st.session_state.demo_results = []
                for step in DEMO_SCRIPT:
                    rec = next(r for r in get_esg_dataset() if r["sirket_adi"] == step["company"])
                    st.session_state.demo_results.append(analyzer.analyze_record(rec))
                st.session_state.demo_step = total_steps
                st.session_state.demo_playing = False
            st.rerun()

    if st.session_state.demo_playing and st.session_state.demo_step < total_steps:
        step = DEMO_SCRIPT[st.session_state.demo_step]
        with st.status(f"🔍 {step['company']} analiz ediliyor…", expanded=True) as status:
            st.write(step["narration"])
            rec = next(r for r in get_esg_dataset() if r["sirket_adi"] == step["company"])
            result = analyzer.analyze_record(rec)
            st.session_state.demo_results.append(result)
            st.session_state.demo_step += 1
            status.update(label=f"✅ {step['company']} — Risk: {result['risk_score']:.0f}/100", state="complete")
        st.session_state.demo_playing = st.session_state.demo_step < total_steps
        st.rerun()

    for i, step in enumerate(DEMO_SCRIPT):
        done = i < len(st.session_state.demo_results)
        active = i == len(st.session_state.demo_results) - 1 and st.session_state.demo_results
        icon = "✅" if done else "⏳"
        opacity = "1" if done or active else "0.45"
        render_html(f"""
        <div style="background:#0E1C2E;border:1px solid {'#14E08A' if active else '#1B2E44'};
                    border-radius:10px;padding:14px 18px;margin-bottom:10px;opacity:{opacity}">
          <span style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#14E08A">
            ADIM {step['step']}/{total_steps}</span> {icon}
          <b style="color:#E8EEF4"> {step['title']}</b><br>
          <span style="font-size:12px;color:#8AA0B4">{step['hook']}</span>
        </div>
        """)

    if st.session_state.demo_results:
        st.markdown("---")
        st.markdown('<div class="sq-card-label">CANLI ANALİZ SONUÇLARI</div>', unsafe_allow_html=True)

        latest = st.session_state.demo_results[-1]
        latest_step = DEMO_SCRIPT[len(st.session_state.demo_results) - 1]
        render_demo_score_reveal(latest, latest_step)

        if len(st.session_state.demo_results) == total_steps:
            st.success("✅ Sunum tamamlandı — 3 vaka analiz edildi!")
            scores = [r["risk_score"] for r in st.session_state.demo_results]
            names = [r["company_name"] for r in st.session_state.demo_results]
            fig = go.Figure(go.Bar(
                x=names, y=scores,
                marker_color=[risk_score_color(s) for s in scores],
                text=[f"{s:.0f}" for s in scores],
                textposition="outside",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#E8EEF4"}, height=280,
                yaxis=dict(range=[0, 110], title="Risk Skoru"),
                title="3 Vaka Karşılaştırması",
            )
            st.plotly_chart(fig, use_container_width=True)

        tabs = st.tabs([
            f"{r['company_name']} ({r['risk_score']:.0f})"
            for r in st.session_state.demo_results
        ])
        for tab, result, step in zip(tabs, st.session_state.demo_results, DEMO_SCRIPT[:len(st.session_state.demo_results)]):
            with tab:
                render_demo_score_reveal(result, step)
                render_analysis_results(result)


def render_verification_panel(verification: dict):
    """Çoklu kaynak teyit paneli."""
    if not verification:
        return
    conf = verification.get("confidence", "düşük")
    color = "#14E08A" if conf == "yüksek" else ("#FFB23E" if conf == "orta" else "#FF5C5C")
    st.markdown(
        '<p style="font-family:IBM Plex Mono,monospace;font-size:10px;'
        'letter-spacing:.16em;color:#5C7185;margin:16px 0 10px">ÇOKLU KAYNAK TEYİDİ</p>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("KAYNAK", verification.get("source_count", 0))
        c2.metric("GÜVENİLİR", verification.get("trusted_count", 0))
        c3.metric("GÜVEN", verification.get("confidence_score", 0))
        st.markdown(
            f'<p style="color:{color};font-weight:600;margin:8px 0 0">'
            f'{verification.get("label", "")}</p>',
            unsafe_allow_html=True,
        )
        for d in verification.get("details", []):
            icon = "✅" if d.get("trusted") else "⚠️"
            st.caption(f"{icon} {d.get('source', '')} · {d.get('type', '')}")


def render_timeline_panel(timeline: dict):
    """Zaman çizelgesi paneli."""
    if not timeline:
        return
    st.markdown(
        '<p style="font-family:IBM Plex Mono,monospace;font-size:10px;'
        'letter-spacing:.16em;color:#5C7185;margin:16px 0 10px">ZAMAN ÇİZELGESİ</p>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        tc1, tc2, tc3 = st.columns(3)
        tc1.metric("SÖYLEM", timeline.get("soylem_date") or "—")
        tc2.metric("EYLEM", timeline.get("eylem_date") or "—")
        gap = timeline.get("gap_days")
        tc3.metric("BOŞLUK", f"{gap} gün" if gap is not None else "—")
        if timeline.get("title"):
            color = "#FF5C5C" if timeline.get("has_anomaly") else "#14E08A"
            st.markdown(
                f'<p style="color:{color};font-weight:600;margin-top:8px">'
                f'{timeline.get("title", "")}</p>',
                unsafe_allow_html=True,
            )
            st.caption(timeline.get("description", ""))


def render_evidence_panel(result: dict):
    """Kanıt zinciri — kaynak, URL, tarih (Tier 1)."""
    evidence = result.get("evidence") or []
    if not evidence and result.get("source"):
        evidence = [{
            "source": result.get("source", ""),
            "url": result.get("kaynak_url", ""),
            "type": "dataset",
            "date": result.get("eylem_tarihi", ""),
        }]
    if not evidence:
        return

    st.markdown(
        '<p style="font-family:IBM Plex Mono,monospace;font-size:10px;'
        'letter-spacing:.16em;color:#5C7185;margin:16px 0 10px">KANIT ZİNCİRİ</p>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        for ev in evidence[:6]:
            src = ev.get("source", "Kaynak")
            url = ev.get("url", "")
            date = ev.get("date", "")
            typ = ev.get("type", "")
            line = f"**{src}**"
            if typ:
                line += f" · `{typ}`"
            if date:
                line += f" · {date}"
            st.markdown(line)
            if url:
                st.markdown(f"[Kaynağı aç]({url})")


def render_entity_panel(entity_gap: dict):
    """Sayısal entity karşılaştırma paneli."""
    if not entity_gap:
        return
    st.markdown(
        '<p style="font-family:IBM Plex Mono,monospace;font-size:10px;'
        'letter-spacing:.16em;color:#5C7185;margin:16px 0 10px">SAYISAL İDDİA ANALİZİ (Mini-NER)</p>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.caption(entity_gap.get("summary", ""))
        if entity_gap.get("conflicts"):
            for c in entity_gap["conflicts"]:
                icon = "🔴" if c.get("severity") == "high" else "🟠"
                st.markdown(f"{icon} **{c.get('title', '')}**")
                st.caption(c.get("description", ""))
        sm, em = st.columns(2)
        with sm:
            st.markdown("**Söylem metrikleri**")
            for m in entity_gap.get("soylem_metrics", [])[:4]:
                st.caption(f"• {m.get('raw', '')}")
        with em:
            st.markdown("**Eylem metrikleri**")
            for m in entity_gap.get("eylem_metrics", [])[:4]:
                st.caption(f"• {m.get('raw', '')}")


def render_hitl_panel(result: dict):
    """Human-in-the-loop analist onayı."""
    key = f"hitl_{result.get('company_name')}_{result.get('category')}"
    st.markdown(
        '<p style="font-family:IBM Plex Mono,monospace;font-size:10px;'
        'letter-spacing:.16em;color:#5C7185;margin:16px 0 10px">HUMAN-IN-THE-LOOP</p>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.caption("Nihai karar analist onayına tabidir (rapor §6 risk önlemi).")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅  Analist Onayı", key=f"approve_{key}", use_container_width=True):
                st.session_state[key] = "approved"
        with c2:
            if st.button("⚠️  İnceleme Gerekli", key=f"reject_{key}", use_container_width=True):
                st.session_state[key] = "review"
        status = st.session_state.get(key)
        if status == "approved":
            st.success("Onaylandı — rapor portföye alınabilir.")
        elif status == "review":
            st.warning("Manuel inceleme kuyruğuna alındı.")


def render_methodology_info():
    """Skor hesaplama metodolojisi."""
    with st.expander("📐 Metodoloji — Skor Nasıl Hesaplanır?"):
        st.markdown("""
        **Say-Do Gap Risk Skoru (0–100)**

        1. **Anlamsal benzerlik** (kosinüs, %65 ağırlık)  
           Söylem ile eylem vektörleri karşılaştırılır. Düşük benzerlik = yüksek risk.

        2. **Duygu boşluğu** (%35 ağırlık)  
           Söylemin eylemden ne kadar daha iyimser olduğu ölçülür.

        3. **Entity analizi** (mini-NER)  
           Emisyon %, MW, ton gibi sayısal iddialar çıkarılır; yönsel çelişkiler işaretlenir.

        4. **Çoklu kaynak teyidi**  
           2+ bağımsız whitelist kaynağı güven skorunu artırır.

        **Anomali sınıfları:** Tam Uyum (0–25) · Kapsam Uyuşmazlığı (26–50) ·  
        Doğrudan Çelişki (51–75) · Veri Yetersizliği (76–100)
        """)


def render_analysis_results(result: dict):
    """B2B terminal sonuç paneli — gerçek NLP çıktısı."""
    risk_skoru = result["risk_score"]
    band = risk_to_band(risk_skoru)
    band_class, band_color, _ = band_style(band)
    esg = derive_esg_scores(result)
    anomaliler = derive_anomalies(result)
    ticker = result.get("bist_code") or "—"
    sirket_adi = result["company_name"]
    mode_label = getattr(analyzer.nlp, "mode_label", "SQ-Detect")

    render_html(f"""
    <div style="background:#0E1C2E;border:1px solid #1B2E44;border-radius:12px;
                padding:18px 22px;display:flex;align-items:center;
                justify-content:space-between;margin-bottom:20px">
      <div>
        <div style="display:flex;align-items:baseline;gap:12px">
          <span style="font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:600;color:#CFE0EC">{ticker}</span>
          <span style="font-size:17px;font-weight:600;color:#E8EEF4">{sirket_adi}</span>
        </div>
        <div style="font-size:12px;color:#5C7185;margin-top:6px">
          {result['category']} · Say-Do Gap · {mode_label}
        </div>
      </div>
      <div class="sq-band {band_class}">
        <span style="width:8px;height:8px;border-radius:50%;background:{band_color};display:inline-block"></span>
        {band} YEŞİL AKLAMA RİSKİ
      </div>
    </div>
    """)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("RİSK SKORU", f"{risk_skoru:.0f} / 100")
    with m2:
        st.metric("E-SKOR (ÇEVRESEL)", f"{esg['e']} / 100")
    with m3:
        st.metric("S-SKOR (SOSYAL)", f"{esg['s']} / 100")
    with m4:
        st.metric("G-SKOR (YÖNETİŞİM)", f"{esg['g']} / 100")

    st.markdown("<br>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.2, 1], gap="large")
    with r1:
        render_html(f"""
        <div class="sq-card">
          <div class="sq-card-label">AI GEREKÇESİ</div>
          <p style="font-size:13.5px;line-height:1.65;color:#CFE0EC;margin:0">{result['summary']}</p>
        </div>
        """)

    with r2:
        render_anomalies_panel(anomaliler)

    e, s, g = esg["e"], esg["s"], esg["g"]
    render_html(f"""
    <div class="sq-card">
      <div class="sq-card-label">ESG KIRILIMI · PERFORMANS</div>
      <div style="margin-bottom:16px">
        <div style="display:flex;justify-content:space-between;margin-bottom:7px">
          <span style="font-size:13px;color:#CFE0EC">Çevresel (E)</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:600;color:{score_bar_color(e)}">{e}</span>
        </div>
        <div style="height:8px;border-radius:5px;background:#16293D;overflow:hidden">
          <div style="height:100%;width:{e}%;background:{score_bar_color(e)};border-radius:5px"></div>
        </div>
      </div>
      <div style="margin-bottom:16px">
        <div style="display:flex;justify-content:space-between;margin-bottom:7px">
          <span style="font-size:13px;color:#CFE0EC">Sosyal (S)</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:600;color:{score_bar_color(s)}">{s}</span>
        </div>
        <div style="height:8px;border-radius:5px;background:#16293D;overflow:hidden">
          <div style="height:100%;width:{s}%;background:{score_bar_color(s)};border-radius:5px"></div>
        </div>
      </div>
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:7px">
          <span style="font-size:13px;color:#CFE0EC">Yönetişim (G)</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:600;color:{score_bar_color(g)}">{g}</span>
        </div>
        <div style="height:8px;border-radius:5px;background:#16293D;overflow:hidden">
          <div style="height:100%;width:{g}%;background:{score_bar_color(g)};border-radius:5px"></div>
        </div>
      </div>
    </div>
    """)

    with st.expander("Detaylı NLP Metrikleri & Master System Prompt Raporu"):
        sim = result["similarity"]
        sent = result["sentiment"]
        comb = result["combined"]
        dc1, dc2, dc3, dc4 = st.columns(4)
        dc1.metric("Benzerlik", f"{sim['similarity']:.2%}")
        dc2.metric("Duygu Boşluğu", f"{sent['sentiment_gap']:.2f}")
        dc3.metric("Benzerlik Risk", f"{comb['similarity_risk']:.1f}")
        dc4.metric("Duygu Risk", f"{comb['sentiment_risk']:.1f}")
        st.markdown(f'<div class="report-output">{result["formatted_report"]}</div>', unsafe_allow_html=True)

    # Söylem-Eylem Boşluğu görselleştirmesi
    sim_val = result["similarity"]["similarity"]
    sent_gap = result["sentiment"]["sentiment_gap"]
    st.markdown('<div class="sq-card-label" style="margin-top:8px">SÖYLEM-EYLEM BOŞLUĞU</div>', unsafe_allow_html=True)
    gap_col1, gap_col2, gap_col3 = st.columns(3)
    gap_col1.metric("Anlamsal Benzerlik", f"{sim_val:.2%}")
    gap_col2.metric(
        "Duygu Boşluğu",
        f"{sent_gap:.2f}",
        help="Söylemin eylemden ne kadar daha iyimser olduğu (0-1). Yüksek = yeşil aklama sinyali.",
    )
    gap_col3.metric("Say-Do Risk", f"{result['risk_score']:.1f}/100")

    if result.get("verification") or result.get("timeline"):
        vcol, tcol = st.columns(2)
        with vcol:
            render_verification_panel(result.get("verification"))
        with tcol:
            render_timeline_panel(result.get("timeline"))

    render_evidence_panel(result)
    render_entity_panel(result.get("entity_gap"))
    render_hitl_panel(result)

    if result.get("live_sources"):
        with st.expander(f"Canlı Kaynaklar ({len(result['live_sources'])})"):
            for src in result["live_sources"]:
                st.markdown(f"**{src.get('source', '')}** ({src.get('type', '')})")
                if src.get("source_url"):
                    st.caption(src["source_url"])
                st.text((src.get("text") or "")[:400] + "...")

    try:
        pdf_bytes = build_analysis_pdf(result)
        st.download_button(
            "📄  Jüri PDF Raporu İndir",
            data=pdf_bytes,
            file_name=f"sustainquant_{result.get('bist_code', 'rapor')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"pdf_dl_{result.get('company_name', '')}_{result.get('category', '')}",
        )
    except Exception as e:
        st.caption(f"PDF oluşturulamadı: {e}")


def create_heatmap_chart(heatmap_data: dict) -> go.Figure:
    """Anomali ısı haritası (şirket × kategori)."""
    import math
    z_raw = heatmap_data["matrix"]
    z = [[float(v) if v is not None else math.nan for v in row] for row in z_raw]
    fig = go.Figure(go.Heatmap(
        z=z,
        x=heatmap_data["categories"],
        y=heatmap_data["companies"],
        colorscale=[
            [0.0, "#14E08A"],
            [0.35, "#FFB23E"],
            [0.55, "#FF8C42"],
            [0.75, "#FF5C5C"],
            [1.0, "#CC2244"],
        ],
        zmin=0,
        zmax=100,
        text=[[f"{v:.0f}" if v is not None else "" for v in row] for row in z_raw],
        texttemplate="%{text}",
        textfont={"size": 14, "color": "#E8EEF4"},
        hovertemplate="Şirket: %{y}<br>Kategori: %{x}<br>Risk: %{z:.1f}/100<extra></extra>",
        colorbar=dict(title="Risk", tickfont=dict(color="#8AA0B4")),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#E8EEF4"},
        height=320,
        margin=dict(l=80, r=20, t=30, b=60),
        xaxis=dict(tickangle=-20),
    )
    return fig


def create_comparison_chart(results: list) -> go.Figure:
    sorted_results = sorted(results, key=lambda r: r["risk_score"], reverse=True)
    companies = [r["company_name"] for r in sorted_results]
    scores = [r["risk_score"] for r in sorted_results]
    colors = [risk_score_color(s) for s in scores]
    categories = [r["category"] for r in sorted_results]

    fig = go.Figure(go.Bar(
        x=companies,
        y=scores,
        marker_color=colors,
        text=[f"{s:.1f}" for s in scores],
        textposition="outside",
        textfont={"color": "white", "size": 14, "family": "IBM Plex Mono"},
        hovertemplate="<b>%{x}</b><br>Kategori: %{customdata}<br>Risk: %{y:.1f}/100<extra></extra>",
        customdata=categories,
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        height=350,
        yaxis=dict(range=[0, 110], gridcolor="rgba(48,54,61,0.5)", title="Risk Skoru"),
        margin=dict(l=50, r=20, t=20, b=60),
        showlegend=False,
    )
    return fig


# ──────────────────────────────────────────────────────────────
# NLP MOTORU
# ──────────────────────────────────────────────────────────────

analyzer = load_analyzer()
models_ready = analyzer.nlp.is_ready
engine_label = getattr(analyzer.nlp, "mode_label", "SQ-Detect v1.0-MVP")

watchlist_pending = "watchlist_summary" not in st.session_state
if watchlist_pending:
    watchlist_items = placeholder_watchlist()
    high_risk_count = 0
else:
    watchlist_summary = st.session_state.watchlist_summary
    watchlist_items = company_watchlist_items(watchlist_summary)
    high_risk_count = watchlist_summary["high_risk_count"]

companies = get_companies()
company_options = [f"{c['sirket_adi']} ({c['bist_kodu']})" for c in companies]

# ──────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:12px 0 20px;border-bottom:1px solid #16273B;margin-bottom:20px">
          <div style="font-weight:700;font-size:17px;letter-spacing:.02em;color:#E8EEF4">
            SUSTAIN<span style="color:#14E08A">QUANT</span>
          </div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.22em;color:#5C7185;margin-top:5px">
            AI · ESG ANALİTİKS
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;letter-spacing:.14em;color:#5C7185;margin-bottom:8px">ANALİZ MODU</div>', unsafe_allow_html=True)
    mode = st.radio(
        "",
        ["Kayıtlı Şirket", "Canlı Doğrulama", "Manuel Giriş", "PDF Rapor Yükle", "Portföy Tarama", "Jüri Demo"],
        label_visibility="collapsed",
    )

    record = None
    selected_company = None

    if mode in ("Kayıtlı Şirket", "PDF Rapor Yükle", "Canlı Doğrulama"):
        st.markdown('<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;letter-spacing:.14em;color:#5C7185;margin:16px 0 8px">ANALİZ EDİLECEK ŞİRKET</div>', unsafe_allow_html=True)
        selected_option = st.selectbox("", company_options, label_visibility="collapsed")
        selected_company = selected_option.split(" (")[0]
        if mode == "Kayıtlı Şirket":
            record = next((r for r in get_esg_dataset() if r["sirket_adi"] == selected_company), None)
        elif mode == "Canlı Doğrulama":
            records = get_company_data(selected_company)
            record = records[0] if records else None
    elif mode not in ("Portföy Tarama", "Jüri Demo"):
        st.markdown('<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;letter-spacing:.14em;color:#5C7185;margin:16px 0 8px">ANALİZ EDİLECEK ŞİRKET</div>', unsafe_allow_html=True)
        st.selectbox("", company_options, label_visibility="collapsed", disabled=True)

    model_status = "Çevrimiçi" if models_ready else "Hazırlanıyor"
    source_count = len(SOURCE_WHITELIST)
    mode_hint = "Lite · offline" if NLP_MODE == "lightweight" else "Full · FinBERT"

    if "use_api_backend" not in st.session_state:
        st.session_state.use_api_backend = USE_API_BACKEND
    st.session_state.use_api_backend = st.checkbox(
        "API Backend (FastAPI)",
        value=st.session_state.use_api_backend,
        help=f"Bağlantı: {API_BASE_URL} — önce: python run.py all",
    )

    render_alerts_sidebar()
    render_methodology_info()
    if mode == "Jüri Demo":
        render_jury_presenter_notes()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:#0E1C2E;border:1px solid #1B2E44;border-radius:9px;padding:12px 14px;margin-bottom:14px">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.14em;color:#5C7185;margin-bottom:8px">MODEL DURUMU</div>
      <div><span class="sq-live-dot"></span><span style="font-size:12px;font-weight:600;color:#CFE0EC">{engine_label}</span></div>
      <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#5C7185;margin-top:6px">{model_status} · {mode_hint} · {source_count} kaynak</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
      <div style="background:#0E1C2E;border:1px solid #1B2E44;border-radius:9px;padding:12px">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:700;color:#FF5C5C">{high_risk_count}</div>
        <div style="font-size:10px;color:#8AA0B4;margin-top:4px">Yüksek risk</div>
      </div>
      <div style="background:#0E1C2E;border:1px solid #1B2E44;border-radius:9px;padding:12px">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:700;color:#14E08A">{len(companies)}</div>
        <div style="font-size:10px;color:#8AA0B4;margin-top:4px">İzlenen şirket</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# Şirket değişince eski analiz sonucunu temizle (sadece bağlam değişince)
if mode in ("Kayıtlı Şirket", "PDF Rapor Yükle", "Canlı Doğrulama") and selected_company:
    current_key = f"{mode}_{selected_company}"
else:
    current_key = mode
_prev_ctx = st.session_state.get("analysis_context")
if _prev_ctx != current_key:
    st.session_state.pop("analysis_result", None)
    st.session_state["analysis_context"] = current_key


# ──────────────────────────────────────────────────────────────
# TOPBAR
# ──────────────────────────────────────────────────────────────

st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:14px 0;border-bottom:1px solid #16273B;margin-bottom:24px">
  <div>
    <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:600;
                 letter-spacing:.18em;color:#14E08A">ESG DENETİM MOTORU</span>
    <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#3C4F63;margin:0 12px">/</span>
    <span style="font-size:13px;color:#8AA0B4">Greenwashing Risk Terminali</span>
  </div>
  <div>
    <span class="sq-live-dot"></span>
    <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                 font-weight:600;letter-spacing:.1em;color:#14E08A">CANLI</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# ANA İÇERİK — MOD 1 & 2: SÖYLEM / EYLEM ANALİZİ
# ──────────────────────────────────────────────────────────────

if mode in ("Kayıtlı Şirket", "Manuel Giriş"):
    col1, col2 = st.columns([1.4, 1], gap="large")

    with col1:
        if mode == "Kayıtlı Şirket" and record:
            default_soylem = record["soylem"]
            default_eylem = record["eylem"]
            default_company = record["sirket_adi"]
            default_category = record["esg_kategorisi"]
            st.markdown(f'<div class="sq-card-label">01 · KAYNAK — {record.get("kaynak", "N/A")}</div>', unsafe_allow_html=True)
        else:
            default_soylem = ""
            default_eylem = ""
            default_company = ""
            default_category = "Genel ESG"
            mc1, mc2 = st.columns(2)
            with mc1:
                default_company = st.text_input("Şirket Adı", placeholder="Örn: Tüpraş")
            with mc2:
                default_category = st.text_input("ESG Kategorisi", placeholder="Örn: Enerji Verimliliği")

        st.markdown('<div class="sq-card-label">02 · SÖYLEM — şirketin sürdürülebilirlik iddiası</div>', unsafe_allow_html=True)
        input_ctx = f"{mode}_{selected_company if record else 'manual'}"
        sync_text_inputs(input_ctx, default_soylem, default_eylem)

        soylem = st.text_area(
            "", height=130,
            placeholder="Şirketin kamuya açık taahhüdünü yapıştırın…",
            label_visibility="collapsed", key="sq_soylem",
        )

        st.markdown('<div class="sq-card-label" style="margin-top:16px">03 · EYLEM — güncel haber / resmi veri</div>', unsafe_allow_html=True)
        eylem = st.text_area(
            "", height=130,
            placeholder="KAP açıklaması, lisans verisi veya haber metnini yapıştırın…",
            label_visibility="collapsed", key="sq_eylem",
        )

        analiz_et = st.button(
            "▸  DERİNLEMESİNE ANALİZ BAŞLAT",
            type="primary", use_container_width=True, key="btn_deep_analyze",
        )

    with col2:
        render_watchlist_panel(watchlist_items, pending=watchlist_pending)
        if st.button("↻  İzleme listesini güncelle", key="refresh_watchlist", use_container_width=True):
            with st.spinner("Portföy skorları hesaplanıyor…"):
                st.session_state.watchlist_summary = analyzer.get_portfolio_summary()
                watchlist_items = company_watchlist_items(st.session_state.watchlist_summary)
                st.session_state["high_risk_count"] = st.session_state.watchlist_summary["high_risk_count"]
            st.rerun()

    if analiz_et:
        if not (soylem or "").strip() or not (eylem or "").strip():
            st.error("Lütfen hem söylem hem eylem alanını doldurun.")
        elif mode == "Manuel Giriş" and not (default_company or "").strip():
            st.error("Lütfen şirket adını girin.")
        elif mode == "Kayıtlı Şirket" and not record:
            st.error(f"Şirket verisi bulunamadı: {selected_company}")
        else:
            try:
                with st.spinner("Say-Do Gap analizi çalışıyor…"):
                    result = run_company_analysis(
                        analyzer, mode, record, soylem, eylem,
                        default_company, default_category,
                    )
                st.session_state["analysis_context"] = current_key
                st.toast(f"Analiz tamamlandı — Risk: {result['risk_score']:.0f}/100", icon="✅")
                st.rerun()
            except Exception as exc:
                st.error(f"Analiz hatası: {exc}")

    if st.session_state.get("analysis_result"):
        st.markdown("---")
        render_analysis_results(st.session_state["analysis_result"])

# ──────────────────────────────────────────────────────────────
# ANA İÇERİK — MOD: CANLI DOĞRULAMA (Faz B)
# ──────────────────────────────────────────────────────────────

elif mode == "Canlı Doğrulama":
    st.markdown('<div class="sq-card-label">CANLI DOĞRULAMA · KAP + HABER + ÇOKLU KAYNAK</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#8AA0B4;font-size:13px;margin-bottom:16px">'
        'KAP bildirimleri ve whitelist haber kaynakları otomatik çekilir; '
        'çoklu kaynak teyidi ve zaman çizelgesi analizi yapılır.</p>',
        unsafe_allow_html=True,
    )

    if not record:
        st.warning("Lütfen sidebar'dan bir şirket seçin.")
    else:
        col1, col2 = st.columns([1.4, 1], gap="large")

        with col1:
            st.markdown(f'<div class="sq-card-label">ŞİRKET — {record["bist_kodu"]} · {record["esg_kategorisi"]}</div>', unsafe_allow_html=True)

            lc1, lc2 = st.columns(2)
            with lc1:
                include_kap = st.checkbox("KAP bildirimi çek", value=True)
            with lc2:
                include_news = st.checkbox("Haber RSS tara", value=True)

            soylem_tarihi = st.text_input("Söylem tarihi", value="2025-01-01", help="YYYY-MM-DD")

            soylem = st.text_area(
                "Söylem", value=record["soylem"], height=120, label_visibility="collapsed",
                key=f"live_soylem_{selected_company}",
            )

            if st.button("↻  KAYNAKLARI ÇEK", use_container_width=True):
                with st.spinner("KAP ve haber kaynakları taranıyor…"):
                    st.session_state.live_context = fetch_live_context(
                        company_name=record["sirket_adi"],
                        bist_code=record["bist_kodu"],
                        category=record["esg_kategorisi"],
                        dataset_eylem=record.get("eylem", ""),
                        include_kap=include_kap,
                        include_news=include_news,
                    )
                st.rerun()

            ctx = st.session_state.get("live_context")
            preview_eylem = record["eylem"]
            if ctx:
                preview_eylem = ctx.get("merged_eylem") or preview_eylem
                if ctx.get("kap") and ctx["kap"].get("error"):
                    st.warning(f"KAP: {ctx['kap']['error']}")

            st.markdown('<div class="sq-card-label" style="margin-top:12px">EYLEM — birleşik kaynak metni</div>', unsafe_allow_html=True)
            eylem = st.text_area(
                "", value=preview_eylem, height=140, label_visibility="collapsed",
                key=f"live_eylem_{selected_company}",
            )

            if st.button("▸  CANLI DOĞRULAMA ANALİZİ", type="primary", use_container_width=True):
                with st.spinner("KAP + haber + Say-Do Gap analizi…"):
                    analysis_record = {
                        **record,
                        "soylem": soylem,
                        "eylem": eylem,
                        "soylem_tarihi": soylem_tarihi,
                    }
                    if ctx:
                        analysis_record = build_enriched_record(analysis_record, ctx, soylem_tarihi)
                    else:
                        live = fetch_live_context(
                            record["sirket_adi"], record["bist_kodu"],
                            record["esg_kategorisi"], record.get("eylem", ""),
                            include_kap, include_news,
                        )
                        analysis_record = build_enriched_record(analysis_record, live, soylem_tarihi)
                    result = analyzer.analyze_record(analysis_record)
                st.session_state["analysis_result"] = result
                st.success(f"Canlı analiz tamamlandı — Risk: {result['risk_score']:.0f}/100")

        with col2:
            render_watchlist_panel(watchlist_items, pending=watchlist_pending)
            ctx = st.session_state.get("live_context")
            if ctx and ctx.get("verification"):
                render_verification_panel(ctx["verification"])
            if ctx and ctx.get("kap") and not ctx["kap"].get("error"):
                kap = ctx["kap"]
                st.markdown("**Son KAP bildirimi**")
                st.caption(f"{kap.get('subject', '')} · {kap.get('publish_date', '')}")
                if kap.get("source_url"):
                    st.caption(kap["source_url"])
            if ctx and ctx.get("news"):
                st.markdown(f"**Eşleşen haberler ({len(ctx['news'])})**")
                for n in ctx["news"][:3]:
                    st.caption(f"• {n.get('title', '')[:80]}")

    if st.session_state.get("analysis_result"):
        st.markdown("---")
        render_analysis_results(st.session_state["analysis_result"])

# ──────────────────────────────────────────────────────────────
# ANA İÇERİK — MOD 3: PDF RAPOR YÜKLE
# ──────────────────────────────────────────────────────────────

elif mode == "PDF Rapor Yükle":
    st.markdown('<div class="sq-card-label">PDF SÜRDÜRÜLEBİLİRLİK RAPORU YÜKLE</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#8AA0B4;font-size:13px;margin-bottom:16px">'
        'PDF yükleyin → söylem otomatik çıkarılır. Eylem verisi seçili şirket için '
        'dataset + KAP/haber kaynaklarından doldurulur.</p>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1.4, 1], gap="large")

    with col1:
        uploaded = st.file_uploader("PDF dosyası", type=["pdf"], label_visibility="collapsed")

        company_records = get_company_data(selected_company) if selected_company else []
        default_record = company_records[0] if company_records else None

        pdf_soylem = st.session_state.get("pdf_soylem", "")
        pdf_meta = ""
        detected_company = None

        if uploaded:
            file_bytes = uploaded.getvalue()
            file_ctx = f"{uploaded.name}_{len(file_bytes)}"
            if st.session_state.get("_pdf_file_ctx") != file_ctx:
                with st.spinner("PDF metni çıkarılıyor…"):
                    raw_text = extract_text_from_pdf(file_bytes)
                    pdf_soylem = extract_esg_claims(raw_text)
                    detected_company = detect_company_from_pdf(raw_text, uploaded.name)
                    st.session_state["_pdf_raw_len"] = len(raw_text)
                    st.session_state["_pdf_detected_company"] = detected_company
                st.session_state["_pdf_file_ctx"] = file_ctx
                st.session_state["pdf_soylem"] = pdf_soylem
            else:
                pdf_soylem = st.session_state.get("pdf_soylem", "")
                detected_company = st.session_state.get("_pdf_detected_company")
            pdf_meta = (
                f"PDF okundu — {st.session_state.get('_pdf_raw_len', 0):,} karakter, "
                f"{len(pdf_soylem):,} karakter ESG özeti"
            )
            if detected_company:
                pdf_meta += f" · Tespit: **{detected_company}**"
            st.success(pdf_meta)

        if detected_company and selected_company and detected_company != selected_company:
            st.warning(
                f"PDF içeriği **{detected_company}** gibi görünüyor; "
                f"sidebar'da **{selected_company}** seçili. Doğru şirketi seçin."
            )

        company_ctx = f"pdf_{selected_company or 'none'}"
        default_eylem, eylem_source = resolve_pdf_eylem(default_record)
        sync_pdf_inputs(
            st.session_state.get("_pdf_file_ctx"),
            company_ctx,
            pdf_soylem if uploaded else None,
            default_eylem,
        )

        st.markdown('<div class="sq-card-label">SÖYLEM — PDF\'den çıkarılan iddialar</div>', unsafe_allow_html=True)
        soylem = st.text_area(
            "", height=130,
            placeholder="PDF yükleyin — iddialar buraya otomatik gelir…",
            label_visibility="collapsed", key="pdf_soylem",
        )

        st.markdown('<div class="sq-card-label" style="margin-top:16px">EYLEM — doğrulama verisi</div>', unsafe_allow_html=True)
        if eylem_source:
            st.caption(f"Kaynak: {eylem_source}")
        eylem = st.text_area(
            "", height=130,
            placeholder="Şirket seçildiğinde resmi kaynak verisi buraya gelir…",
            label_visibility="collapsed", key="pdf_eylem",
        )

        if st.button("▸  PDF ANALİZİ BAŞLAT", type="primary", use_container_width=True):
            if not (soylem or "").strip() or not (eylem or "").strip():
                st.error("Önce PDF yükleyin ve sidebar'dan şirket seçin.")
            elif not selected_company:
                st.error("Lütfen sidebar'dan şirket seçin.")
            else:
                with st.spinner("Say-Do Gap analizi çalışıyor…"):
                    analysis_record = {
                        **(default_record or {}),
                        "sirket_adi": selected_company,
                        "soylem": soylem,
                        "eylem": eylem,
                        "esg_kategorisi": (default_record or {}).get("esg_kategorisi", "Genel ESG"),
                    }
                    result = analyzer.analyze_record(analysis_record)
                st.session_state["analysis_result"] = result
                st.session_state["analysis_context"] = f"PDF_{selected_company}"
                st.success(f"Analiz tamamlandı — Risk skoru: {result['risk_score']:.0f}/100")
                st.rerun()

    with col2:
        render_watchlist_panel(watchlist_items, pending=watchlist_pending)
        if st.button("↻  İzleme listesini güncelle", key="refresh_watchlist_pdf", use_container_width=True):
            with st.spinner("Portföy skorları hesaplanıyor…"):
                st.session_state.watchlist_summary = analyzer.get_portfolio_summary()
            st.rerun()

    if st.session_state.get("analysis_result") and st.session_state.get("analysis_context", "").startswith("PDF"):
        st.markdown("---")
        render_analysis_results(st.session_state["analysis_result"])

# ──────────────────────────────────────────────────────────────
# ANA İÇERİK — MOD 4: PORTFÖY TARAMA
# ──────────────────────────────────────────────────────────────

elif mode == "Portföy Tarama":
    st.markdown('<div class="sq-card-label">PORTFÖY GENELİ TARAMA</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#8AA0B4;font-size:13px;margin-bottom:16px">Tüm kayıtlı şirketlerin ESG risk analizini tek tıkla çalıştırın.</p>', unsafe_allow_html=True)

    if st.button("▸  TÜM ŞİRKETLERİ TARA"):
        with st.spinner("Portföy taranıyor…"):
            summary = analyzer.get_portfolio_summary()
        st.session_state.portfolio_summary = summary
        st.session_state.portfolio_done = True
        st.session_state.watchlist_summary = summary

    if st.session_state.get("portfolio_done"):
        summary = st.session_state.portfolio_summary
        results = summary["results"]
        heatmap_data = analyzer.get_heatmap_data()

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("TOPLAM ŞİRKET", summary["total_companies"])
        s2.metric("ORT. RİSK", f"{summary['avg_risk_score']:.1f}")
        s3.metric("YÜKSEK RİSK", summary["high_risk_count"])
        s4.metric("MAKS. RİSK", f"{summary['max_risk_score']:.1f}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sq-card-label">ANOMALİ ISI HARİTASI · ŞİRKET × KATEGORİ</div>', unsafe_allow_html=True)
        st.plotly_chart(create_heatmap_chart(heatmap_data), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sq-card-label">ŞİRKET RİSK KARŞILAŞTIRMASI</div>', unsafe_allow_html=True)
        st.plotly_chart(create_comparison_chart(results), use_container_width=True)

        table_data = [{
            "Şirket": r["company_name"],
            "BIST": r["bist_code"],
            "Kategori": r["category"],
            "Risk": f"{r['risk_score']:.1f}",
            "Anomali": r["anomaly_status"],
            "Benzerlik": f"{r['similarity']['similarity']:.2%}",
        } for r in results]
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "Sonuçları CSV İndir",
                data=pd.DataFrame(table_data).to_csv(index=False, encoding="utf-8-sig"),
                file_name=f"sustainquant_portfolio_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dl2:
            try:
                portfolio_pdf = build_portfolio_pdf(summary)
                st.download_button(
                    "📄  Jüri PDF Özeti İndir",
                    data=portfolio_pdf,
                    file_name=f"sustainquant_portfolio_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.caption(f"PDF: {e}")

        for r in results:
            with st.expander(f"{r['company_name']} — {r['category']} (Risk: {r['risk_score']:.1f})"):
                render_analysis_results(r)

# ──────────────────────────────────────────────────────────────
# ANA İÇERİK — MOD 5: JÜRİ DEMO
# ──────────────────────────────────────────────────────────────

elif mode == "Jüri Demo":
    render_jury_demo()

# ──────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
_engine_footer = "SQ-Detect Lite" if NLP_MODE == "lightweight" else "FinBERT Full"
st.markdown(f"""
<div style="text-align:center;color:#5C7185;font-size:11px;padding:16px 0;border-top:1px solid #16273B">
  <b style="color:#8AA0B4">SustainaQuant AI</b> · Teknofest Finansal Teknolojiler 2026 · Takım ID: 918431<br>
  <span style="color:#14E08A">Say-Do Gap · Kosinüs Benzerliği · {_engine_footer}</span>
</div>
""", unsafe_allow_html=True)
