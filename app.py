import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(page_title="SITREP Geopolítico Multipolar V4", layout="wide")

@st.cache_data(ttl=300)
def load_data():
    try:
        conn = sqlite3.connect("data/geopol.db")
        df = pd.read_sql("SELECT * FROM SITREP ORDER BY date DESC", conn)
        conn.close()
        df['date'] = pd.to_datetime(df['date'])
        return df
    except: return pd.DataFrame()

df = load_data()

# --- SIDEBAR: KPI MERCADOS ---
with st.sidebar:
    st.title("🎖️ COMMAND CENTER")
    if not df.empty:
        st.metric("VIX (PANIC)", f"{df['vix'].iloc[0]:.2f}", delta="ALERTA" if df['vix'].iloc[0] > 20 else "NORMAL")
        st.metric("BRENT CRUDE", f"${df['brent'].iloc[0]:.2f}")
        st.metric("DXY (USD)", f"{df['dxy'].iloc[0]:.2f}")
    st.divider()
    st.info("© 2024 M.Castillo\nmybloggingnotes@gmail.com")

# --- HEADER ---
st.title("🌍 SISTEMA DE INTELIGENCIA MULTIPOLAR (16 FUENTES)")

if df.empty:
    st.error("📡 Sin datos. Ejecuta harvester.py")
    st.stop()

# KPIs MULTIPOLARES
k1, k2, k3, k4 = st.columns(4)
k1.metric("INTEL CAPTURADA", len(df))
k2.metric("FUENTES ACTIVAS", df['fuente'].nunique())
# Índice de Polarización (Diferencia de sentimiento entre Bloques)
sent_west = df[df['bloque'] == "Occidente (G7)"]['sentiment_score'].mean()
sent_east = df[df['bloque'] == "Eurasia (RU/CH)"]['sentiment_score'].mean()
k3.metric("TENSIÓN OCCIDENTE", round(sent_west, 2))
k4.metric("TENSIÓN EURASIA", round(sent_east, 2))

st.divider()

t1, t2, t3, t4, t5 = st.tabs(["📊 Radar Geopolítico", "📡 Guerra de Narrativas", "💹 Correlación Mercados", "🗺 Mapa de Crisis", "📚 Directorio de Fuentes"])

with t1:
    fig = px.scatter(df, x="date", y="sentiment_score", size="impacto", color="bloque",
                     hover_name="titulo", height=600, template="plotly_dark",
                     title="Radar Multipolar: Hostilidad vs Impacto")
    st.plotly_chart(fig, use_container_width=True)

with t2:
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("### Sesgo Narrativo Detectado")
        st.plotly_chart(px.pie(df, names='narrativa', hole=0.4), use_container_width=True)
    with col_b:
        st.write("### Titulares por Bloque de Poder")
        st.dataframe(df[['bloque', 'titulo', 'fuente']].head(20), hide_index=True)

with t3:
    st.subheader("Correlación de Commodities y Riesgo")
    st.line_chart(df.set_index('date')[['brent', 'vix']])

with t4:
    m = folium.Map(location=[25, 45], zoom_start=3, tiles="CartoDB dark_matter")
    hotspots = {"Ormuz": [26, 56], "Bab el-Mandeb": [12, 43], "Taiwan": [23, 121], "Donbas": [48, 37], "Guyana": [6, -58]}
    for n, c in hotspots.items():
        folium.Marker(c, popup=n, icon=folium.Icon(color="red")).add_to(m)
    st_folium(m, width="100%", height=500)

with t5:
    st.subheader("Fuentes en Monitorización Activa")
    st.table(df.groupby('fuente').agg({'titulo': 'count', 'sentiment_score': 'mean'}).rename(columns={'titulo': 'Alertas', 'sentiment_score': 'Sesgo Promedio'}))
