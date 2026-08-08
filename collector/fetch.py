"""Fetch feeds over HTTP (stdlib only) with graceful per-feed failure."""

from __future__ import annotations

import concurrent.futures
import gzip
import io
import sys
import urllib.request

from .feeds import Feed
from .parse import Article, parse_feed

USER_AGENT = (
    "Mozilla/5.0 (compatible; news-collector/1.0; "
    "+https://github.com/sharjeel45557/news-collector)"
)
TIMEOUT = 20


def fetch_url(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip" or data[:2] == b"\x1f\x8b":
            data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
    return data.decode("utf-8", errors="replace")


def fetch_feed(feed: Feed) -> list[Article]:
    try:
        xml_text = fetch_url(feed.url)
    except Exception as exc:  # network errors must never kill the run
        print(f"warn: {feed.source} ({feed.url}): {exc}", file=sys.stderr)
        return []
    articles = parse_feed(xml_text, feed.source, feed.section)
    if not articles:
        print(f"warn: {feed.source} ({feed.url}): no articles parsed", file=sys.stderr)
    return articles


def fetch_all(feeds: list[Feed], max_workers: int = 8) -> list[Article]:
    articles: list[Article] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        for result in pool.map(fetch_feed, feeds):
            articles.extend(result)
    return articles
