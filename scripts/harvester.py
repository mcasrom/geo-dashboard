import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import os
import yfinance as yf
import sqlite3

DB_PATH = "/home/dietpi/geopol_dashboard/data/geopol.db"

# 16 FUENTES GLOBALES PARA ROMPER LA POLARIZACIÓN
SOURCES = {
    # OCCIDENTE (G7/OTAN)
    'Reuters': 'https://www.reutersagency.com/feed/?best-topics=world',
    'BBC World': 'https://feeds.bbci.co.uk/news/world/rss.xml',
    'DW News (Alemania)': 'https://rss.dw.com/rdf/rss-en-all',
    'France24': 'https://www.france24.com/en/rss',
    
    # EURASIA (Rusia/China)
    'TASS (Rusia)': 'https://tass.com/rss/v2.xml',
    'Sputnik': 'https://sputnikglobe.com/export/rss2/archive/index.xml',
    'Xinhua (China)': 'https://www.xinhuanet.com/english/rss/worldrss.xml',
    'Global Times (China)': 'https://www.globaltimes.cn/rss/world.xml',
    
    # ORIENTE MEDIO (MENA/Irán/Israel)
    'Al Jazeera (Qatar)': 'https://www.aljazeera.com/xml/rss/all.xml',
    'PressTV (Irán)': 'https://www.presstv.ir/Default/RSS',
    'TRT World (Turquía)': 'https://www.trtworld.com/rss/world',
    'Haaretz (Israel)': 'https://www.haaretz.com/cmlink/1.4621115',
    
    # SUR GLOBAL / EMERGENTES
    'The Hindu (India)': 'https://www.thehindu.com/news/international/feeder/default.rss',
    'Africanews': 'https://www.africanews.com/feed/rss',
    'MercoPress (LatAm)': 'https://en.mercopress.com/rss/',
    'ZeroHedge (Alternativo)': 'https://feeds.feedburner.com/zerohedge/feed'
}

def analyze_narrative(text):
    text = text.lower()
    if any(x in text for x in ['nato', 'biden', 'sanctions', 'aggression']): return "Pro-Occidente / Anti-Rusia"
    if any(x in text for x in ['imperialism', 'hegemony', 'resistance', 'colonial']): return "Anti-Occidente / Soberanista"
    if any(x in text for x in ['multipolar', 'brics', 'global south']): return "Multipolarismo / Emergentes"
    if any(x in text for x in ['nuclear', 'missile', 'strike', 'war']): return "Escalada Militar"
    return "Informativo Neutral"

def run():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Captura de Mercados
    try:
        data = yf.download(["BZ=F", "^VIX", "DX-Y.NYB"], period="1d", interval="1m")['Close'].iloc[-1]
        brent, vix, dxy = data["BZ=F"], data["^VIX"], data["DX-Y.NYB"]
    except: brent, vix, dxy = 0, 0, 0

    entries = []
    for name, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                sent = TextBlob(e.title).sentiment.polarity
                
                # Clasificación por Bloque Geopolítico
                if name in ['Reuters', 'BBC World', 'DW News (Alemania)', 'France24']: bloque = "Occidente (G7)"
                elif name in ['TASS (Rusia)', 'Sputnik', 'Xinhua (China)', 'Global Times (China)']: bloque = "Eurasia (RU/CH)"
                elif name in ['Al Jazeera (Qatar)', 'PressTV (Irán)', 'TRT World (Turquía)', 'Haaretz (Israel)']: bloque = "MENA / Resistencia"
                else: bloque = "Sur Global / Otros"

                entries.append({
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'bloque': bloque,
                    'fuente': name,
                    'titulo': e.title,
                    'sentiment_score': sent,
                    'impacto': round(abs(sent) * 10, 1) + (5 if any(x in e.title.lower() for x in ['war', 'nuclear', 'attack']) else 2),
                    'narrativa': analyze_narrative(e.title),
                    'brent': brent, 'vix': vix, 'dxy': dxy
                })
        except: continue
    
    df_new = pd.DataFrame(entries)
    conn = sqlite3.connect(DB_PATH)
    try:
        df_old = pd.read_sql("SELECT * FROM SITREP", conn)
        pd.concat([df_old, df_new]).drop_duplicates(subset=['titulo']).tail(10000).to_sql("SITREP", conn, if_exists="replace", index=False)
    except:
        df_new.to_sql("SITREP", conn, if_exists="replace", index=False)
    conn.close()
    print(f"SITREP Actualizado con 16 fuentes. Total registros: {len(df_new)}")

if __name__ == "__main__":
    run()
