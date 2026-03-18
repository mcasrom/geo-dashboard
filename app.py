import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(page_title="SITREP Geopolítico V5", layout="wide", page_icon="📡")

# Estilo CSS para mejorar la estética en pantallas oscuras
st.markdown("""<style>
    .reportview-container { background: #0e1117; }
    .stMetric { background: #1c212d; padding: 10px; border-radius: 10px; border: 1px solid #30363d; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_all_data():
    try:
        conn = sqlite3.connect("data/geopol.db")
        df = pd.read_sql("SELECT * FROM SITREP ORDER BY date DESC", conn)
        meta = pd.read_sql("SELECT last_run FROM METADATA", conn)
        conn.close()
        
        df['date'] = pd.to_datetime(df['date'])
        numeric_cols = ['sentiment_score', 'impacto', 'brent', 'vix', 'dxy']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
        return df, meta['last_run'].iloc[0]
    except:
        return pd.DataFrame(), "N/A"

df, last_update = load_all_data()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2560/2560303.png", width=80)
    st.title("COMMAND CENTER")
    st.status(f"Última actualización:\n{last_update}")
    
    if not df.empty:
        # Recuperamos el último valor no-cero de los mercados
        m_brent = df[df['brent'] > 0]['brent'].iloc[0] if not df[df['brent'] > 0].empty else 0.0
        m_vix = df[df['vix'] > 0]['vix'].iloc[0] if not df[df['vix'] > 0].empty else 0.0
        m_dxy = df[df['dxy'] > 0]['dxy'].iloc[0] if not df[df['dxy'] > 0].empty else 0.0
        
        st.metric("BRENT CRUDE", f"${m_brent:.2f} USD")
        st.metric("VIX PANIC INDEX", f"{m_vix:.2f}", delta="ALERTA" if m_vix > 20 else "ESTABLE", delta_color="inverse")
        st.metric("DXY INDEX", f"{m_dxy:.2f}")
    
    st.divider()
    st.caption("Terminal Inteligencia Odroid-C2")
    st.info("V 5.0.1 - Multipolar Ready")

# --- MAIN UI ---
st.title("🌍 SITREP GEOPOLÍTICO MULTIPOLAR")
st.caption(f"Monitorizando {df['fuente'].nunique() if not df.empty else 0} fuentes globales en tiempo real.")

if df.empty:
    st.warning("Esperando datos del harvester...")
    st.stop()

# KPIs Superiores
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("INTEL TOTAL", len(df))
with c2:
    # Color de sentimiento según valor
    avg_sent = df['sentiment_score'].mean()
    st.metric("SENTIMIENTO GLOBAL", f"{avg_sent:.2f}", delta="TENSIÓN" if avg_sent < 0 else "NEUTRAL")
with c3:
    volatilidad = df['sentiment_score'].std() * 10
    st.metric("VOLATILIDAD NARRATIVA", f"{volatilidad:.1f}%")
with c4:
    fuentes_activas = df['fuente'].nunique()
    st.metric("COBERTURA FUENTES", fuentes_activas)

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["📊 Radar de Tensión", "📡 Guerra de Narrativas", "💹 Mercados", "🗺 Mapa de Crisis"])

with t1:
    # Gráfico de burbujas dinámico
    fig = px.scatter(df.head(200), x="date", y="sentiment_score", size="impacto", color="bloque",
                     hover_name="titulo", height=550, template="plotly_dark",
                     title="Impacto y Sentimiento por Bloque Geopolítico (Últimas Alertas)",
                     color_discrete_map={'Occidente (G7)':'#3498db','Eurasia (RU/CH)':'#e74c3c','MENA / Resistencia':'#f1c40f','Sur Global / Otros':'#2ecc71'})
    st.plotly_chart(fig, use_container_width=True)

with t2:
    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.plotly_chart(px.pie(df, names='narrativa', hole=0.5, title="Sesgo Dominante"), use_container_width=True)
    with col_right:
        st.write("### 🗞️ Últimos Cables de Inteligencia")
        st.dataframe(df[['date', 'bloque', 'fuente', 'titulo']].head(20), hide_index=True)

with t3:
    st.subheader("Interrelación Energía y Riesgo")
    # Gráfico de dos ejes para Brent vs VIX
    st.line_chart(df.set_index('date')[['brent', 'vix']])
    st.caption("Nota: Si los valores son 0, el mercado está cerrado o la API de Yahoo Finance está en mantenimiento.")

with t4:
    # Mapa optimizado
    m = folium.Map(location=[25, 45], zoom_start=2, tiles="CartoDB dark_matter")
    hotspots = {
        "Estrecho de Ormuz (Energía)": [26, 56],
        "Bab el-Mandeb (Logística)": [12, 43],
        "Taiwán (Semiconductores)": [23, 121],
        "Donbás (Frontera OTAN/RU)": [48, 37],
        "Esequibo (LatAm Tensión)": [6.7, -58.9],
        "Sahel (África Subsahariana)": [15, 10]
    }
    for n, c in hotspots.items():
        folium.Marker(c, popup=n, icon=folium.Icon(color="red", icon="warning-sign")).add_to(m)
    st_folium(m, width="100%", height=600)
