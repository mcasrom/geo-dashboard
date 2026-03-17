import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="SITREP Geopolítico", layout="wide")
st.title("🌍 Dashboard Geopolítico y Estratégico Global")

@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv("data/geopol_data.csv")
        df['date'] = pd.to_datetime(df['date'])
        return df
    except:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("📡 Esperando que el Odroid envíe los primeros datos...")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Volumen de Inteligencia", f"{len(df)} alertas")
col2.metric("Termómetro de Tensión", round(df['sentiment_score'].mean(), 2), "Negativo = Hostil")
col3.metric("Foco de Conflicto", df['tema'].mode()[0])

st.divider()

tab1, tab2 = st.tabs(["📊 Narrativas por Bloque", "🗺️ Chokepoints Marítimos"])

with tab1:
    df_bloques = df.groupby(['bloque', 'tema'])['sentiment_score'].mean().reset_index()
    fig = px.bar(df_bloques, x="bloque", y="sentiment_score", color="tema", barmode="group", title="Hostilidad vs Afinidad")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    m = folium.Map(location=[25, 45], zoom_start=4, tiles="CartoDB dark_matter")
    chokepoints = [
        {"name": "Estrecho de Ormuz", "coords":[26.56, 56.25]},
        {"name": "Bab el-Mandeb", "coords": [12.58, 43.33]},
        {"name": "Canal de Suez", "coords": [30.6, 32.35]}
    ]
    for pt in chokepoints:
        folium.Marker(location=pt["coords"], popup=pt["name"], icon=folium.Icon(color="red")).add_to(m)
    st_folium(m, width=1200, height=500)
