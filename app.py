import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(page_title="SustainaQuant AI", layout="wide")

# CSS - Arka planı açık mavi yaptık
st.markdown("""
    <style>
    .main { background-color: #e3f2fd; } 
    .stButton>button { width: 100%; border-radius: 8px; background-color: #2e7d32; color: white; font-weight: bold; }
    .report-card { background-color: #ffffff; padding: 25px; border-radius: 15px; border-left: 6px solid #2e7d32; box-shadow: 0 8px 12px rgba(0,0,0,0.15); }
    </style>
    """, unsafe_allow_html=True)

# Logoyu ekle
st.sidebar.image("sustainquant_logo.png", use_container_width=True)

st.title("🌱 SustainQuant AI | ESG Denetim Motoru")

# Sütunlu Tasarım
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Giriş Verileri")
    sirket = st.selectbox("Analiz Edilecek Şirket", ["Tüpraş", "ASELSAN", "Ford Otosan"])
    soylem = st.text_area("Şirketin Sürdürülebilirlik İddiası (Söylem):", height=150)
    eylem = st.text_area("Güncel Haber / Resmi Veri (Eylem):", height=150)
    analiz_et = st.button("🚀 Derinlemesine Analiz Başlat")

with col2:
    st.subheader("🔍 Analiz Sonuçları")
    if analiz_et:
        if soylem and eylem:
            with st.container():
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.metric(label="Yeşil Aklama Risk Skoru", value="20/100")
                st.write("**Anomali Durumu:** Kapsam Uyuşmazlığı")
                st.write("**Özet Gerekçe:** Taahhüt edilen kapasite ile resmi onaylar arasında ölçek farkı tespit edildi.")
                st.write("**Tetikleyici:** Şanlıurfa GES lisans süreçleri izlenmeli.")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("Lütfen analiz için verileri giriniz.")
