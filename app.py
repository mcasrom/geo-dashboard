import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="WAR ROOM - Intel Terminal V7.1", layout="wide", page_icon="📡")

# Estilo visual de terminal
st.markdown("""<style>
    .stMetric { background: #1c212d; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .stExpander { border: 1px solid #30363d; background: #0e1117; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = sqlite3.connect("data/geopol.db")
        df = pd.read_sql("SELECT * FROM SITREP ORDER BY date DESC", conn)
        meta = pd.read_sql("SELECT last_run FROM METADATA", conn)
        conn.close()
        
        # --- LIMPIEZA ANTI-CRASH (Crucial) ---
        df['theatre'] = df['theatre'].fillna("Global / Otros").astype(str)
        for col in ['sentiment_score', 'impacto', 'brent', 'vix']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        df['date'] = pd.to_datetime(df['date'])
        return df, meta['last_run'].iloc[0]
    except:
        return pd.DataFrame(), "Pendiente"

df, last_update = load_data()

# --- SIDEBAR (Copyright & Intel Status) ---
with st.sidebar:
    st.title("🎖️ INTEL COMMAND")
    st.write(f"**Sincronización:**\n`{last_update}`")
    
    if not df.empty:
        b_val = df[df['brent'] > 0]['brent'].iloc[0] if not df[df['brent'] > 0].empty else 0.0
        v_val = df[df['vix'] > 0]['vix'].iloc[0] if not df[df['vix'] > 0].empty else 0.0
        
        st.metric("BRENT CRUDE", f"${b_val:.2f}")
        st.metric("VIX (FEAR INDEX)", f"{v_val:.2f}", delta="ALERTA" if v_val > 20 else "ESTABLE", delta_color="inverse")
    
    st.divider()
    st.info("© 2024 M.Castillo\n\n📧 mybloggingnotes@gmail.com")
    st.caption("Intelligence Unit - Odroid-C2")

# --- HEADER ---
st.title("🌍 SITREP GEOPOLÍTICO MULTIPOLAR")

if df.empty:
    st.error("📡 DB Vacía. Ejecuta harvester.py.")
    st.stop()

# KPIs Superiores
k1, k2, k3, k4 = st.columns(4)
k1.metric("INTEL CAPTURADA", len(df))
k2.metric("FUENTES ACTIVAS", df['fuente'].nunique())
escalation = len(df[df['impacto'] > 12]) / 10
k3.metric("RIESGO ESCALADA", f"{escalation:.1f}", delta="ALTO" if escalation > 1 else "BAJO", delta_color="inverse")
k4.metric("VOLATILIDAD BRENT", f"{df['brent'].std():.2f}")

st.divider()

# --- TABS ---
t_war, t_radar, t_merc, t_map, t_met = st.tabs(["🔥 WAR ROOM", "📊 Radar", "💹 Mercados", "🗺 Mapa", "🛠 Metodología"])

with t_war:
    st.subheader("📍 Síntesis por Teatros de Operaciones")
    col_a, col_b = st.columns(2)
    
    # Agrupación por teatros con protección de tipos
    theatres_list = [t for t in df['theatre'].unique() if t]
    for i, t in enumerate(theatres_list):
        with col_a if i % 2 == 0 else col_b:
            t_data = df[df['theatre'] == t].head(5)
            avg_impact = t_data['impacto'].mean()
            
            # str(t).upper() previene el error AttributeError
            with st.expander(f"🎭 {str(t).upper()} (Impacto: {avg_impact:.1f})", expanded=avg_impact > 10):
                for _, row in t_data.iterrows():
                    st.write(f"- **{row['fuente']}**: {row['titulo']}")

with t_radar:
    fig = px.scatter(df.head(400), x="date", y="sentiment_score", size="impacto", color="theatre",
                     hover_name="titulo", height=600, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with t_merc:
    st.subheader("Correlación Brent vs Pánico (VIX)")
    st.line_chart(df.set_index('date')[['brent', 'vix']])

with t_map:
    m = folium.Map(location=[25, 45], zoom_start=3, tiles="CartoDB dark_matter")
    hotspots = {"Ormuz": [26, 56], "Bab el-Mandeb": [12, 43], "Taiwán": [23, 121], "Donbás": [48, 37]}
    for n, c in hotspots.items():
        folium.Marker(c, popup=n, icon=folium.Icon(color="red", icon="warning-sign")).add_to(m)
    st_folium(m, width="100%", height=500)

with t_met:
    st.header("Metodología de Inteligencia V 7.1")
    st.markdown("""
    - **Teatros de Operaciones:** Clasificación automática por palabras clave en 22 fuentes.
    - **Cálculo de Impacto:** Polaridad NLP + Bonificación por términos de combate (Attack, Strike, Missile).
    - **Correlación:** Cruce de eventos en tiempo real con precios de commodities (Yahoo Finance).
    - **Persistencia:** Base de datos SQLite optimizada para Odroid-C2.
    """)
