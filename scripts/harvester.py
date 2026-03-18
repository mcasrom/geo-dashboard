import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import os
import yfinance as yf
import sqlite3
import warnings
import logging

# SILENCIAR LOGS DE YFINANCE Y AVISOS
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
warnings.simplefilter(action='ignore', category=FutureWarning)

DB_PATH = "/home/dietpi/geopol_dashboard/data/geopol.db"

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

def get_impact_score(text, sentiment):
    text = text.lower()
    score = abs(sentiment) * 10
    weights = {'nuclear': 8, 'war': 7, 'attack': 6, 'missile': 6, 'sanctions': 4, 'oil': 4, 'gas': 4}
    for word, weight in weights.items():
        if word in text: score += weight
    return round(score, 1)

def analyze_narrative(text):
    text = text.lower()
    if any(x in text for x in ['nato', 'biden', 'sanctions']): return "Pro-Occidente / Anti-Rusia"
    if any(x in text for x in ['imperialism', 'hegemony', 'resistance']): return "Anti-Occidente / Soberanista"
    if any(x in text for x in ['multipolar', 'brics', 'global south']): return "Multipolarismo"
    if any(x in text for x in ['nuclear', 'war', 'strike']): return "Escalada Militar"
    return "Informativo Global"

def run():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # PERSISTENCIA MEJORADA (Búsqueda de últimos valores reales)
    brent, vix, dxy = 82.0, 15.0, 103.5
    try:
        conn = sqlite3.connect(DB_PATH)
        for col in ['brent', 'vix', 'dxy']:
            res = conn.execute(f"SELECT {col} FROM SITREP WHERE {col} > 0 ORDER BY date DESC LIMIT 1").fetchone()
            if res:
                if col == 'brent': brent = res[0]
                elif col == 'vix': vix = res[0]
                elif col == 'dxy': dxy = res[0]
        conn.close()
    except: pass

    # TICKERS ACTUALIZADOS: DX=F es más estable que DX-Y.NYB
    assets = {"BZ=F": "brent", "^VIX": "vix", "DX=F": "dxy"}
    for ticker, name in assets.items():
        try:
            m_data = yf.download(ticker, period="5d", interval="1d", progress=False)
            if not m_data.empty:
                val = float(m_data['Close'].dropna().iloc[-1])
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
                if name in ['Reuters', 'BBC World', 'DW News', 'France24', 'Kyiv Independent']: bloque = "Occidente (G7)"
                elif name in ['TASS (Rusia)', 'Sputnik', 'RT News', 'Xinhua (China)', 'Global Times (China)', 'SCMP (Hong Kong)']: bloque = "Eurasia (RU/CH)"
                elif name in ['Al Jazeera', 'PressTV (Irán)', 'Tehran Times', 'The Cradle', 'TRT World', 'Haaretz (Israel)']: bloque = "MENA / Resistencia"
                else: bloque = "Sur Global / Otros"

                entries.append({
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'bloque': bloque, 'fuente': name, 'titulo': e.title,
                    'sentiment_score': float(sent),
                    'impacto': get_impact_score(e.title, sent),
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
            conn.execute("VACUUM")
        except:
            df_new.to_sql("SITREP", conn, if_exists="replace", index=False)
        
        pd.DataFrame([{'last_run': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]).to_sql("METADATA", conn, if_exists="replace", index=False)
        conn.close()
        print(f"SITREP OK: Brent ${brent:.2f} | VIX {vix:.2f} | DXY {dxy:.2f}")

if __name__ == "__main__":
    run()
