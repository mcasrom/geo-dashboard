import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime

# 1. Configuración de página
st.set_page_config(page_title="SITREP Geopolítico PRO", layout="wide")

# 2. Carga de Datos Segura con limpieza de tipos
@st.cache_data(ttl=300)
def load_data():
    try:
        conn = sqlite3.connect("data/geopol.db")
        df = pd.read_sql("SELECT * FROM SITREP ORDER BY date DESC", conn)
        conn.close()
        
        # --- LIMPIEZA DE TIPOS (Evita el TypeError) ---
        for col in ['vix', 'dxy', 'brent', 'sentiment_score', 'impacto']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        # Si falla, no rompemos la app, devolvemos DF vacío
        return pd.DataFrame()

df = load_data()

# --- SIDEBAR: INTELIGENCIA FINANCIERA ---
with st.sidebar:
    st.title("🕵️ SITREP Intelligence")
    
    if not df.empty:
        # Extraer valores con seguridad
        vix_val = float(df['vix'].iloc[0])
        dxy_val = float(df['dxy'].iloc[0])
        brent_val = float(df['brent'].iloc[0])
        
        c_vix, c_dxy = st.columns(2)
        
        # Metric con delta condicional seguro
        vix_delta = "ALTO RIESGO" if vix_val > 20 else "Estable"
        c_vix.metric("VIX (Pánico)", f"{vix_val:.2f}", delta=vix_delta, delta_color="inverse")
        
        c_dxy.metric("DXY (Dólar)", f"{dxy_val:.2f}")
        
        st.metric("BRENT CRUDE", f"${brent_val:.2f}/bbl")
        
        st.caption(f"Última actualización: {df['date'].iloc[0].strftime('%H:%M:%S')}")
    else:
        st.warning("Esperando datos de la DB...")
    
    st.divider()
    st.info("© 2024 M.Castillo\n\n📧 mybloggingnotes@gmail.com")

# --- INTERFAZ PRINCIPAL ---
st.title("🛡️ DASHBOARD ESTRATÉGICO MULTIPOLAR")

if df.empty:
    st.error("📡 La base de datos está vacía o no existe en 'data/geopol.db'. Ejecuta harvester.py primero.")
    st.stop()

t1, t2, t3, t4 = st.tabs(["📊 Análisis Narrativo", "🗺 Mapa de Crisis", "🧪 Metodología", "📖 Guía"])

with t1:
    col_l, col_r = st.columns([2,1])
    with col_l:
        # Gráfico de burbujas (Análisis de Hostilidad)
        fig = px.scatter(df, x="date", y="sentiment_score", size="impacto", color="bloque",
                         hover_name="titulo", title="Mapa de Hostilidad Global",
                         color_discrete_map={'Occidente':'#3498db','Eurasia':'#e74c3c','MENA':'#f1c40f'},
                         template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        st.write("### Últimas Alertas Críticas")
        # Mostrar las 10 noticias más impactantes
        st.dataframe(df[['bloque', 'titulo', 'impacto']].head(10), hide_index=True)

with t2:
    st.subheader("Vigilancia de Chokepoints Marítimos")
    m = folium.Map(location=[25, 45], zoom_start=3, tiles="CartoDB dark_matter")
    # Puntos críticos
    hotspots = {
        "Estrecho de Ormuz": [26.5, 56.2], 
        "Bab el-Mandeb": [12.6, 43.3], 
        "Estrecho de Taiwán": [23.5, 121.0], 
        "Canal de Suez": [30.6, 32.3]
    }
    for name, coords in hotspots.items():
        folium.Marker(coords, popup=name, icon=folium.Icon(color="red", icon="warning-sign")).add_to(m)
    st_folium(m, width="100%", height=500)

with t3:
    st.markdown("""
    ### 🛡️ Metodología V-OSINT 3.5
    - **Motor de Datos**: SQLite3 para alta velocidad en Odroid-C2.
    - **NLP**: Análisis de sentimiento mediante `TextBlob`.
    - **Mercados**: Correlación en tiempo real con VIX (Miedo) y DXY (Dólar) vía Yahoo Finance.
    - **Fuentes**: TASS (Rusia), SCMP (China), Al Jazeera (MENA), Reuters (Occidente).
    """)

with t4:
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("""
        **Guía de Lectura:**
        - **Sentiment Score**: Negativo (<0) indica noticias de guerra, sanciones o conflicto.
        - **VIX > 20**: Los mercados financieros detectan miedo global inminente.
        """)
    with col_g2:
        st.markdown("""
        **Acrónimos:**
        - **DXY**: Índice del Dólar (Fuerza de la moneda reserva).
        - **MENA**: Middle East & North Africa.
        - **OSINT**: Open Source Intelligence.
        """)
