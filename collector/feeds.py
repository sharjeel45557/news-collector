"""Curated list of RSS/Atom feeds spanning major publishers and topics.

Each feed maps to one of the page sections. Order within a section is the
tie-break priority when ranking stories.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Feed:
    url: str
    source: str
    section: str


SECTIONS = [
    "World",
    "Business",
    "Markets",
    "Technology",
    "Science",
    "Sports",
    "Culture",
]

FEEDS: list[Feed] = [
    # World
    Feed("https://feeds.bbci.co.uk/news/world/rss.xml", "BBC News", "World"),
    Feed("https://www.theguardian.com/world/rss", "The Guardian", "World"),
    Feed("https://www.aljazeera.com/xml/rss/all.xml", "Al Jazeera", "World"),
    Feed("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "The New York Times", "World"),
    Feed("https://feeds.npr.org/1004/rss.xml", "NPR", "World"),
    Feed("https://www.cbc.ca/webfeed/rss/rss-world", "CBC News", "World"),
    # Business
    Feed("https://feeds.bbci.co.uk/news/business/rss.xml", "BBC News", "Business"),
    Feed("https://www.theguardian.com/uk/business/rss", "The Guardian", "Business"),
    Feed("https://rss.nytimes.com/services/xml/rss/nyt/Business.xml", "The New York Times", "Business"),
    Feed("https://www.cnbc.com/id/10001147/device/rss/rss.html", "CNBC", "Business"),
    Feed("https://fortune.com/feed/", "Fortune", "Business"),
    # Markets
    Feed("https://www.cnbc.com/id/100003114/device/rss/rss.html", "CNBC", "Markets"),
    Feed("https://feeds.content.dowjones.io/public/rss/RSSMarketsMain", "The Wall Street Journal", "Markets"),
    Feed("https://www.investing.com/rss/news_25.rss", "Investing.com", "Markets"),
    Feed("https://feeds.marketwatch.com/marketwatch/topstories/", "MarketWatch", "Markets"),
    # Technology
    Feed("https://techcrunch.com/feed/", "TechCrunch", "Technology"),
    Feed("https://www.theverge.com/rss/index.xml", "The Verge", "Technology"),
    Feed("https://feeds.arstechnica.com/arstechnica/index", "Ars Technica", "Technology"),
    Feed("https://www.wired.com/feed/rss", "Wired", "Technology"),
    Feed("https://feeds.bbci.co.uk/news/technology/rss.xml", "BBC News", "Technology"),
    # Science
    Feed("https://www.sciencedaily.com/rss/all.xml", "ScienceDaily", "Science"),
    Feed("https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "BBC News", "Science"),
    Feed("https://rss.nytimes.com/services/xml/rss/nyt/Science.xml", "The New York Times", "Science"),
    Feed("https://www.nasa.gov/feed/", "NASA", "Science"),
    # Sports
    Feed("https://www.espn.com/espn/rss/news", "ESPN", "Sports"),
    Feed("https://feeds.bbci.co.uk/sport/rss.xml", "BBC Sport", "Sports"),
    Feed("https://www.theguardian.com/uk/sport/rss", "The Guardian", "Sports"),
    # Culture
    Feed("https://www.theguardian.com/uk/culture/rss", "The Guardian", "Culture"),
    Feed("https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml", "The New York Times", "Culture"),
    Feed("https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", "BBC News", "Culture"),
]
