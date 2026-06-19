import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="SustainaQuant AI", layout="wide")

# Kurumsal Koyu Tema CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e2530; padding: 20px; border-radius: 10px; border-left: 5px solid #00ff88; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #00ff88; color: #000000; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Sidebar (Logo)
st.sidebar.image("sustainquant_logo.png", use_container_width=True)
st.sidebar.title("Kontrol Paneli")

st.title("📊 SustainaQuant AI | ESG Risk Terminali")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Veri Girişi")
    soylem = st.text_area("Şirket Söylemi (ESG Raporu):", height=100)
    eylem = st.text_area("Gerçekleşen Eylem (Haber/Veri):", height=100)
    if st.button("🚀 Analizi Çalıştır"):
        # Burası aslında AI modelinin döneceği yer
        st.session_state.analyze = True

with col2:
    st.subheader("Canlı Risk Paneli")
    if 'analyze' in st.session_state:
        # Görselleştirme (Plotly - Gauge Chart)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = 65, # AI'dan gelecek skor
            title = {'text': "Greenwashing Risk Skoru"},
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#00ff88"}}))
        st.plotly_chart(fig, use_container_width=True)
        
        st.metric(label="Güven Aralığı", value="%88")
        st.info("⚠️ Dikkat: Söylem ve eylem arasında %65'lik bir uyumsuzluk tespit edildi.")
    else:
        st.write("Analiz başlatmak için veri giriniz.")
