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

# Lógica de Impacto Ponderado
def get_impact_score(text, sentiment):
    text = text.lower()
    score = abs(sentiment) * 10
    weights = {
        'nuclear': 8, 'war': 7, 'attack': 6, 'missile': 6, 
        'sanctions': 4, 'brics': 3, 'treaty': 3, 'summit': 2,
        'election': 2, 'oil': 4, 'gas': 4, 'dollar': 3
    }
    for word, weight in weights.items():
        if word in text:
            score += weight
    return round(score, 1)

def analyze_narrative(text):
    text = text.lower()
    if any(x in text for x in ['nato', 'biden', 'sanctions', 'aggression']): return "Pro-Occidente / Anti-Rusia"
    if any(x in text for x in ['imperialism', 'hegemony', 'resistance', 'genocide']): return "Anti-Occidente / Soberanista"
    if any(x in text for x in ['multipolar', 'brics', 'de-dollarization', 'global south']): return "Multipolarismo"
    if any(x in text for x in ['nuclear', 'missile', 'strike', 'war', 'frontline']): return "Escalada Militar"
    return "Informativo Global"

def run():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Persistencia de mercados
    brent, vix, dxy = 82.0, 15.0, 103.5
    try:
        conn = sqlite3.connect(DB_PATH)
        for col, var in [('brent', 'brent'), ('vix', 'vix'), ('dxy', 'dxy')]:
            res = conn.execute(f"SELECT {col} FROM SITREP WHERE {col} > 0 ORDER BY date DESC LIMIT 1").fetchone()
            if res:
                if var == 'brent': brent = res[0]
                elif var == 'vix': vix = res[0]
                elif var == 'dxy': dxy = res[0]
        conn.close()
    except: pass

    # Update Mercados
    assets = {"BZ=F": "brent", "^VIX": "vix", "DX-Y.NYB": "dxy"}
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
            # Mantenemos 5000 registros para no saturar RAM de la Odroid
            pd.concat([df_old, df_new]).drop_duplicates(subset=['titulo']).tail(5000).to_sql("SITREP", conn, if_exists="replace", index=False)
            # OPTIMIZACIÓN SD: Limpieza física de la DB
            conn.execute("VACUUM")
        except:
            df_new.to_sql("SITREP", conn, if_exists="replace", index=False)
        
        pd.DataFrame([{'last_run': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]).to_sql("METADATA", conn, if_exists="replace", index=False)
        conn.close()
        print(f"SITREP V6 OK: Brent ${brent:.2f} | VIX {vix:.2f} | DXY {dxy:.2f}")

if __name__ == "__main__":
    run()
