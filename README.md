# SITREP Geopolítico Multipolar - Odroid-C2
**Autor:** M.Castillo (mybloggingnotes@gmail.com)
**Estado:** V 2.8.2 Funcional.

## Estructura de Archivos
- `app.py`: Dashboard Streamlit con 5 tabs (Análisis, Narrativas, Mapa, Metodología, Guía).
- `scripts/harvester.py`: Motor de ingesta RSS (Reuters, TASS, SCMP, Al Jazeera, PressTV) con análisis de sentimiento NLP (TextBlob).
- `data/geopol_data.csv`: Base de datos de inteligencia (date, bloque, tema, sentiment_score, impacto, fuente, titulo, narrativa).
- `update_repo.sh`: Script de automatización para recolección y sincronización con GitHub.
- `venv/`: Entorno virtual Python 3.13.

## Dependencias Críticas
- streamlit, pandas, plotly, folium, streamlit-folium, feedparser, textblob.
- Corporas NLTK de TextBlob instalados.

## Lógica de Clasificación
- **Bloques:** Occidente, Eurasia, MENA/Irán, Global South.
- **Narrativas:** Anti-Occidente, Anti-Rusia, Anti-China, Pro-X, Eje Resistencia.
