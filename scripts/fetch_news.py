#!/usr/bin/env python3
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

RSS_FEEDS = [
    ("Japan Real Estate", "https://news.google.com/rss/search?q=Japan%20real%20estate%20market%20OR%20Tokyo%20property%20investment&hl=en-US&gl=US&ceid=US:en"),
    ("Luxury / Hospitality", "https://news.google.com/rss/search?q=Japan%20luxury%20hotel%20residence%20hospitality%20investment&hl=en-US&gl=US&ceid=US:en"),
    ("Wealth / Inbound", "https://news.google.com/rss/search?q=Japan%20inbound%20wealth%20luxury%20travel%20residence&hl=en-US&gl=US&ceid=US:en"),
    ("HK / SG Capital", "https://news.google.com/rss/search?q=Hong%20Kong%20Singapore%20capital%20Japan%20investment%20real%20estate&hl=en-US&gl=US&ceid=US:en"),
    ("FX / Rates", "https://news.google.com/rss/search?q=Japan%20yen%20interest%20rates%20Bank%20of%20Japan%20real%20estate&hl=en-US&gl=US&ceid=US:en"),
    ("Art / Jewelry", "https://news.google.com/rss/search?q=art%20jewelry%20luxury%20auction%20Asia%20wealth&hl=en-US&gl=US&ceid=US:en"),
]
MAX_ITEMS = 18
OUT = Path("news.json")

def clean_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title or "").strip()
    title = re.sub(r"\s+-\s+[^-]{2,80}$", "", title).strip()
    return title[:150]

def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 SynthXMarketPulse/1.0",
        "Accept": "application/rss+xml, application/xml, text/xml",
    })
    with urllib.request.urlopen(req, timeout=18) as r:
        return r.read()

def parse_feed(category: str, url: str):
    root = ET.fromstring(fetch(url))
    channel = root.find("channel")
    if channel is None:
        return []
    items = []
    for item in channel.findall("item"):
        title = clean_title(item.findtext("title"))
        link = item.findtext("link") or "#"
        pub = item.findtext("pubDate") or ""
        source = item.findtext("source") or category
        ts = 0
        try:
            ts = int(parsedate_to_datetime(pub).timestamp())
        except Exception:
            pass
        if title:
            items.append({
                "title": title,
                "source": source.strip(),
                "category": category,
                "url": link,
                "published": pub,
                "_ts": ts,
            })
    return items

def main():
    seen = set()
    all_items = []
    for category, url in RSS_FEEDS:
        try:
            for item in parse_feed(category, url):
                key = item["title"].lower()
                if key in seen:
                    continue
                seen.add(key)
                all_items.append(item)
        except Exception as e:
            print(f"Feed failed: {category}: {e}")
    all_items.sort(key=lambda x: x.get("_ts", 0), reverse=True)
    all_items = all_items[:MAX_ITEMS]
    for x in all_items:
        x.pop("_ts", None)
    if not all_items and OUT.exists():
        print("No new items; keeping existing news.json")
        return
    OUT.write_text(json.dumps({
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "items": all_items,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_items)} items to {OUT}")

if __name__ == "__main__":
    main()
