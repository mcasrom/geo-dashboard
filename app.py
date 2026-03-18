import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="SITREP Geopolítico PRO", layout="wide")

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

# --- SIDEBAR: INTELIGENCIA FINANCIERA ---
with st.sidebar:
    st.title("🕵️ SITREP Intelligence")
    if not df.empty:
        # Mostrar KPIs de mercado
        c_vix, c_dxy = st.columns(2)
        vix_val = df['vix'].iloc[0]
        dxy_val = df['dxy'].iloc[0]
        c_vix.metric("VIX (Pánico)", vix_val, delta="ALTO" if vix_val > 20 else "Normal")
        c_dxy.metric("DXY (Dólar)", dxy_val)
        st.metric("BRENT OIL", f"${df['brent'].iloc[0]}")
    
    st.divider()
    st.info("© 2024 M.Castillo\nmybloggingnotes@gmail.com")

# --- INTERFAZ PRINCIPAL ---
st.title("🛡️ DASHBOARD ESTRATÉGICO MULTIPOLAR")

if df.empty:
    st.warning("📡 No hay datos en la DB. Ejecuta harvester.py")
    st.stop()

t1, t2, t3, t4 = st.tabs(["📊 Análisis", "🗺 Mapa", "🧪 Metodología", "📖 Guía"])

with t1:
    col_l, col_r = st.columns([2,1])
    with col_l:
        # Gráfico Tensión vs Pánico (VIX)
        fig = px.scatter(df, x="date", y="sentiment_score", size="impacto", color="bloque",
                         hover_name="titulo", title="Mapa de Tensión vs Tiempo", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        st.write("### Top Alertas Hoy")
        st.dataframe(df[['titulo', 'impacto']].head(10), hide_index=True)

with t2:
    m = folium.Map(location=[25, 45], zoom_start=3, tiles="CartoDB dark_matter")
    hotspots = {"Ormuz": [26, 56], "Bab el-Mandeb": [12, 43], "Taiwan": [23, 121], "Suez": [30, 32]}
    for n, c in hotspots.items():
        folium.Marker(c, popup=n, icon=folium.Icon(color="red")).add_to(m)
    st_folium(m, width="100%", height=500)

with t3:
    st.markdown("### Metodología V-OSINT 3.5\n- **DB**: SQLite 3 Engine.\n- **Market**: Correlación con VIX (Miedo) y DXY (Fuerza USD).\n- **Hardware**: Optimizado para ARM Odroid-C2.")

with t4:
    st.markdown("**Acrónimos:**\n- **VIX**: Índice de volatilidad. >20 indica miedo en mercados.\n- **DXY**: Índice del dólar. Sube en crisis globales.")
