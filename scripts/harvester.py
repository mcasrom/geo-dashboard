import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import os
import yfinance as yf
import sqlite3

# CONFIGURACIÓN
DB_PATH = "/home/dietpi/geopol_dashboard/data/geopol.db"
SOURCES = {
    'Occidente (Reuters)': 'https://www.reutersagency.com/feed/?best-topics=world',
    'Rusia (TASS)': 'https://tass.com/rss/v2.xml', 
    'China (SCMP)': 'https://www.scmp.com/rss/91/feed.xml',
    'Mundo Árabe (Al Jazeera)': 'https://www.aljazeera.com/xml/rss/all.xml',
    'Irán (PressTV)': 'https://www.presstv.ir/Default/RSS'
}

def get_market_intel():
    try:
        # ^VIX: Pánico | DX-Y.NYB: Dólar | BZ=F: Brent
        tickers = {"brent": "BZ=F", "vix": "^VIX", "dxy": "DX-Y.NYB"}
        data = yf.download(list(tickers.values()), period="1d", interval="1m")['Close'].iloc[-1]
        return round(data[tickers['brent']], 2), round(data[tickers['vix']], 2), round(data[tickers['dxy']], 2)
    except: return 0.0, 0.0, 0.0

def run_harvester():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    brent, vix, dxy = get_market_intel()
    
    new_entries = []
    for name, url in SOURCES.items():
        feed = feedparser.parse(url)
        for e in feed.entries:
            sent = TextBlob(e.title).sentiment.polarity
            new_entries.append({
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'bloque': "Occidente" if "Reuters" in name else "Eurasia" if ("TASS" in name or "SCMP" in name) else "MENA",
                'sentiment_score': sent,
                'impacto': round(abs(sent) * 10, 1) + 2,
                'fuente': name,
                'titulo': e.title,
                'brent': brent, 'vix': vix, 'dxy': dxy
            })

    df_new = pd.DataFrame(new_entries)
    
    # GUARDAR EN SQLITE (No duplica noticias por título)
    conn = sqlite3.connect(DB_PATH)
    try:
        # Cargamos lo existente para no duplicar
        df_old = pd.read_sql("SELECT * FROM SITREP", conn)
        df_final = pd.concat([df_old, df_new]).drop_duplicates(subset=['titulo']).tail(5000)
        df_final.to_sql("SITREP", conn, if_exists="replace", index=False)
    except:
        df_new.to_sql("SITREP", conn, if_exists="replace", index=False)
    conn.close()
    print(f"SITREP DB Actualizada. VIX: {vix} | DXY: {dxy}")

if __name__ == "__main__":
    run_harvester()
