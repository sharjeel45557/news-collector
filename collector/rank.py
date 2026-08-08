"""Deduplicate, rank, and select the stories that make the front page."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from .parse import Article

MAX_AGE = timedelta(hours=48)
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _canonical_url(link: str) -> str:
    parts = urlsplit(link.strip())
    host = parts.netloc.lower().removeprefix("www.")
    return f"{host}{parts.path.rstrip('/')}"


def _similar(a: Article, b: Article) -> bool:
    if not a.words or not b.words:
        return False
    overlap = len(a.words & b.words)
    return overlap / min(len(a.words), len(b.words)) >= 0.75


def _quality(article: Article) -> tuple:
    return (
        article.image is not None,
        len(article.summary) > 40,
        article.published or EPOCH,
    )


def dedupe(articles: list[Article]) -> list[Article]:
    """Drop same-URL duplicates and near-identical headlines, keeping the
    richest copy (image > summary > recency)."""
    by_url: dict[str, Article] = {}
    for art in articles:
        key = _canonical_url(art.link)
        if key not in by_url or _quality(art) > _quality(by_url[key]):
            by_url[key] = art
    unique: list[Article] = []
    for art in sorted(by_url.values(), key=_quality, reverse=True):
        if not any(_similar(art, kept) for kept in unique):
            unique.append(art)
    return unique


def _sort_key(article: Article) -> datetime:
    return article.published or EPOCH


def select(
    articles: list[Article],
    sections: list[str],
    now: datetime | None = None,
    per_section: int = 8,
) -> dict:
    """Build the front-page structure: a lead story, a latest-news rail,
    and per-section story lists."""
    now = now or datetime.now(timezone.utc)
    fresh = [
        a
        for a in dedupe(articles)
        if a.published is None or now - a.published <= MAX_AGE
    ]
    fresh.sort(key=_sort_key, reverse=True)

    # Lead: among the freshest stories rich enough for the slot, prefer the
    # earliest section in the configured order (hard news first).
    eligible = [a for a in fresh if a.image and a.summary and len(a.summary) > 60]
    priority = {s: i for i, s in enumerate(sections)}
    lead = min(
        eligible[:10],
        key=lambda a: priority.get(a.section, len(sections)),
        default=fresh[0] if fresh else None,
    )
    top_pool = [a for a in fresh if a is not lead]
    top = [a for a in top_pool if a.image][:3]
    used = {id(lead)} | {id(a) for a in top}

    latest = [a for a in fresh if id(a) not in used][:10]

    by_section: dict[str, list[Article]] = {s: [] for s in sections}
    for art in fresh:
        if id(art) in used:
            continue
        bucket = by_section.get(art.section)
        if bucket is not None and len(bucket) < per_section:
            bucket.append(art)

    return {
        "generated": now,
        "lead": lead,
        "top": top,
        "latest": latest,
        "sections": {s: arts for s, arts in by_section.items() if arts},
    }
