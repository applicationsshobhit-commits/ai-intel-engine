import urllib.request
import xml.etree.ElementTree as ET

from ingestion.item import make_item

ATOM_NS = "{http://www.w3.org/2005/Atom}"


def _parse_rss2(root, limit):
    for entry in root.findall(".//item")[:limit]:
        title = entry.findtext("title") or ""
        link = entry.findtext("link") or ""
        description = entry.findtext("description") or ""
        pub_date = entry.findtext("pubDate")
        if link:
            yield title, link, description, pub_date


def _parse_atom(root, limit):
    for entry in root.findall(f"{ATOM_NS}entry")[:limit]:
        title = entry.findtext(f"{ATOM_NS}title") or ""
        link_el = entry.find(f"{ATOM_NS}link[@rel='alternate']") or entry.find(f"{ATOM_NS}link")
        link = link_el.get("href") if link_el is not None else ""
        summary = entry.findtext(f"{ATOM_NS}summary") or entry.findtext(f"{ATOM_NS}content") or ""
        pub_date = entry.findtext(f"{ATOM_NS}published") or entry.findtext(f"{ATOM_NS}updated")
        if link:
            yield title, link, summary, pub_date


def fetch_rss(feed_url: str, source_name: str, limit: int = 40):
    req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml_data = resp.read()

    root = ET.fromstring(xml_data)
    parser = _parse_atom if root.tag == f"{ATOM_NS}feed" else _parse_rss2

    items = []
    for title, link, description, pub_date in parser(root, limit):
        items.append(make_item(
            source=source_name,
            url=link,
            title=title,
            content=description,
            published_at=pub_date,
        ))
    return items
