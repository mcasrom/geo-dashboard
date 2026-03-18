import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime

st.set_page_config(page_title="WAR ROOM - Intel Terminal", layout="wide")

# --- CARGA DE DATOS ---
def load_intel():
    conn = sqlite3.connect("data/geopol.db")
    df = pd.read_sql("SELECT * FROM SITREP ORDER BY date DESC", conn)
    conn.close()
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_intel()

# --- SIDEBAR (Estado de Alerta) ---
with st.sidebar:
    st.title("🎖️ STRATEGIC STATUS")
    if not df.empty:
        vix = df['vix'].iloc[0]
        # Cálculo de Escalada: Frecuencia de noticias de alto impacto en las últimas 12h
        high_impact = df[df['impacto'] > 12]
        escalation_score = len(high_impact) / 10 # Ratio de crisis
        
        st.metric("ÍNDICE DE ESCALADA", f"{escalation_score:.1f}", 
                  delta="CRÍTICO" if escalation_score > 1.5 else "BAJO", delta_color="inverse")
        
        st.divider()
        st.write("**Resumen de Mercados:**")
        st.metric("BRENT", f"${df['brent'].iloc[0]:.2f}")
        st.metric("VIX (FEAR)", f"{vix:.2f}")

# --- PANTALLA PRINCIPAL ---
st.title("📡 TERMINAL DE INTELIGENCIA ESTRATÉGICA")

tabs = st.tabs(["🔥 WAR ROOM", "💹 CORRELACIÓN", "📊 RADAR", "📚 ARCHIVO"])

with tabs[0]:
    st.subheader("📍 Síntesis por Teatros de Crisis")
    col1, col2 = st.columns(2)
    
    # Agrupación por Teatros para la síntesis
    theatres = df['theatre'].unique()
    for i, t in enumerate(theatres):
        with col1 if i % 2 == 0 else col2:
            t_data = df[df['theatre'] == t].head(5)
            avg_impact = t_data['impacto'].mean()
            
            with st.expander(f"🎭 {t.upper()} (Impacto: {avg_impact:.1f})", expanded=avg_impact > 10):
                for _, row in t_data.iterrows():
                    color = "🔴" if row['impacto'] > 12 else "🟡"
                    st.write(f"{color} **{row['fuente']}**: {row['titulo']}")
                
                if t == "Suministro Energético" and avg_impact > 10:
                    st.error("⚠️ CONCLUSIÓN: Alta probabilidad de presión alcista en el crudo por eventos en cuellos de botella.")

with tabs[1]:
    st.subheader("📈 Correlación Eventos vs Precios")
    st.write("Este gráfico muestra cómo las noticias de alto impacto coinciden con movimientos del Brent.")
    fig = px.scatter(df.head(200), x="brent", y="impacto", color="theatre", 
                     size="impacto", hover_name="titulo", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    # El radar clásico pero optimizado
    fig_radar = px.scatter(df.head(300), x="date", y="sentiment_score", size="impacto", color="theatre",
                           height=600, template="plotly_dark")
    st.plotly_chart(fig_radar, use_container_width=True)

with tabs[3]:
    st.dataframe(df[['date', 'fuente', 'theatre', 'titulo', 'impacto']], use_container_width=True)

st.caption("© 2024 M.Castillo | V 7.0 Intel Correlacional | Odroid-C2 Deploy")
