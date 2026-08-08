"""Generate realistic RSS/Atom fixture feeds with fresh timestamps.

Used by unit tests and the e2e test so the whole pipeline can run offline.
Images are inline SVG data URIs, so the rendered page is self-contained.

    python tests/gen_fixtures.py OUT_DIR
"""

from __future__ import annotations

import base64
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path


def _svg_image(color: str, label: str) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400">'
        f'<rect width="600" height="400" fill="{color}"/>'
        f'<text x="300" y="210" font-size="40" fill="#fff" text-anchor="middle" '
        f'font-family="Georgia">{label}</text></svg>'
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


STORIES = {
    ("world-news-network", "world"): [
        ("Leaders gather for emergency summit on regional security pact",
         "Heads of state from twelve nations convened late on Thursday to negotiate "
         "a new framework for regional security cooperation, with observers calling "
         "it the most consequential diplomatic gathering in a decade.", "#1f3a5f"),
        ("Historic ceasefire agreement signed after marathon negotiations",
         "Negotiators announced a comprehensive ceasefire following eighteen hours "
         "of continuous talks mediated by neutral parties.", "#27496d"),
        ("Election observers report record turnout in national vote",
         "Early figures suggest the highest participation in forty years as polls "
         "closed across the country.", ""),
        ("Flooding displaces thousands as rivers crest at record levels",
         "Emergency services evacuated low-lying districts overnight while engineers "
         "reinforced levees along the swollen river basin.", "#0f5257"),
        ("Trade corridor reopens after months of border closures",
         "Freight traffic resumed at dawn, easing shortages that had rippled through "
         "neighbouring economies.", ""),
    ],
    ("global-business-review", "business"): [
        ("Central bank holds rates steady but signals cuts ahead",
         "Policymakers voted unanimously to keep the benchmark rate unchanged while "
         "revising inflation forecasts downward for the third consecutive quarter.", "#5c3d2e"),
        ("Airline megamerger clears final regulatory hurdle",
         "The combined carrier will become the largest in the region by fleet size "
         "after regulators accepted concessions on landing slots.", ""),
        ("Retail giant posts surprise profit on cost discipline",
         "Shares jumped in early trading after margins beat analyst expectations "
         "despite soft consumer demand.", "#7a4a2b"),
        ("Startup funding rebounds to strongest quarter in two years",
         "Venture investment rose sharply, led by energy storage and enterprise "
         "software deals.", ""),
    ],
    ("market-watch-daily", "markets"): [
        ("Global stocks rally as inflation data comes in cooler than expected",
         "Equity benchmarks climbed across Europe and Asia after consumer price "
         "growth slowed more than forecast, boosting bets on earlier rate cuts.", "#2d5016"),
        ("Oil slides on inventory build and demand worries",
         "Crude futures fell for a fourth session as stockpiles rose unexpectedly.", ""),
        ("Bond yields retreat from multi-year highs",
         "Ten-year yields eased as traders repriced the path of monetary policy.", ""),
        ("Gold touches fresh record as investors seek havens",
         "The metal extended its rally amid currency volatility and central bank "
         "buying.", "#6b5416"),
    ],
    ("tech-chronicle", "technology"): [
        ("Breakthrough chip design promises fourfold gain in AI efficiency",
         "Researchers unveiled a processor architecture that dramatically reduces "
         "power consumption for machine learning workloads, with production slated "
         "for next year.", "#3c1361"),
        ("Major platform rolls out end-to-end encryption by default",
         "The change covers billions of messages daily and follows years of "
         "pressure from privacy advocates.", ""),
        ("Open-source model tops benchmarks in surprise release",
         "The freely licensed model outperformed proprietary rivals on reasoning "
         "tasks.", "#4b2e83"),
        ("Satellite internet constellation reaches global coverage milestone",
         "The network now serves every inhabited continent after the latest launch.", ""),
    ],
    ("science-observer", "science"): [
        ("Astronomers detect water vapour on distant rocky exoplanet",
         "The discovery marks the strongest evidence yet for atmospheric water on "
         "a terrestrial world beyond our solar system, researchers report.", "#1b4965"),
        ("Gene therapy trial restores partial vision in landmark study",
         "Patients with inherited blindness regained light sensitivity in the "
         "year-long trial.", ""),
        ("Antarctic expedition returns with oldest ice core ever drilled",
         "The samples could reveal climate records stretching back a million years.", "#2c699a"),
    ],
    ("sports-tribune", "sports"): [
        ("Underdogs stun champions in extra-time thriller",
         "A stoppage-time equaliser and a composed penalty shoot-out sealed one of "
         "the great cup upsets.", "#7f1d1d"),
        ("Record transfer fee agreed for teenage striker",
         "The deal eclipses the previous record set only last summer.", ""),
        ("Marathon world record falls by nineteen seconds",
         "Perfect conditions and a fearless early pace delivered a historic run.", "#9a3412"),
    ],
    ("arts-and-letters", "culture"): [
        ("Long-lost manuscript by celebrated novelist discovered in archive",
         "Scholars authenticated the handwritten draft, which predates the "
         "author's debut by six years and will be published next spring.", "#78350f"),
        ("Film festival opens with restored silent-era classic",
         "The restoration took eight years and drew a standing ovation.", ""),
        ("Museum returns disputed artefacts in landmark repatriation",
         "The agreement is expected to set a template for similar claims.", "#92400e"),
    ],
}

ATOM_FEED = ("tech-chronicle", "technology")  # rendered as Atom, rest as RSS


def _rss(source: str, items: list[tuple], now: datetime) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">',
        f"<channel><title>{source}</title><link>https://example.com/{source}</link>",
        f"<description>{source} fixture feed</description>",
    ]
    for i, (title, summary, color) in enumerate(items):
        published = format_datetime(now - timedelta(minutes=25 + i * 47))
        media = ""
        if color:
            media = f'<media:content url="{_svg_image(color, source[:1].upper())}" medium="image"/>'
        parts.append(
            f"<item><title>{title}</title>"
            f"<link>https://example.com/{source}/{i}</link>"
            f"<description>{summary}</description>"
            f"<pubDate>{published}</pubDate>{media}</item>"
        )
    parts.append("</channel></rss>")
    return "\n".join(parts)


def _atom(source: str, items: list[tuple], now: datetime) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">',
        f"<title>{source}</title><id>urn:{source}</id>",
    ]
    for i, (title, summary, color) in enumerate(items):
        published = (now - timedelta(minutes=30 + i * 53)).strftime("%Y-%m-%dT%H:%M:%SZ")
        media = ""
        if color:
            media = f'<media:thumbnail url="{_svg_image(color, source[:1].upper())}"/>'
        parts.append(
            f"<entry><title>{title}</title>"
            f'<link rel="alternate" href="https://example.com/{source}/{i}"/>'
            f"<summary>{summary}</summary>"
            f"<published>{published}</published>{media}</entry>"
        )
    parts.append("</feed>")
    return "\n".join(parts)


def generate(out_dir: Path, now: datetime | None = None) -> list[Path]:
    now = now or datetime.now(timezone.utc)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for (source, section), items in STORIES.items():
        builder = _atom if (source, section) == ATOM_FEED else _rss
        path = out_dir / f"{source}__{section}.xml"
        path.write_text(builder(source, items, now), encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tests/fixtures")
    for p in generate(target):
        print(p)
