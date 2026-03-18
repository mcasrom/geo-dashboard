import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="SITREP Geopolítico Multipolar V5.1", layout="wide", page_icon="📡")

# Estilo para mejorar visibilidad en Odroid
st.markdown("""<style>
    .stMetric { background: #1c212d; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    [data-testid="stSidebar"] { background-color: #0e1117; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = sqlite3.connect("data/geopol.db")
        df = pd.read_sql("SELECT * FROM SITREP ORDER BY date DESC", conn)
        # Intentar cargar timestamp de última actualización
        try:
            meta = pd.read_sql("SELECT last_run FROM METADATA", conn)
            last_ts = meta['last_run'].iloc[0]
        except:
            last_ts = "No disponible"
        conn.close()
        
        df['date'] = pd.to_datetime(df['date'])
        numeric_cols = ['sentiment_score', 'impacto', 'brent', 'vix', 'dxy']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        return df, last_ts
    except:
        return pd.DataFrame(), "Error de conexión"

df, last_update = load_data()

# --- SIDEBAR (Copyright & Markets) ---
with st.sidebar:
    st.title("🎖️ COMMAND CENTER")
    st.write(f"**Última actualización:**\n`{last_update}`")
    
    if not df.empty:
        # Recuperamos el último valor válido (no cero)
        brent_val = df[df['brent'] > 0]['brent'].iloc[0] if not df[df['brent'] > 0].empty else 0.0
        vix_val = df[df['vix'] > 0]['vix'].iloc[0] if not df[df['vix'] > 0].empty else 0.0
        dxy_val = df[df['dxy'] > 0]['dxy'].iloc[0] if not df[df['dxy'] > 0].empty else 0.0
        
        st.metric("BRENT CRUDE", f"${brent_val:.2f}")
        st.metric("VIX (PANIC INDEX)", f"{vix_val:.2f}", 
                  delta="ALERTA" if vix_val > 20 else "ESTABLE", delta_color="inverse")
        st.metric("DXY (USD INDEX)", f"{dxy_val:.2f}")
    
    st.divider()
    st.info("© 2024 M.Castillo\n\n📧 mybloggingnotes@gmail.com")
    st.caption("Odroid-C2 Intelligence Unit")

# --- HEADER ---
st.title("🌍 INTELIGENCIA ESTRATÉGICA GLOBAL")
st.write(f"Monitorizando activamente el equilibrio de poder multipolar.")

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

# --- TABS (Restaurados y Mejorados) ---
t1, t2, t3, t4, t5, t6 = st.tabs([
    "📊 Radar Geopolítico", 
    "📡 Guerra de Narrativas", 
    "💹 Mercados", 
    "🗺 Mapa de Crisis", 
    "📚 Directorio de Fuentes",
    "🛠 Metodología"
])

with t1:
    fig = px.scatter(df.head(300), x="date", y="sentiment_score", size="impacto", color="bloque",
                     hover_name="titulo", height=600, template="plotly_dark",
                     color_discrete_map={
                         'Occidente (G7)':'#3498db',
                         'Eurasia (RU/CH)':'#e74c3c',
                         'MENA / Resistencia':'#f1c40f',
                         'Sur Global / Otros':'#2ecc71'
                     })
    st.plotly_chart(fig, use_container_width=True)

with t2:
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.plotly_chart(px.pie(df, names='narrativa', hole=0.4, title="Sesgo Narrativo Global"), use_container_width=True)
    with col_b:
        st.write("### Últimos Despliegues de Mensaje")
        st.dataframe(df[['bloque', 'titulo', 'fuente']].head(20), hide_index=True)

with t3:
    st.subheader("Análisis de Riesgo Financiero Geopolítico")
    st.line_chart(df.set_index('date')[['brent', 'vix']])
    st.caption("Nota: El Brent se captura de los últimos 5 días de trading para evitar valores en cero.")

with t4:
    m = folium.Map(location=[25, 45], zoom_start=3, tiles="CartoDB dark_matter")
    hotspots = {
        "Estrecho de Ormuz": [26, 56], "Bab el-Mandeb": [12, 43], 
        "Taiwán": [23, 121], "Donbás": [48, 37], "Esequibo": [6.7, -58.9]
    }
    for n, c in hotspots.items():
        folium.Marker(c, popup=n, icon=folium.Icon(color="red", icon="warning-sign")).add_to(m)
    st_folium(m, width="100%", height=500)

with t5:
    st.subheader("Directorio de Monitorización")
    source_stats = df.groupby(['fuente', 'bloque']).agg({'titulo': 'count', 'sentiment_score': 'mean'}).sort_values(by='titulo', ascending=False)
    st.table(source_stats.rename(columns={'titulo': 'Alertas', 'sentiment_score': 'Sesgo Promedio'}))

with t6:
    st.header("Metodología de Inteligencia (V 5.1)")
    st.markdown("""
    **1. Ingesta Multipolar:** Recolección de 22 fuentes de noticias categorizadas por bloques geopolíticos.
    **2. Análisis de Sentimiento (NLP):** Uso de `TextBlob` para calcular la polaridad de los titulares (-1 a 1).
    **3. Clasificación Narrativa:**
    - **Pro-Occidente:** Enfoque en sanciones, OTAN y retórica del G7.
    - **Anti-Occidente / Soberanista:** Enfoque en hegemonía, resistencia y soberanía.
    - **Multipolarismo / BRICS+:** Cooperación fuera del eje dólar.
    - **Escalada Militar:** Alertas de despliegue, pruebas nucleares y conflicto directo.
    **4. Correlación de Mercados:** Sincronización de eventos geopolíticos con el precio del petróleo (Brent) y el índice de pánico (VIX).
    """)
