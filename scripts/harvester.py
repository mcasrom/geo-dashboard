import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
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
    'ZeroHedge': 'https://feeds.feedburner.com/zerohedge/feed'
}

def analyze_theatre(text):
    text = text.lower()
    if any(x in text for x in ['houthi', 'yemen', 'red sea', 'bab el-mandeb', 'ormuz']): return "Suministro Energético"
    if any(x in text for x in ['ukraine', 'russia', 'nato', 'poland', 'baltic']): return "Frente Europeo"
    if any(x in text for x in ['taiwan', 'china', 'philippines', 'south china sea']): return "Indo-Pacífico"
    if any(x in text for x in ['israel', 'gaza', 'lebanon', 'iran']): return "Levante / Oriente Medio"
    return "Global / Otros"

def run():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 1. Recuperar Precios Anteriores para calcular CORRELACIÓN
    brent_old, vix_old = 80.0, 15.0
    try:
        conn = sqlite3.connect(DB_PATH)
        res = conn.execute("SELECT brent, vix FROM SITREP ORDER BY date DESC LIMIT 1").fetchone()
        if res: brent_old, vix_old = res[0], res[1]
        conn.close()
    except: pass

    # 2. Descarga de Mercados Actuales
    brent, vix, dxy = brent_old, vix_old, 103.0
    try:
        for ticker, name in [("BZ=F", "brent"), ("^VIX", "vix"), ("DX=F", "dxy")]:
            m_data = yf.download(ticker, period="2d", interval="1h", progress=False)
            if not m_data.empty:
                val = float(m_data['Close'].iloc[-1])
                if name == "brent": brent = val
                elif name == "vix": vix = val
                elif name == "dxy": dxy = val
    except: pass

    # 3. Calcular Correlación de Impacto
    # Si el Brent subió más de 0.5% desde la última vez, las noticias de energía tienen "Alta Correlación"
    brent_delta = (brent - brent_old) / brent_old if brent_old > 0 else 0
    vix_delta = (vix - vix_old) / vix_old if vix_old > 0 else 0

    entries = []
    for name, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                sent = TextBlob(e.title).sentiment.polarity
                theatre = analyze_theatre(e.title)
                
                # LÓGICA DE CORRELACIÓN:
                # Si la noticia es del teatro "Energía" y el Brent subió, el impacto se duplica.
                correlacion = 1.0
                if theatre == "Suministro Energético" and brent_delta > 0.005: correlacion = 2.0
                if vix_delta > 0.05: correlacion = 1.5 # Pánico generalizado aumenta el impacto
                
                impacto = (abs(sent) * 10) * correlacion
                if any(x in e.title.lower() for x in ['attack', 'missile', 'strike', 'shutdown']): impacto += 5

                entries.append({
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'fuente': name, 'titulo': e.title, 'theatre': theatre,
                    'sentiment_score': float(sent), 'impacto': round(impacto, 2),
                    'brent': brent, 'vix': vix, 'dxy': dxy,
                    'market_move': "BULLISH" if brent_delta > 0.002 else "STABLE"
                })
        except: continue
    
    if entries:
        df_new = pd.DataFrame(entries)
        conn = sqlite3.connect(DB_PATH)
        try:
            df_old = pd.read_sql("SELECT * FROM SITREP", conn)
            pd.concat([df_old, df_new]).drop_duplicates(subset=['titulo']).tail(3000).to_sql("SITREP", conn, if_exists="replace", index=False)
        except:
            df_new.to_sql("SITREP", conn, if_exists="replace", index=False)
        conn.close()
        print(f"Intel V7 OK | Brent Delta: {brent_delta:.4f} | VIX Delta: {vix_delta:.4f}")

if __name__ == "__main__":
    run()
