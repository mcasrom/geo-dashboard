import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import os
import yfinance as yf
import sqlite3

DB_PATH = "/home/dietpi/geopol_dashboard/data/geopol.db"

# 22 FUENTES PARA UNA VISIÓN MULTIPOLAR REAL
SOURCES = {
    'Reuters': 'https://www.reutersagency.com/feed/?best-topics=world',
    'BBC World': 'https://feeds.bbci.co.uk/news/world/rss.xml',
    'DW News': 'https://rss.dw.com/rdf/rss-en-all',
    'France24': 'https://www.france24.com/en/rss',
    'Kyiv Independent': 'https://kyivindependent.com/feed/',
    'TASS (Rusia)': 'https://tass.com/rss/v2.xml',
    'Sputnik': 'https://sputnikglobe.com/export/rss2/archive/index.xml',
    'RT News': 'https://www.rt.com/rss/news/',
    'Xinhua (China)': 'https://www.xinhuanet.com/english/rss/worldrss.xml',
    'Global Times (China)': 'https://www.globaltimes.cn/rss/world.xml',
    'SCMP (Hong Kong)': 'https://www.scmp.com/rss/91/feed',
    'Al Jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
    'PressTV (Irán)': 'https://www.presstv.ir/Default/RSS',
    'Tehran Times': 'https://www.tehrantimes.com/rss',
    'The Cradle': 'https://thecradle.co/feed',
    'TRT World': 'https://www.trtworld.com/rss/world',
    'Haaretz (Israel)': 'https://www.haaretz.com/cmlink/1.4621115',
    'The Hindu (India)': 'https://www.thehindu.com/news/international/feeder/default.rss',
    'Africanews': 'https://www.africanews.com/feed/rss',
    'MercoPress (LatAm)': 'https://en.mercopress.com/rss/',
    'ZeroHedge': 'https://feeds.feedburner.com/zerohedge/feed',
    'TOLOnews (Afganistán)': 'https://tolonews.com/rss/world'
}

def analyze_narrative(text):
    text = text.lower()
    if any(x in text for x in ['nato', 'biden', 'sanctions', 'aggression']): return "Pro-Occidente / Anti-Rusia"
    if any(x in text for x in ['imperialism', 'hegemony', 'resistance', 'genocide']): return "Anti-Occidente / Soberanista"
    if any(x in text for x in ['multipolar', 'brics', 'global south', 'de-dollarization']): return "Multipolarismo"
    if any(x in text for x in ['nuclear', 'missile', 'strike', 'war', 'escalation']): return "Escalada Militar"
    return "Informativo Global"

def run():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # --- PERSISTENCIA DE MERCADOS (Evitar el 0.0) ---
    # Intentamos cargar valores previos por si falla la descarga nueva
    try:
        conn_pre = sqlite3.connect(DB_PATH)
        last_row = pd.read_sql("SELECT brent, vix, dxy FROM SITREP ORDER BY date DESC LIMIT 1", conn_pre)
        conn_pre.close()
        brent, vix, dxy = float(last_row['brent'].iloc[0]), float(last_row['vix'].iloc[0]), float(last_row['dxy'].iloc[0])
    except:
        brent, vix, dxy = 80.0, 15.0, 103.0 # Valores base si la DB está vacía

    # Actualización individual por activo (Si uno falla, los otros siguen)
    assets = {"BZ=F": "brent", "^VIX": "vix", "DX-Y.NYB": "dxy"}
    for ticker, name in assets.items():
        try:
            m_data = yf.download(ticker, period="5d", interval="1d", progress=False)
            if not m_data.empty:
                val = float(m_data['Close'].dropna().iloc[-1])
                if name == "brent": brent = val
                if name == "vix": vix = val
                if name == "dxy": dxy = val
        except:
            print(f"⚠️ Error actualizando {ticker}, usando valor previo.")

    entries = []
    for name, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                sent = TextBlob(e.title).sentiment.polarity
                if name in ['Reuters', 'BBC World', 'DW News', 'France24', 'Kyiv Independent']: bloque = "Occidente (G7)"
                elif name in ['TASS (Rusia)', 'Sputnik', 'RT News', 'Xinhua (China)', 'Global Times (China)', 'SCMP (Hong Kong)']: bloque = "Eurasia (RU/CH)"
                elif name in ['Al Jazeera', 'PressTV (Irán)', 'Tehran Times', 'The Cradle', 'TRT World', 'Haaretz (Israel)']: bloque = "MENA / Resistencia"
                else: bloque = "Sur Global / Otros"

                entries.append({
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'bloque': bloque, 'fuente': name, 'titulo': e.title,
                    'sentiment_score': float(sent),
                    'impacto': round(abs(sent) * 10, 1) + (5 if any(x in e.title.lower() for x in ['war', 'nuclear', 'attack']) else 2),
                    'narrativa': analyze_narrative(e.title),
                    'brent': brent, 'vix': vix, 'dxy': dxy
                })
        except: continue
    
    if entries:
        df_new = pd.DataFrame(entries)
        conn = sqlite3.connect(DB_PATH)
        try:
            df_old = pd.read_sql("SELECT * FROM SITREP", conn)
            pd.concat([df_old, df_new]).drop_duplicates(subset=['titulo']).tail(5000).to_sql("SITREP", conn, if_exists="replace", index=False)
        except:
            df_new.to_sql("SITREP", conn, if_exists="replace", index=False)
        
        # Guardamos timestamp de éxito
        pd.DataFrame([{'last_run': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]).to_sql("METADATA", conn, if_exists="replace", index=False)
        conn.close()
        print(f"SITREP OK: Brent ${brent:.2f}")

if __name__ == "__main__":
    run()
