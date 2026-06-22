"""
SustainaQuant AI – ESG Risk Terminali (Streamlit Dashboard)
=============================================================
Gerçek NLP motoruna bağlı interaktif dashboard.
Rapordaki Katman 3 – Sunum katmanının implementasyonu.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Proje kök dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    DASHBOARD_TITLE, DASHBOARD_PAGE_TITLE, DASHBOARD_LAYOUT,
    THEME, ANOMALY_COLORS, ANOMALY_LABELS, MASTER_SYSTEM_PROMPT,
    LOGO_PATH,
)
from data.esg_dataset import get_esg_dataset, get_companies
from nlp.analyzer import GreenwashingAnalyzer

# ──────────────────────────────────────────────────────────────
# SAYFA KONFİGÜRASYONU
# ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title=DASHBOARD_PAGE_TITLE,
    page_icon="📊",
    layout=DASHBOARD_LAYOUT,
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# KURUMSAL KOYU TEMA CSS
# ──────────────────────────────────────────────────────────────

st.markdown(f"""
<style>
    /* Ana tema */
    .stApp {{
        background-color: {THEME["bg_primary"]};
        color: {THEME["text_primary"]};
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {THEME["bg_secondary"]};
        border-right: 1px solid {THEME["border"]};
    }}

    /* Kartlar */
    .metric-card {{
        background: linear-gradient(135deg, {THEME["bg_card"]} 0%, {THEME["bg_secondary"]} 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid {THEME["accent_green"]};
        margin: 8px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }}

    .metric-card h3 {{
        margin: 0 0 8px 0;
        color: {THEME["text_secondary"]};
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    .metric-card .value {{
        font-size: 2rem;
        font-weight: 700;
        color: {THEME["text_primary"]};
    }}

    /* Risk kutusu */
    .risk-box {{
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        border: 1px solid {THEME["border"]};
        background: {THEME["bg_card"]};
    }}

    /* Rapor çıktısı */
    .report-output {{
        background: {THEME["bg_card"]};
        border: 1px solid {THEME["accent_green"]};
        border-radius: 12px;
        padding: 24px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.9rem;
        line-height: 1.8;
        white-space: pre-wrap;
        color: {THEME["accent_green"]};
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.05);
    }}

    /* Anomali badge'leri */
    .badge-tam-uyum {{
        background-color: rgba(0, 255, 136, 0.15);
        color: #00ff88;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }}
    .badge-kapsam {{
        background-color: rgba(255, 204, 0, 0.15);
        color: #ffcc00;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }}
    .badge-celiski {{
        background-color: rgba(255, 107, 53, 0.15);
        color: #ff6b35;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }}
    .badge-yetersizlik {{
        background-color: rgba(255, 0, 84, 0.15);
        color: #ff0054;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }}

    /* Başlık stili */
    .main-title {{
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00ff88, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }}

    .subtitle {{
        color: {THEME["text_secondary"]};
        font-size: 0.9rem;
        margin-top: 4px;
    }}

    /* Butonlar */
    .stButton > button {{
        background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
        color: #000000;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        transition: all 0.3s ease;
        width: 100%;
    }}

    .stButton > button:hover {{
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
        transform: translateY(-1px);
    }}

    /* Divider */
    .section-divider {{
        border: none;
        border-top: 1px solid {THEME["border"]};
        margin: 20px 0;
    }}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ──────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_analyzer():
    """NLP analyzer'ı yükler ve cache'ler."""
    with st.spinner("🧠 NLP modelleri yükleniyor... (İlk seferde 1-2 dakika sürebilir)"):
        analyzer = GreenwashingAnalyzer()
        try:
            analyzer.nlp.warmup()
        except Exception as e:
            st.warning(f"⚠️ Model yükleme uyarısı: {e}")
    return analyzer


def get_anomaly_color(anomaly_key: str) -> str:
    """Anomali durumuna göre renk döndürür."""
    return ANOMALY_COLORS.get(anomaly_key, THEME["text_secondary"])


def create_gauge_chart(risk_score: float, title: str = "Yeşil Aklama Risk Skoru") -> go.Figure:
    """Risk skoru için gauge chart oluşturur."""
    # Renk belirleme
    if risk_score <= 25:
        bar_color = ANOMALY_COLORS["tam_uyum"]
    elif risk_score <= 50:
        bar_color = ANOMALY_COLORS["kapsam_uyusmazligi"]
    elif risk_score <= 75:
        bar_color = ANOMALY_COLORS["dogrudan_celiski"]
    else:
        bar_color = ANOMALY_COLORS["veri_yetersizligi"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        number={"suffix": "/100", "font": {"size": 36, "color": "white"}},
        title={"text": title, "font": {"size": 16, "color": "#8b949e"}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#30363d",
                "dtick": 25,
                "tickfont": {"color": "#8b949e"},
            },
            "bar": {"color": bar_color, "thickness": 0.75},
            "bgcolor": "#1e2530",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 25], "color": "rgba(0, 255, 136, 0.08)"},
                {"range": [25, 50], "color": "rgba(255, 204, 0, 0.08)"},
                {"range": [50, 75], "color": "rgba(255, 107, 53, 0.08)"},
                {"range": [75, 100], "color": "rgba(255, 0, 84, 0.08)"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 2},
                "thickness": 0.8,
                "value": risk_score,
            },
        },
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        height=280,
        margin=dict(l=30, r=30, t=50, b=10),
    )
    return fig


def create_comparison_chart(results: list) -> go.Figure:
    """Şirket karşılaştırma bar chart'ı oluşturur."""
    companies = [r["company_name"] for r in results]
    scores = [r["risk_score"] for r in results]
    colors = [get_anomaly_color(r["anomaly_key"]) for r in results]
    categories = [r["category"] for r in results]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=companies,
        y=scores,
        marker_color=colors,
        text=[f"{s:.1f}" for s in scores],
        textposition="outside",
        textfont={"color": "white", "size": 14, "family": "JetBrains Mono"},
        hovertemplate="<b>%{x}</b><br>Kategori: %{customdata}<br>Risk Skoru: %{y:.1f}/100<extra></extra>",
        customdata=categories,
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        height=350,
        yaxis=dict(
            range=[0, 110],
            gridcolor="rgba(48, 54, 61, 0.5)",
            title=dict(
                text="Risk Skoru",
                font=dict(color="#8b949e")
            ),
        ),
        xaxis=dict(
            title="",
            tickfont={"size": 13},
        ),
        margin=dict(l=50, r=20, t=20, b=60),
        showlegend=False,
    )
    return fig


# ──────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────

with st.sidebar:
    # Logo
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    else:
        st.markdown("## 📊 SustainQuant AI")

    st.markdown("---")
    st.markdown("### 🎛️ Kontrol Paneli")

    # Analiz modu seçimi
    mode = st.radio(
        "Analiz Modu",
        ["📋 Kayıtlı Şirket Analizi", "✍️ Manuel Giriş", "📊 Toplu Portföy Tarama"],
        index=0,
    )

    st.markdown("---")

    if mode == "📋 Kayıtlı Şirket Analizi":
        companies = get_companies()
        company_names = [c["sirket_adi"] for c in companies]
        selected_company = st.selectbox(
            "🏢 Şirket Seçin",
            company_names,
            index=0,
        )

    st.markdown("---")

    # Sistem bilgisi
    st.markdown("### ℹ️ Sistem Bilgisi")
    st.markdown(f"""
    <div style="font-size: 0.8rem; color: {THEME['text_secondary']}; line-height: 1.6;">
    <b>Proje:</b> SustainaQuant AI<br>
    <b>Takım ID:</b> 918431<br>
    <b>Versiyon:</b> 1.0.0-MVP<br>
    <b>Motor:</b> FinBERT + BERTürk<br>
    <b>Algoritma:</b> Say-Do Gap<br>
    <b>Tarih:</b> {datetime.now().strftime("%d.%m.%Y %H:%M")}
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# ANA İÇERİK
# ──────────────────────────────────────────────────────────────

# Başlık
st.markdown(f"""
<div style="margin-bottom: 24px;">
    <p class="main-title">{DASHBOARD_TITLE}</p>
    <p class="subtitle">NLP Tabanlı Yeşil Aklama (Greenwashing) Tespit & ESG Risk Analitiği Platformu</p>
</div>
""", unsafe_allow_html=True)

# Analyzer'ı yükle
analyzer = load_analyzer()

# ── MOD 1: Kayıtlı Şirket Analizi ──────────────────────────

if mode == "📋 Kayıtlı Şirket Analizi":
    dataset = get_esg_dataset()
    company_data = [r for r in dataset if r["sirket_adi"] == selected_company]

    if company_data:
        record = company_data[0]

        # Üst bilgi kartları
        info_col1, info_col2, info_col3 = st.columns(3)
        with info_col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Şirket</h3>
                <div class="value">{record['sirket_adi']}</div>
            </div>
            """, unsafe_allow_html=True)
        with info_col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>BIST Kodu</h3>
                <div class="value">{record['bist_kodu']}</div>
            </div>
            """, unsafe_allow_html=True)
        with info_col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>ESG Kategorisi</h3>
                <div class="value" style="font-size: 1.2rem;">{record['esg_kategorisi']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        # Söylem vs Eylem paneli
        col_soylem, col_eylem = st.columns(2)

        with col_soylem:
            st.markdown("#### 📢 Şirket Söylemi (ESG Raporu)")
            st.info(record["soylem"])

        with col_eylem:
            st.markdown("#### 🔍 Gerçekleşen Eylem (Bağımsız Kaynak)")
            st.warning(record["eylem"])
            st.caption(f"📌 Kaynak: {record.get('kaynak', 'N/A')}")

        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        # Analizi çalıştır
        if st.button("🚀 Say-Do Gap Analizini Çalıştır", use_container_width=True):
            with st.spinner("🧠 NLP motoru analiz yapıyor..."):
                result = analyzer.analyze_record(record)

            st.session_state.current_result = result
            st.session_state.analysis_done = True

        # Sonuçları göster
        if st.session_state.get("analysis_done"):
            result = st.session_state.current_result

            st.markdown("### 📊 Analiz Sonuçları")

            # Gauge chart ve metrikler
            col_gauge, col_metrics = st.columns([1, 1])

            with col_gauge:
                fig = create_gauge_chart(result["risk_score"])
                st.plotly_chart(fig, use_container_width=True)

            with col_metrics:
                # Anomali durumu
                anomaly_color = get_anomaly_color(result["anomaly_key"])
                st.markdown(f"""
                <div class="risk-box" style="border-left: 4px solid {anomaly_color};">
                    <div style="color: {THEME['text_secondary']}; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">Anomali Durumu</div>
                    <div style="color: {anomaly_color}; font-size: 1.5rem; font-weight: 700; margin: 8px 0;">{result['anomaly_status']}</div>
                </div>
                """, unsafe_allow_html=True)

                # Detay metrikler
                sim = result["similarity"]
                sent = result["sentiment"]
                comb = result["combined"]

                m1, m2 = st.columns(2)
                with m1:
                    st.metric("Benzerlik Skoru", f"{sim['similarity']:.2%}")
                    st.metric("Benzerlik Risk", f"{comb['similarity_risk']:.1f}/100")
                with m2:
                    st.metric("Duygu Boşluğu", f"{sent['sentiment_gap']:.2f}")
                    st.metric("Duygu Risk", f"{comb['sentiment_risk']:.1f}/100")

            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

            # Master System Prompt formatında rapor çıktısı
            st.markdown("### 📋 Analiz Raporu (Master System Prompt Çıktısı)")
            st.markdown(f"""
            <div class="report-output">{result['formatted_report']}</div>
            """, unsafe_allow_html=True)

            # Duygu analizi detayı
            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
            st.markdown("### 🎭 Duygu Analizi Detayı")
            st.markdown(f"*{sent['interpretation']}*")

            sent_col1, sent_col2 = st.columns(2)
            with sent_col1:
                soylem_s = sent["soylem_sentiment"]
                st.markdown(f"**Söylem Duygusu:** `{soylem_s['label']}` (polarite: {soylem_s['polarity']:.2f})")
            with sent_col2:
                eylem_s = sent["eylem_sentiment"]
                st.markdown(f"**Eylem Duygusu:** `{eylem_s['label']}` (polarite: {eylem_s['polarity']:.2f})")


# ── MOD 2: Manuel Giriş ─────────────────────────────────────

elif mode == "✍️ Manuel Giriş":
    st.markdown("### ✍️ Manuel Söylem-Eylem Analizi")
    st.markdown(f"<p style='color:{THEME['text_secondary']}'>Herhangi bir şirketin ESG söylemini ve gerçekleşen eylemini girerek yeşil aklama risk analizi yapın.</p>", unsafe_allow_html=True)

    col_input1, col_input2 = st.columns(2)

    with col_input1:
        manual_company = st.text_input("🏢 Şirket Adı", placeholder="Örn: Tüpraş")
        manual_category = st.text_input("📁 ESG Kategorisi", placeholder="Örn: Enerji Verimliliği")

    with col_input2:
        pass

    manual_soylem = st.text_area(
        "📢 Şirket Söylemi (ESG Raporu)",
        height=120,
        placeholder="Şirketin sürdürülebilirlik raporundaki iddiasını buraya yazın..."
    )

    manual_eylem = st.text_area(
        "🔍 Gerçekleşen Eylem (Bağımsız Kaynak)",
        height=120,
        placeholder="Bağımsız kaynaklardan doğrulanan gerçek durumu buraya yazın..."
    )

    if st.button("🚀 Analizi Çalıştır", use_container_width=True):
        if manual_company and manual_soylem and manual_eylem:
            with st.spinner("🧠 NLP motoru analiz yapıyor..."):
                result = analyzer.analyze_custom(
                    company_name=manual_company,
                    category=manual_category or "Genel ESG",
                    soylem=manual_soylem,
                    eylem=manual_eylem,
                )

            # Gauge ve rapor gösterimi
            col_g, col_r = st.columns([1, 1])
            with col_g:
                fig = create_gauge_chart(result["risk_score"])
                st.plotly_chart(fig, use_container_width=True)

            with col_r:
                anomaly_color = get_anomaly_color(result["anomaly_key"])
                st.markdown(f"""
                <div class="risk-box" style="border-left: 4px solid {anomaly_color};">
                    <div style="color: {THEME['text_secondary']}; font-size: 0.85rem;">ANOMALİ DURUMU</div>
                    <div style="color: {anomaly_color}; font-size: 1.5rem; font-weight: 700; margin: 8px 0;">{result['anomaly_status']}</div>
                    <div style="color: {THEME['text_secondary']}; font-size: 0.9rem; margin-top: 12px;">
                        Benzerlik: {result['similarity']['similarity']:.2%} | 
                        Duygu Boşluğu: {result['sentiment']['sentiment_gap']:.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("### 📋 Analiz Raporu")
            st.markdown(f"""
            <div class="report-output">{result['formatted_report']}</div>
            """, unsafe_allow_html=True)
        else:
            st.error("⚠️ Lütfen tüm alanları doldurun.")


# ── MOD 3: Toplu Portföy Tarama ─────────────────────────────

elif mode == "📊 Toplu Portföy Tarama":
    st.markdown("### 📊 Toplu Portföy Tarama")
    st.markdown(f"<p style='color:{THEME['text_secondary']}'>Tüm kayıtlı şirketlerin ESG risk analizini tek tıkla çalıştırın. Portföy yöneticileri için idealdir.</p>", unsafe_allow_html=True)

    if st.button("🔄 Tüm Şirketleri Tara", use_container_width=True):
        with st.spinner("🧠 Portföy taranıyor... (Bu işlem biraz zaman alabilir)"):
            summary = analyzer.get_portfolio_summary()

        st.session_state.portfolio_summary = summary
        st.session_state.portfolio_done = True

    if st.session_state.get("portfolio_done"):
        summary = st.session_state.portfolio_summary
        results = summary["results"]

        # Özet kartlar
        sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
        with sum_col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Toplam Şirket</h3>
                <div class="value">{summary['total_companies']}</div>
            </div>
            """, unsafe_allow_html=True)
        with sum_col2:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {THEME['accent_blue']};">
                <h3>Ort. Risk Skoru</h3>
                <div class="value">{summary['avg_risk_score']:.1f}</div>
            </div>
            """, unsafe_allow_html=True)
        with sum_col3:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {THEME['accent_orange']};">
                <h3>Yüksek Risk</h3>
                <div class="value">{summary['high_risk_count']}</div>
            </div>
            """, unsafe_allow_html=True)
        with sum_col4:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {THEME['accent_red']};">
                <h3>Maks. Risk</h3>
                <div class="value">{summary['max_risk_score']:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        # Karşılaştırma grafiği
        st.markdown("### 📈 Şirket Risk Karşılaştırması")
        fig = create_comparison_chart(results)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        # Detaylı tablo
        st.markdown("### 📋 Detaylı Sonuçlar")
        table_data = []
        for r in results:
            table_data.append({
                "Şirket": r["company_name"],
                "BIST": r["bist_code"],
                "Kategori": r["category"],
                "Risk Skoru": f"{r['risk_score']:.1f}",
                "Anomali": r["anomaly_status"],
                "Benzerlik": f"{r['similarity']['similarity']:.2%}",
                "Duygu Boşluğu": f"{r['sentiment']['sentiment_gap']:.2f}",
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        # Her şirket için rapor çıktıları
        st.markdown("### 📝 Şirket Bazlı Raporlar")
        for r in results:
            with st.expander(f"{'🟢' if r['risk_score'] <= 25 else '🟡' if r['risk_score'] <= 50 else '🔴'} {r['company_name']} – {r['category']} (Risk: {r['risk_score']:.1f})"):
                st.markdown(f"""
                <div class="report-output">{r['formatted_report']}</div>
                """, unsafe_allow_html=True)

        # CSV dışa aktarma
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
        csv_df = pd.DataFrame(table_data)
        st.download_button(
            label="📥 Sonuçları CSV Olarak İndir",
            data=csv_df.to_csv(index=False, encoding="utf-8-sig"),
            file_name=f"sustainquant_portfolio_analiz_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ──────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align: center; color: {THEME['text_secondary']}; font-size: 0.8rem; padding: 20px 0;">
    <b>SustainaQuant AI</b> | Teknofest Finansal Teknolojiler Yarışması 2026<br>
    Takım ID: 918431 | NLP Tabanlı ESG Risk & Yeşil Aklama Tespit Motoru<br>
    <span style="color: {THEME['accent_green']};">Powered by FinBERT + BERTürk + Cosine Similarity</span>
</div>
""", unsafe_allow_html=True)
