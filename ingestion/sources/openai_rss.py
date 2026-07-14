import urllib.request
import xml.etree.ElementTree as ET

from ingestion.item import make_item

FEED_URL = "https://openai.com/news/rss.xml"


def fetch():
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml_data = resp.read()

    root = ET.fromstring(xml_data)
    items = []
    for entry in root.findall(".//item"):
        title = entry.findtext("title") or ""
        link = entry.findtext("link") or ""
        description = entry.findtext("description") or ""
        pub_date = entry.findtext("pubDate")
        if not link:
            continue
        items.append(make_item(
            source="openai.com/news",
            url=link,
            title=title,
            content=description,
            published_at=pub_date,
        ))
    return items
