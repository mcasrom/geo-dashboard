import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime

# --- CONFIGURACIÓN PRO ---
st.set_page_config(page_title="SITREP Geopolítico Multipolar", layout="wide")

# --- CARGA DE DATOS (Recuperando todas las columnas) ---
@st.cache_data(ttl=300)
def load_data():
    try:
        conn = sqlite3.connect("data/geopol.db")
        # Forzamos la lectura de todas las columnas que el Harvester debería estar guardando
        df = pd.read_sql("SELECT * FROM SITREP ORDER BY date DESC", conn)
        conn.close()
        
        # Limpieza de nulos y tipos
        numeric_cols = ['sentiment_score', 'impacto', 'brent', 'vix', 'dxy']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        df['date'] = pd.to_datetime(df['date'])
        # Aseguramos columnas de texto
        text_cols = ['bloque', 'fuente', 'titulo', 'narrativa', 'tema']
        for col in text_cols:
            if col not in df.columns: df[col] = "N/A"
            df[col] = df[col].fillna("N/A")
            
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- SIDEBAR ESTRATÉGICO ---
with st.sidebar:
    st.title("🎖️ SITREP COMMAND")
    if not df.empty:
        st.metric("VIX (PANIC INDEX)", f"{df['vix'].iloc[0]:.2f}", 
                  delta="ALTO" if df['vix'].iloc[0] > 20 else "NORMAL", delta_color="inverse")
        st.metric("BRENT OIL", f"${df['brent'].iloc[0]:.2f}")
        st.metric("DXY (USD INDEX)", f"{df['dxy'].iloc[0]:.2f}")
        st.caption(f"Last Intel: {df['date'].max().strftime('%H:%M:%S')}")
    
    st.divider()
    st.markdown("### 🏛️ Propiedad")
    st.info("© 2024 M.Castillo\n\n📧 mybloggingnotes@gmail.com")
    st.caption("Odroid-C2 Intelligence Unit v3.8")

# --- MAIN DASHBOARD ---
st.title("🌍 SISTEMA DE INTELIGENCIA ESTRATÉGICA GLOBAL")

if df.empty:
    st.error("📡 Sin datos en la base de datos SQL. Ejecuta harvester.py")
    st.stop()

# --- KPIs DE CABECERA ---
k1, k2, k3, k4 = st.columns(4)
k1.metric("INTEL TOTAL", len(df))
k2.metric("POLO DOMINANTE", df['bloque'].mode()[0])
k3.metric("NARRATIVA CLAVE", df['narrativa'].mode()[0] if 'narrativa' in df.columns else "N/A")
k4.metric("FUENTES ACTIVAS", df['fuente'].nunique())

st.divider()

# --- NAVEGACIÓN DE 6 PESTAÑAS ---
t1, t2, t3, t4, t5, t6 = st.tabs([
    "📊 Análisis Poder", 
    "📡 Info-Warfare", 
    "💹 Mercados", 
    "🗺 Mapa Crisis", 
    "📚 Fuentes & Data",
    "🧪 Metodología"
])

with t1:
    st.subheader("Mapa de Hostilidad por Bloques Geopolíticos")
    fig = px.scatter(df, x="date", y="sentiment_score", size="impacto", color="bloque",
                     hover_name="titulo", height=500,
                     color_discrete_map={'Occidente':'#3498db','Eurasia':'#e74c3c','MENA':'#f1c40f','Otros':'#95a5a6'},
                     template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with t2:
    st.subheader("Guerra de Narrativas y Campañas")
    c_n1, c_n2 = st.columns(2)
    with c_n1:
        narr_counts = df['narrativa'].value_counts()
        st.plotly_chart(px.bar(narr_counts, title="Detección de Sesgo en Tiempo Real", orientation='h'), use_container_width=True)
    with c_n2:
        st.write("### Despliegue de Mensajes Críticos")
        st.dataframe(df[df['impacto'] > 6][['bloque', 'titulo', 'fuente']].head(12), hide_index=True)

with t3:
    st.subheader("Correlación: Tensión Geopolítica vs Mercados")
    # Agrupamos por hora para el gráfico de líneas
    df_m = df.set_index('date').resample('H').agg({'sentiment_score':'mean', 'brent':'last'}).dropna().reset_index()
    fig_m = go.Figure()
    fig_m.add_trace(go.Scatter(x=df_m['date'], y=df_m['brent'], name="Brent Oil", line=dict(color="#00ff00", width=3)))
    fig_m.add_trace(go.Scatter(x=df_m['date'], y=df_m['sentiment_score'], name="Tensión", yaxis="y2", line=dict(color="#ff4b4b", dash='dot')))
    fig_m.update_layout(yaxis2=dict(overlaying="y", side="right"), template="plotly_dark", height=500)
    st.plotly_chart(fig_m, use_container_width=True)

with t4:
    st.subheader("Vigilancia de Chokepoints Marítimos")
    m = folium.Map(location=[20, 50], zoom_start=3, tiles="CartoDB dark_matter")
    hotspots = {"Ormuz": [26.5, 56.2], "Taiwán": [23.5, 121.0], "Suez": [30.6, 32.3], "Bab el-Mandeb": [12.6, 43.3]}
    for name, coords in hotspots.items():
        folium.Marker(coords, popup=name, icon=folium.Icon(color="red", icon="tower")).add_to(m)
    st_folium(m, width="100%", height=500)

with t5:
    st.subheader("Inspección de Inteligencia (Raw Data)")
    st.write("Explora las fuentes detectadas por el Odroid-C2:")
    col_src, col_raw = st.columns([1,3])
    with col_src:
        st.write("**Ranking de Fuentes**")
        st.write(df['fuente'].value_counts())
    with col_raw:
        st.write("**Últimas 50 entradas capturadas**")
        st.dataframe(df[['date', 'fuente', 'bloque', 'titulo', 'sentiment_score']].head(50), use_container_width=True)

with t6:
    st.markdown("""
    ### 🛡️ Metodología V-OSINT 3.8 (Odroid Optimized)
    1. **Agregación**: Monitorización de 5 ejes multipolares mediante RSS.
    2. **NLP (Sentiment)**: Polaridad calculada con `TextBlob` sobre titulares traducidos al vuelo.
    3. **Correlación de Mercado**: Ingesta de tickers `BZ=F`, `^VIX`, `DX-Y.NYB` mediante `yfinance`.
    4. **Persistencia**: Motor SQLite3 con desduplicación por título para evitar ruido informativo.
    """)
    st.info("Desplegado en DietPi Linux | Arquitectura ARMv7")
