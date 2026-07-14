from urllib.parse import quote

from ingestion.sources.rss import fetch_rss


def fetch_query(query: str, source_name: str, window: str = "3d"):
    url = f"https://news.google.com/rss/search?q={quote(query)}+when:{window}&hl=en-US&gl=US&ceid=US:en"
    return fetch_rss(url, source_name)
