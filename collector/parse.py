"""Parse RSS 2.0 and Atom feeds into Article objects using only the stdlib."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

ATOM_NS = "{http://www.w3.org/2005/Atom}"
MEDIA_NS = "{http://search.yahoo.com/mrss/}"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)


@dataclass
class Article:
    title: str
    link: str
    summary: str = ""
    published: datetime | None = None
    image: str | None = None
    source: str = ""
    section: str = ""
    words: frozenset[str] = field(default_factory=frozenset, repr=False)

    def __post_init__(self) -> None:
        self.words = frozenset(re.findall(r"[a-z0-9]+", self.title.lower()))


def _strip_html(text: str) -> str:
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def _parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _first_text(el: ET.Element, *tags: str) -> str | None:
    for tag in tags:
        child = el.find(tag)
        if child is not None and child.text:
            return child.text.strip()
    return None


def _extract_image(item: ET.Element, description_html: str) -> str | None:
    for tag in (f"{MEDIA_NS}content", f"{MEDIA_NS}thumbnail"):
        for media in item.iter(tag):
            url = media.get("url")
            medium = media.get("medium", "image")
            mtype = media.get("type", "image/")
            if url and (medium == "image" or mtype.startswith("image")):
                return url
    for enc in item.iter("enclosure"):
        if enc.get("url") and enc.get("type", "").startswith("image"):
            return enc.get("url")
    match = _IMG_RE.search(description_html)
    if match:
        return match.group(1)
    return None


def _parse_rss_item(item: ET.Element, source: str, section: str) -> Article | None:
    title = _first_text(item, "title")
    link = _first_text(item, "link")
    if not title or not link:
        return None
    raw_desc = _first_text(item, "description", f"{CONTENT_NS}encoded") or ""
    return Article(
        title=_strip_html(title),
        link=link,
        summary=_strip_html(raw_desc),
        published=_parse_date(_first_text(item, "pubDate", "date")),
        image=_extract_image(item, raw_desc),
        source=source,
        section=section,
    )


def _parse_atom_entry(entry: ET.Element, source: str, section: str) -> Article | None:
    title_el = entry.find(f"{ATOM_NS}title")
    title = "".join(title_el.itertext()).strip() if title_el is not None else None
    link = None
    for link_el in entry.findall(f"{ATOM_NS}link"):
        rel = link_el.get("rel", "alternate")
        if rel == "alternate" and link_el.get("href"):
            link = link_el.get("href")
            break
    if not title or not link:
        return None
    raw_summary = ""
    for tag in (f"{ATOM_NS}summary", f"{ATOM_NS}content"):
        el = entry.find(tag)
        if el is not None:
            raw_summary = "".join(el.itertext())
            break
    return Article(
        title=_strip_html(title),
        link=link,
        summary=_strip_html(raw_summary),
        published=_parse_date(
            _first_text(entry, f"{ATOM_NS}published", f"{ATOM_NS}updated")
        ),
        image=_extract_image(entry, raw_summary),
        source=source,
        section=section,
    )


def parse_feed(xml_text: str, source: str, section: str) -> list[Article]:
    """Parse a feed document (RSS 2.0 or Atom); returns [] on malformed input."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    articles: list[Article] = []
    if root.tag == f"{ATOM_NS}feed":
        for entry in root.findall(f"{ATOM_NS}entry"):
            art = _parse_atom_entry(entry, source, section)
            if art:
                articles.append(art)
    else:
        for item in root.iter("item"):
            art = _parse_rss_item(item, source, section)
            if art:
                articles.append(art)
    return articles
