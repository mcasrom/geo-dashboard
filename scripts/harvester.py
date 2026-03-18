import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import os
import yfinance as yf
import sqlite3

DB_PATH = "/home/dietpi/geopol_dashboard/data/geopol.db"
SOURCES = {
    'Reuters (Occidente)': 'https://www.reutersagency.com/feed/?best-topics=world',
    'TASS (Rusia)': 'https://tass.com/rss/v2.xml', 
    'SCMP (China)': 'https://www.scmp.com/rss/91/feed.xml',
    'Al Jazeera (MENA)': 'https://www.aljazeera.com/xml/rss/all.xml',
    'PressTV (Irán)': 'https://www.presstv.ir/Default/RSS'
}

def analyze_narrative(text):
    text = text.lower()
    if any(x in text for x in ['nato', 'biden', 'sanctions']): return "Anti-Rusia/China"
    if any(x in text for x in ['imperialism', 'hegemony', 'resistance']): return "Anti-Occidente"
    if any(x in text for x in ['taiwan', 'south china sea']): return "Crisis Asia"
    return "Informativo Global"

def run():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    # Obtener Mercados
    try:
        data = yf.download(["BZ=F", "^VIX", "DX-Y.NYB"], period="1d", interval="1m")['Close'].iloc[-1]
        brent, vix, dxy = data["BZ=F"], data["^VIX"], data["DX-Y.NYB"]
    except: brent, vix, dxy = 0, 0, 0

    entries = []
    for name, url in SOURCES.items():
        feed = feedparser.parse(url)
        for e in feed.entries:
            sent = TextBlob(e.title).sentiment.polarity
            entries.append({
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'bloque': "Occidente" if "Reuters" in name else "Eurasia" if ("TASS" in name or "SCMP" in name) else "MENA",
                'fuente': name,
                'titulo': e.title,
                'sentiment_score': sent,
                'impacto': round(abs(sent) * 10, 1) + 2,
                'narrativa': analyze_narrative(e.title),
                'brent': brent, 'vix': vix, 'dxy': dxy
            })
    
    df_new = pd.DataFrame(entries)
    conn = sqlite3.connect(DB_PATH)
    try:
        df_old = pd.read_sql("SELECT * FROM SITREP", conn)
        pd.concat([df_old, df_new]).drop_duplicates(subset=['titulo']).tail(5000).to_sql("SITREP", conn, if_exists="replace", index=False)
    except:
        df_new.to_sql("SITREP", conn, if_exists="replace", index=False)
    conn.close()

if __name__ == "__main__":
    run()
