import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import os
import yfinance as yf
import sqlite3
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
DB_PATH = "/home/dietpi/geopol_dashboard/data/geopol.db"

SOURCES = {
    'Reuters': 'https://www.reutersagency.com/feed/?best-topics=world',
    'TASS': 'https://tass.com/rss/v2.xml',
    'Al Jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
    'Tehran Times': 'https://www.tehrantimes.com/rss',
    'SCMP': 'https://www.scmp.com/rss/91/feed',
    'ZeroHedge': 'https://feeds.feedburner.com/zerohedge/feed',
    'RT News': 'https://www.rt.com/rss/news/',
    'Sputnik': 'https://sputnikglobe.com/export/rss2/archive/index.xml'
}

def analyze_theatre(text):
    if not text: return "Global / Otros"
    text = text.lower()
    if any(x in text for x in ['houthi', 'yemen', 'red sea', 'ormuz', 'bab el-mandeb']): return "Suministro Energético"
    if any(x in text for x in ['ukraine', 'russia', 'nato', 'nord stream', 'putin']): return "Frente Europeo"
    if any(x in text for x in ['taiwan', 'china', 'philippines', 'south china sea', 'xi jinping']): return "Indo-Pacífico"
    if any(x in text for x in ['israel', 'gaza', 'lebanon', 'iran', 'hezbollah']): return "Levante / Oriente Medio"
    return "Global / Otros"

def run():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 1. Recuperar Precios con Persistencia
    brent, vix, dxy = 80.0, 15.0, 103.0
    try:
        conn = sqlite3.connect(DB_PATH)
        res = conn.execute("SELECT brent, vix, dxy FROM SITREP WHERE brent > 0 ORDER BY date DESC LIMIT 1").fetchone()
        if res: brent, vix, dxy = res[0], res[1], res[2]
        conn.close()
    except: pass

    # 2. Descarga de Mercados (Uso de DX=F para estabilidad)
    try:
        for ticker, name in [("BZ=F", "brent"), ("^VIX", "vix"), ("DX=F", "dxy")]:
            m_data = yf.download(ticker, period="2d", interval="1h", progress=False)
            if not m_data.empty:
                val = float(m_data['Close'].iloc[-1])
                if val > 0:
                    if name == "brent": brent = val
                    elif name == "vix": vix = val
                    elif name == "dxy": dxy = val
    except: pass

    entries = []
    for name, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                sent = TextBlob(e.title).sentiment.polarity
                theatre = analyze_theatre(e.title)
                
                # Cálculo de Impacto
                impacto = abs(sent) * 10
                if any(x in e.title.lower() for x in ['attack', 'missile', 'strike', 'war', 'nuclear']): impacto += 7
                if theatre == "Suministro Energético" and brent > 90: impacto += 5

                entries.append({
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'fuente': name, 'titulo': e.title, 'theatre': theatre,
                    'sentiment_score': float(sent), 'impacto': round(impacto, 2),
                    'brent': brent, 'vix': vix, 'dxy': dxy
                })
        except: continue
    
    if entries:
        df_new = pd.DataFrame(entries)
        conn = sqlite3.connect(DB_PATH)
        try:
            df_old = pd.read_sql("SELECT * FROM SITREP", conn)
            # Mantenemos 5000 registros, eliminamos duplicados
            pd.concat([df_old, df_new]).drop_duplicates(subset=['titulo']).tail(5000).to_sql("SITREP", conn, if_exists="replace", index=False)
        except:
            df_new.to_sql("SITREP", conn, if_exists="replace", index=False)
        
        pd.DataFrame([{'last_run': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]).to_sql("METADATA", conn, if_exists="replace", index=False)
        conn.close()
        print(f"SITREP OK | Brent: ${brent:.2f}")

if __name__ == "__main__":
    run()
