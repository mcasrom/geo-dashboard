import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="SITREP Geopolítico Multipolar V5.1", layout="wide", page_icon="📡")

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = sqlite3.connect("data/geopol.db")
        df = pd.read_sql("SELECT * FROM SITREP ORDER BY date DESC", conn)
        try:
            meta = pd.read_sql("SELECT last_run FROM METADATA", conn)
            last_ts = meta['last_run'].iloc[0]
        except:
            last_ts = "Pendiente"
        conn.close()
        
        # Limpieza forzosa
        numeric_cols = ['sentiment_score', 'impacto', 'brent', 'vix', 'dxy']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        df['date'] = pd.to_datetime(df['date'])
        return df, last_ts
    except:
        return pd.DataFrame(), "Sin conexión"

df, last_update = load_data()

# --- SIDEBAR (Copyright & Markets) ---
with st.sidebar:
    st.title("🎖️ COMMAND CENTER")
    st.write(f"**Última Actualización:**\n`{last_update}`")
    
    if not df.empty:
        # Buscamos el último valor que no sea 0.0 para mostrar en métricas
        b_val = df[df['brent'] > 0]['brent'].iloc[0] if not df[df['brent'] > 0].empty else 0.0
        v_val = df[df['vix'] > 0]['vix'].iloc[0] if not df[df['vix'] > 0].empty else 0.0
        d_val = df[df['dxy'] > 0]['dxy'].iloc[0] if not df[df['dxy'] > 0].empty else 0.0
        
        st.metric("BRENT CRUDE", f"${b_val:.2f}")
        st.metric("VIX (PANIC INDEX)", f"{v_val:.2f}", 
                  delta="ALERTA" if v_val > 20 else "ESTABLE", delta_color="inverse")
        st.metric("DXY (USD INDEX)", f"{d_val:.2f}")
    
    st.divider()
    st.info("© 2024 M.Castillo\n\n📧 mybloggingnotes@gmail.com")
    st.caption("Odroid-C2 Intelligence Unit")

# --- HEADER ---
st.title("🌍 INTELIGENCIA ESTRATÉGICA GLOBAL")

if df.empty:
    st.error("📡 Sin datos en la DB. Ejecuta harvester.py.")
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

# --- TABS (Todos restaurados) ---
t1, t2, t3, t4, t5, t6 = st.tabs(["📊 Radar", "📡 Narrativas", "💹 Mercados", "🗺 Mapa", "📚 Fuentes", "🛠 Metodología"])

with t1:
    fig = px.scatter(df.head(400), x="date", y="sentiment_score", size="impacto", color="bloque",
                     hover_name="titulo", height=600, template="plotly_dark",
                     color_discrete_map={'Occidente (G7)':'#3498db','Eurasia (RU/CH)':'#e74c3c','MENA / Resistencia':'#f1c40f','Sur Global / Otros':'#2ecc71'})
    st.plotly_chart(fig, use_container_width=True)

with t2:
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.plotly_chart(px.pie(df, names='narrativa', hole=0.4, title="Sesgo Narrativo Global"), use_container_width=True)
    with col_b:
        st.write("### Últimas Alertas Analizadas")
        st.dataframe(df[['bloque', 'titulo', 'fuente']].head(20), hide_index=True)

with t3:
    st.subheader("Riesgo Geopolítico y Commodities")
    st.line_chart(df.set_index('date')[['brent', 'vix']])

with t4:
    m = folium.Map(location=[25, 45], zoom_start=3, tiles="CartoDB dark_matter")
    hotspots = {"Ormuz": [26, 56], "Bab el-Mandeb": [12, 43], "Taiwán": [23, 121], "Donbás": [48, 37], "Esequibo": [6.7, -58.9]}
    for n, c in hotspots.items():
        folium.Marker(c, popup=n, icon=folium.Icon(color="red", icon="warning-sign")).add_to(m)
    st_folium(m, width="100%", height=500)

with t5:
    st.subheader("Directorio de Monitorización Activa")
    source_stats = df.groupby('fuente').agg({'titulo': 'count', 'sentiment_score': 'mean'}).sort_values(by='titulo', ascending=False)
    st.table(source_stats.rename(columns={'titulo': 'Alertas', 'sentiment_score': 'Sesgo (Sentiment)'}))

with t6:
    st.header("Metodología SITREP Geopolítico")
    st.markdown("""
    1. **Ingesta:** Monitorización de 22 fuentes RSS globales cada hora.
    2. **Análisis Sentiment:** Procesamiento de lenguaje natural (NLP) con `TextBlob`.
    3. **Categorización:** Clasificación automática de bloques según la fuente y palabras clave.
    4. **Persistencia:** Almacenamiento en base de datos SQLite con protección de históricos de mercados.
    """)
