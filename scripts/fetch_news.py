#!/usr/bin/env python3
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

# 日本語ニュース見出しをGoogle News RSSから取得。
# Reuters等を直接スクレイピングしない。Google Newsの検索結果に出る場合のみ表示。
RSS_FEEDS = [
    ("日本不動産", "https://news.google.com/rss/search?q=%E6%97%A5%E6%9C%AC%20%E4%B8%8D%E5%8B%95%E7%94%A3%20%E6%8A%95%E8%B3%87%20OR%20%E6%9D%B1%E4%BA%AC%20%E4%B8%8D%E5%8B%95%E7%94%A3%20%E6%8A%95%E8%B3%87&hl=ja&gl=JP&ceid=JP:ja"),
    ("ホテル/インバウンド", "https://news.google.com/rss/search?q=%E6%97%A5%E6%9C%AC%20%E3%83%9B%E3%83%86%E3%83%AB%20%E3%82%A4%E3%83%B3%E3%83%90%E3%82%A6%E3%83%B3%E3%83%89%20%E6%8A%95%E8%B3%87&hl=ja&gl=JP&ceid=JP:ja"),
    ("富裕層/ラグジュアリー", "https://news.google.com/rss/search?q=%E6%97%A5%E6%9C%AC%20%E5%AF%8C%E8%A3%95%E5%B1%A4%20%E3%83%A9%E3%82%B0%E3%82%B8%E3%83%A5%E3%82%A2%E3%83%AA%E3%83%BC%20%E6%B6%88%E8%B2%BB&hl=ja&gl=JP&ceid=JP:ja"),
    ("香港/シンガポール資本", "https://news.google.com/rss/search?q=%E9%A6%99%E6%B8%AF%20%E3%82%B7%E3%83%B3%E3%82%AC%E3%83%9D%E3%83%BC%E3%83%AB%20%E6%97%A5%E6%9C%AC%20%E6%8A%95%E8%B3%87%20%E4%B8%8D%E5%8B%95%E7%94%A3&hl=ja&gl=JP&ceid=JP:ja"),
    ("金利/為替", "https://news.google.com/rss/search?q=%E6%97%A5%E6%9C%AC%20%E9%87%91%E5%88%A9%20%E5%86%86%E7%9B%B8%E5%A0%B4%20%E6%97%A5%E9%8A%80%20%E4%B8%8D%E5%8B%95%E7%94%A3&hl=ja&gl=JP&ceid=JP:ja"),
    ("アート/ジュエリー", "https://news.google.com/rss/search?q=%E3%82%A2%E3%83%BC%E3%83%88%20%E3%82%B8%E3%83%A5%E3%82%A8%E3%83%AA%E3%83%BC%20%E3%82%AA%E3%83%BC%E3%82%AF%E3%82%B7%E3%83%A7%E3%83%B3%20%E5%AF%8C%E8%A3%95%E5%B1%A4&hl=ja&gl=JP&ceid=JP:ja"),
]
MAX_ITEMS = 20
OUT = Path("news.json")

def clean_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title or "").strip()
    # Google News title often ends with " - 媒体名"; keep source separately when possible.
    title = re.sub(r"\s+-\s+[^-]{2,80}$", "", title).strip()
    return title[:120]

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
        link = item.findtext("link") or ""
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
