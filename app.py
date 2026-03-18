import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="SITREP Geopolítico V6", layout="wide", page_icon="📡")

# Estilo visual de terminal
st.markdown("""<style>
    .stMetric { background: #1c212d; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .stAlert { background: #1c212d; border: 1px solid #e74c3c; }
</style>""", unsafe_allow_html=True)

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
        
        for col in ['sentiment_score', 'impacto', 'brent', 'vix', 'dxy']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        df['date'] = pd.to_datetime(df['date'])
        return df, last_ts
    except:
        return pd.DataFrame(), "Sin conexión"

df, last_update = load_data()

# --- SIDEBAR (Intel Room) ---
with st.sidebar:
    st.title("🎖️ INTEL COMMAND")
    st.write(f"**Sincronización:**\n`{last_update}`")
    
    if not df.empty:
        b_val = df[df['brent'] > 0]['brent'].iloc[0] if not df[df['brent'] > 0].empty else 0.0
        v_val = df[df['vix'] > 0]['vix'].iloc[0] if not df[df['vix'] > 0].empty else 0.0
        
        st.metric("BRENT CRUDE", f"${b_val:.2f}")
        st.metric("VIX PANIC", f"{v_val:.2f}", delta="TENSIÓN" if v_val > 20 else "ESTABLE", delta_color="inverse")
    
    st.divider()
    st.subheader("⚠️ ALERTA DE IMPACTO")
    # Mostrar las 3 noticias con más impacto del día
    top_news = df.sort_values(by='impacto', ascending=False).head(3)
    for i, row in top_news.iterrows():
        st.caption(f"**{row['fuente']}**: {row['titulo'][:60]}...")
        st.progress(min(row['impacto']/20, 1.0))

    st.divider()
    st.info("© 2024 M.Castillo | V 6.0")
    st.caption("Intelligence Unit - Odroid-C2")

# --- HEADER ---
st.title("🌍 SITREP GEOPOLÍTICO MULTIPOLAR")

if df.empty:
    st.error("📡 DB Vacía. Ejecuta harvester.py.")
    st.stop()

# --- KPIs DINÁMICOS ---
k1, k2, k3, k4 = st.columns(4)
k1.metric("INTEL CAPTURADA", len(df))
k2.metric("FUENTES ACTIVAS", df['fuente'].nunique())

# Cálculo de Diferencial de Guerra Fría
sent_west = df[df['bloque'] == "Occidente (G7)"]['sentiment_score'].mean()
sent_east = df[df['bloque'] == "Eurasia (RU/CH)"]['sentiment_score'].mean()
gap = abs(sent_west - sent_east)

k3.metric("DIFERENCIAL BLOQUES", f"{gap:.2f}", delta="AMPLIÁNDOSE" if gap > 0.5 else "ESTABLE")
k4.metric("VOLATILIDAD BRENT", f"{df['brent'].std():.2f}")

st.divider()

# --- TABS ---
t1, t2, t3, t4, t5, t6 = st.tabs(["📊 Radar", "📡 Narrativas", "💹 Mercados", "🗺 Mapa", "📚 Fuentes", "🛠 Metodología"])

with t1:
    fig = px.scatter(df.head(500), x="date", y="sentiment_score", size="impacto", color="bloque",
                     hover_name="titulo", height=600, template="plotly_dark",
                     title="Radar de Eventos (Eje X: Tiempo | Eje Y: Sentimiento | Tamaño: Impacto)",
                     color_discrete_map={'Occidente (G7)':'#3498db','Eurasia (RU/CH)':'#e74c3c','MENA / Resistencia':'#f1c40f','Sur Global / Otros':'#2ecc71'})
    st.plotly_chart(fig, use_container_width=True)

with t2:
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.plotly_chart(px.pie(df, names='narrativa', hole=0.4, title="Dominio Narrativo"), use_container_width=True)
    with col_b:
        st.write("### 🗞️ Últimos Cables Analizados")
        st.dataframe(df[['date', 'bloque', 'fuente', 'titulo', 'impacto']].head(25), hide_index=True)

with t3:
    st.subheader("Correlación Geopolítica-Financiera")
    st.line_chart(df.set_index('date')[['brent', 'vix', 'dxy']])

with t4:
    m = folium.Map(location=[25, 45], zoom_start=3, tiles="CartoDB dark_matter")
    hotspots = {"Ormuz": [26, 56], "Bab el-Mandeb": [12, 43], "Taiwán": [23, 121], "Donbás": [48, 37], "Esequibo": [6.7, -58.9]}
    for n, c in hotspots.items():
        folium.Marker(c, popup=n, icon=folium.Icon(color="red", icon="warning-sign")).add_to(m)
    st_folium(m, width="100%", height=500)

with t5:
    st.subheader("Balance de Cobertura por Fuente")
    source_stats = df.groupby(['fuente', 'bloque']).agg({'titulo': 'count', 'sentiment_score': 'mean', 'impacto': 'mean'}).sort_values(by='titulo', ascending=False)
    st.table(source_stats.rename(columns={'titulo': 'Cables', 'sentiment_score': 'Sesgo', 'impacto': 'Impacto Promedio'}))

with t6:
    st.header("Metodología SITREP V 6.0")
    st.markdown("""
    **1. Ingesta:** Monitorización de 22 agencias internacionales (Visión 360°).
    **2. Impacto Ponderado:** El sistema identifica palabras clave (Nuclear, War, BRICS) y ajusta la relevancia del evento automáticamente.
    **3. Análisis de Sesgo:** NLP vía TextBlob para determinar la carga emocional del titular.
    **4. Persistencia:** Base de datos SQLite optimizada con `VACUUM` para hardware embebido (Odroid-C2).
    """)
