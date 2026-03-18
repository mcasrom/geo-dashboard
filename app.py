import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="SITREP Geopolítico Multipolar V4.1", layout="wide")

@st.cache_data(ttl=300)
def load_data():
    try:
        conn = sqlite3.connect("data/geopol.db")
        df = pd.read_sql("SELECT * FROM SITREP ORDER BY date DESC", conn)
        conn.close()
        
        # --- LIMPIEZA FORZOSA DE DATOS (Anti-Crash) ---
        numeric_cols = ['sentiment_score', 'impacto', 'brent', 'vix', 'dxy']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        df['date'] = pd.to_datetime(df['date'])
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- SIDEBAR (Copyright & Markets) ---
with st.sidebar:
    st.title("🎖️ COMMAND CENTER")
    if not df.empty:
        # Aseguramos que los valores sean float antes de pasarlos a metric
        vix_val = float(df['vix'].iloc[0])
        brent_val = float(df['brent'].iloc[0])
        dxy_val = float(df['dxy'].iloc[0])
        
        st.metric("VIX (PANIC INDEX)", f"{vix_val:.2f}", 
                  delta="ALERTA" if vix_val > 20 else "ESTABLE", delta_color="inverse")
        st.metric("BRENT CRUDE", f"${brent_val:.2f}")
        st.metric("DXY (USD INDEX)", f"{dxy_val:.2f}")
    
    st.divider()
    st.info("© 2024 M.Castillo\n\n📧 mybloggingnotes@gmail.com")
    st.caption("Odroid-C2 Intelligence Unit")

# --- HEADER ---
st.title("🌍 INTELIGENCIA ESTRATÉGICA GLOBAL (16 FUENTES)")

if df.empty:
    st.error("📡 Sin datos. Ejecuta harvester.py primero.")
    st.stop()

# KPIs de Estado Multipolar
k1, k2, k3, k4 = st.columns(4)
k1.metric("INTEL CAPTURADA", len(df))
k2.metric("FUENTES ACTIVAS", df['fuente'].nunique())
sent_west = df[df['bloque'] == "Occidente (G7)"]['sentiment_score'].mean()
sent_east = df[df['bloque'] == "Eurasia (RU/CH)"]['sentiment_score'].mean()
k3.metric("TENSIÓN OCCIDENTE", f"{sent_west:.2f}")
k4.metric("TENSIÓN EURASIA", f"{sent_east:.2f}")

st.divider()

# --- TABS ---
t1, t2, t3, t4, t5 = st.tabs(["📊 Radar Geopolítico", "📡 Guerra de Narrativas", "💹 Mercados", "🗺 Mapa de Crisis", "📚 Directorio de Fuentes"])

with t1:
    fig = px.scatter(df, x="date", y="sentiment_score", size="impacto", color="bloque",
                     hover_name="titulo", height=600, template="plotly_dark",
                     color_discrete_map={'Occidente (G7)':'#3498db','Eurasia (RU/CH)':'#e74c3c','MENA / Resistencia':'#f1c40f','Sur Global / Otros':'#2ecc71'})
    st.plotly_chart(fig, use_container_width=True)

with t2:
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(px.pie(df, names='narrativa', hole=0.4, title="Sesgo Narrativo Global"), use_container_width=True)
    with col_b:
        st.write("### Últimos Despliegues de Mensaje")
        st.dataframe(df[['bloque', 'titulo', 'fuente']].head(15), hide_index=True)

with t3:
    st.subheader("Análisis de Riesgo Financiero Geopolítico")
    st.line_chart(df.set_index('date')[['brent', 'vix']])

with t4:
    m = folium.Map(location=[25, 45], zoom_start=3, tiles="CartoDB dark_matter")
    hotspots = {"Estrecho de Ormuz": [26, 56], "Bab el-Mandeb": [12, 43], "Taiwán": [23, 121], "Donbás": [48, 37]}
    for n, c in hotspots.items():
        folium.Marker(c, popup=n, icon=folium.Icon(color="red", icon="warning-sign")).add_to(m)
    st_folium(m, width="100%", height=500)

with t5:
    st.subheader("Fuentes en Monitorización Activa")
    source_stats = df.groupby('fuente').agg({'titulo': 'count', 'sentiment_score': 'mean'}).sort_values(by='titulo', ascending=False)
    st.table(source_stats.rename(columns={'titulo': 'Alertas Totales', 'sentiment_score': 'Sesgo (Sentiment)'}))
