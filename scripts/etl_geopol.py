import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import datetime
import os

RSS_FEEDS = {
    "Occidente_USA": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "OrienteMedio_Qatar": "https://www.aljazeera.com/xml/rss/all.xml",
    "Rusia_TASS": "https://tass.com/rss/v2.xml"
}

KEYWORDS =["iran", "israel", "gaza", "nato", "putin", "biden", "oil", "red sea", "houthi", "china", "eu", "brics"]

analyzer = SentimentIntensityAnalyzer()
extracted_data =[]

for block, url in RSS_FEEDS.items():
    feed = feedparser.parse(url)
    for entry in feed.entries:
        title = entry.title
        if any(kw in title.lower() for kw in KEYWORDS):
            vs = analyzer.polarity_scores(title)
            tema = "General"
            if "nato" in title.lower() or "eu" in title.lower(): tema = "OTAN/UE"
            if "iran" in title.lower() or "israel" in title.lower(): tema = "Conflicto Medio Oriente"
            if "oil" in title.lower() or "red sea" in title.lower() or "houthi" in title.lower(): tema = "Comercio/Petroleo"

            extracted_data.append({
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "bloque": block,
                "title": title,
                "tema": tema,
                "sentiment_score": vs['compound']
            })

csv_path = "/home/dietpi/geopol_dashboard/data/geopol_data.csv"
df = pd.DataFrame(extracted_data)

if not df.empty:
    if os.path.exists(csv_path):
        df.to_csv(csv_path, mode='a', header=False, index=False)
    else:
        df.to_csv(csv_path, index=False)
