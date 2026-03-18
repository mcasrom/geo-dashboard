import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import os
import yfinance as yf

SOURCES = {
    'Occidente (Reuters)': 'https://www.reutersagency.com/feed/?best-topics=world',
    'Rusia (TASS)': 'https://tass.com/rss/v2.xml', 
    'China (SCMP)': 'https://www.scmp.com/rss/91/feed.xml',
    'Mundo Árabe (Al Jazeera)': 'https://www.aljazeera.com/xml/rss/all.xml',
    'Irán (PressTV)': 'https://www.presstv.ir/Default/RSS'
}

def analyze_narrative(text):
    text = text.lower()
    if any(x in text for x in ['nato', 'biden', 'hegemony', 'imperialism']): return "Narrativa Crítica Occidente"
    if any(x in text for x in ['putin', 'aggression', 'invasion', 'sanctions']): return "Narrativa Conflicto Rusia"
    if any(x in text for x in ['taiwan', 'sovereignty', 'xi jinping']): return "Eje Asia-Pacífico"
    if any(x in text for x in ['iran', 'tehran', 'resistance', 'zionist']): return "Eje Resistencia (MENA)"
    return "Estándar / Informativo"

def run_harvester():
    csv_path = "/home/dietpi/geopol_dashboard/data/geopol_data.csv"
    os.makedirs("/home/dietpi/geopol_dashboard/data", exist_ok=True)
    
    # Mercados
    try:
        brent = round(yf.Ticker("BZ=F").fast_info['last_price'], 2)
        gold = round(yf.Ticker("GC=F").fast_info['last_price'], 2)
    except: brent, gold = 0.0, 0.0

    collected = []
    for name, url in SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title
            sent = TextBlob(title).sentiment.polarity
            
            # Bloque
            bloque = "Occidente" if "Reuters" in name else "Eurasia" if ("TASS" in name or "SCMP" in name) else "MENA" if "Al Jazeera" in name or "PressTV" in name else "Otros"
            
            collected.append({
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'bloque': bloque,
                'sentiment_score': sent,
                'impacto': round(abs(sent) * 10, 1) + 2,
                'fuente': name,
                'titulo': title,
                'narrativa': analyze_narrative(title),
                'brent_price': brent,
                'gold_price': gold
            })

    df_new = pd.DataFrame(collected)
    if os.path.exists(csv_path):
        df_old = pd.read_csv(csv_path)
        pd.concat([df_old, df_new]).drop_duplicates(subset=['titulo']).tail(3000).to_csv(csv_path, index=False)
    else:
        df_new.to_csv(csv_path, index=False)
    print(f"SITREP OK. Brent: ${brent}")

if __name__ == "__main__":
    run_harvester()
