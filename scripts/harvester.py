import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import os
import yfinance as yf
import sqlite3

DB_PATH = "/home/dietpi/geopol_dashboard/data/geopol.db"

# AMPLIACIÓN A 22 FUENTES (Más balanceado)
SOURCES = {
    # Occidente (G7)
    'Reuters': 'https://www.reutersagency.com/feed/?best-topics=world',
    'BBC World': 'https://feeds.bbci.co.uk/news/world/rss.xml',
    'DW News': 'https://rss.dw.com/rdf/rss-en-all',
    'France24': 'https://www.france24.com/en/rss',
    'Kyiv Independent': 'https://kyivindependent.com/feed/', 
    # Eurasia (RU/CH/IR)
    'TASS (Rusia)': 'https://tass.com/rss/v2.xml',
    'Sputnik': 'https://sputnikglobe.com/export/rss2/archive/index.xml',
    'RT News': 'https://www.rt.com/rss/news/',
    'Xinhua (China)': 'https://www.xinhuanet.com/english/rss/worldrss.xml',
    'Global Times (China)': 'https://www.globaltimes.cn/rss/world.xml',
    'SCMP (Hong Kong)': 'https://www.scmp.com/rss/91/feed',
    # MENA / Resistencia
    'Al Jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
    'PressTV (Irán)': 'https://www.presstv.ir/Default/RSS',
    'Tehran Times': 'https://www.tehrantimes.com/rss',
    'The Cradle': 'https://thecradle.co/feed',
    'TRT World': 'https://www.trtworld.com/rss/world',
    'Haaretz (Israel)': 'https://www.haaretz.com/cmlink/1.4621115',
    # Sur Global / Otros
    'The Hindu (India)': 'https://www.thehindu.com/news/international/feeder/default.rss',
    'Africanews': 'https://www.africanews.com/feed/rss',
    'MercoPress (LatAm)': 'https://en.mercopress.com/rss/',
    'ZeroHedge': 'https://feeds.feedburner.com/zerohedge/feed',
    'TOLOnews (Afganistán)': 'https://tolonews.com/rss/world'
}

def analyze_narrative(text):
    text = text.lower()
    if any(x in text for x in ['nato', 'biden', 'sanctions', 'aggression', 'invasion']): return "Pro-Occidente / Anti-Rusia"
    if any(x in text for x in ['imperialism', 'hegemony', 'resistance', 'genocide', 'axis']): return "Anti-Occidente / Soberanista"
    if any(x in text for x in ['multipolar', 'brics', 'expansion', 'de-dollarization']): return "Multipolarismo / BRICS+"
    if any(x in text for x in ['nuclear', 'missile', 'strike', 'war', 'escalation', 'red line']): return "Escalada Militar"
    return "Informativo Global"

def run():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Captura de Mercados Robusta (Brent, VIX, DXY)
    try:
        # Usamos periodo de 5 días para asegurar pillar el último cierre si es fin de semana
        assets = ["BZ=F", "^VIX", "DX-Y.NYB"]
        m_data = yf.download(assets, period="5d", interval="1d", progress=False)['Close']
        brent = float(m_data["BZ=F"].dropna().iloc[-1])
        vix = float(m_data["^VIX"].dropna().iloc[-1])
        dxy = float(m_data["DX-Y.NYB"].dropna().iloc[-1])
    except Exception as e:
        print(f"Error mercados: {e}")
        brent, vix, dxy = 0.0, 0.0, 0.0

    entries = []
    for name, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                sent = TextBlob(e.title).sentiment.polarity
                
                # Clasificación por Bloques
                if name in ['Reuters', 'BBC World', 'DW News', 'France24', 'Kyiv Independent']: bloque = "Occidente (G7)"
                elif name in ['TASS (Rusia)', 'Sputnik', 'RT News', 'Xinhua (China)', 'Global Times (China)', 'SCMP (Hong Kong)']: bloque = "Eurasia (RU/CH)"
                elif name in ['Al Jazeera', 'PressTV (Irán)', 'Tehran Times', 'The Cradle', 'TRT World', 'Haaretz (Israel)']: bloque = "MENA / Resistencia"
                else: bloque = "Sur Global / Otros"

                entries.append({
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'bloque': bloque,
                    'fuente': name,
                    'titulo': e.title,
                    'sentiment_score': float(sent),
                    'impacto': round(abs(sent) * 10, 1) + (5 if any(x in e.title.lower() for x in ['war', 'nuclear', 'attack', 'threat']) else 2),
                    'narrativa': analyze_narrative(e.title),
                    'brent': brent, 'vix': vix, 'dxy': dxy
                })
        except: continue
    
    if not entries: return

    df_new = pd.DataFrame(entries)
    conn = sqlite3.connect(DB_PATH)
    
    # Guardar noticias
    try:
        df_old = pd.read_sql("SELECT * FROM SITREP", conn)
        df_final = pd.concat([df_old, df_new]).drop_duplicates(subset=['titulo'])
        # Limitar a 5000 registros para no saturar la SD de la Odroid
        df_final.tail(5000).to_sql("SITREP", conn, if_exists="replace", index=False)
    except:
        df_new.to_sql("SITREP", conn, if_exists="replace", index=False)
    
    # Guardar Metadata de última actualización
    pd.DataFrame([{'last_run': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]).to_sql("METADATA", conn, if_exists="replace", index=False)
    
    conn.close()
    print(f"SITREP OK: {datetime.now()} - Brent: ${brent}")

if __name__ == "__main__":
    run()
