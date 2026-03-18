import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

st.set_page_config(page_title="SITREP Geopolítico PRO", layout="wide")

@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv("data/geopol_data.csv")
        df['date'] = pd.to_datetime(df['date'])
        for col in ['brent_price', 'gold_price', 'sentiment_score', 'impacto']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df.sort_values(by='date', ascending=False)
    except: return pd.DataFrame()

df = load_data()

# --- DETECCIÓN DE ANOMALÍAS ---
def check_anomalies(df):
    if df.empty: return False, ""
    last_hour = df[df['date'] > (datetime.now() - timedelta(hours=1))]
    previous_period = df[(df['date'] <= (datetime.now() - timedelta(hours=1))) & 
                         (df['date'] > (datetime.now() - timedelta(hours=24)))]
    
    avg_hourly = len(previous_period) / 24
    if len(last_hour) > (avg_hourly * 1.5) and len(last_hour) > 5:
        return True, len(last_hour)
    return False, 0

anomaly_detected, anomaly_count = check_anomalies(df)

# --- SIDEBAR & COPYRIGHT ---
with st.sidebar:
    st.title("🎖️ SITREP Control")
    if anomaly_detected:
        st.error(f"⚠️ ANOMALÍA DETECTADA\n{anomaly_count} noticias en la última hora (Volumen crítico).")
    
    if not df.empty:
        st.metric("BRENT CRUDE", f"${df['brent_price'].iloc[0]}")
        st.metric("GOLD", f"${df['gold_price'].iloc[0]}")
    
    st.divider()
    st.markdown("### 🏛️ Copyright")
    st.info("© 2024 M.Castillo\n\n📧 mybloggingnotes@gmail.com")

# --- MAIN INTERFACE ---
st.title("🌍 DASHBOARD GEOPOLÍTICO Y ESTRATÉGICO")
if anomaly_detected:
    st.warning("🚨 ALERTA: Se ha detectado un pico de actividad informativa en los últimos 60 minutos.")

t1, t2, t3, t4, t5 = st.tabs(["📊 Análisis Poder", "💹 Mercados", "🗺 Mapa", "🧪 Metodología", "📖 Guía"])

with t1:
    c1, c2 = st.columns([2,1])
    with c1:
        fig = px.scatter(df, x="date", y="sentiment_score", size="impacto", color="bloque",
                         hover_name="titulo", title="Mapa de Hostilidad", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.write("### Desglose Narrativo")
        st.plotly_chart(px.pie(df, names='narrativa', hole=0.4), use_container_width=True)

with t2:
    st.subheader("Correlación Tensión vs Petróleo")
    df_m = df.set_index('date').resample('H').agg({'sentiment_score':'mean', 'brent_price':'last'}).dropna().reset_index()
    fig_m = go.Figure()
    fig_m.add_trace(go.Scatter(x=df_m['date'], y=df_m['brent_price'], name="Brent USD", line=dict(color="#00ff00")))
    fig_m.add_trace(go.Scatter(x=df_m['date'], y=df_m['sentiment_score'], name="Tensión", yaxis="y2", line=dict(color="#ff4b4b")))
    fig_m.update_layout(yaxis2=dict(overlaying="y", side="right"), template="plotly_dark")
    st.plotly_chart(fig_m, use_container_width=True)

with t3:
    m = folium.Map(location=[25, 45], zoom_start=3, tiles="CartoDB dark_matter")
    hotspots = {"Ormuz": [26, 56], "Taiwan": [23, 121], "Mar Rojo": [15, 42], "Suez": [30, 32]}
    for n, c in hotspots.items():
        folium.Marker(c, popup=n, icon=folium.Icon(color="red")).add_to(m)
    st_folium(m, width="100%", height=500)

with t4:
    st.write("### V-OSINT 3.0\nSistema de monitorización multipolar con detección de anomalías estadísticas y correlación de commodities.")

with t5:
    st.markdown("**Guía de Acrónimos**\n- **SITREP**: Situation Report.\n- **Anomaly**: Volumen de noticias > 150% de la media diaria.\n- **Sentiment**: Negativo indica hostilidad/conflicto.")
