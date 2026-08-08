"""CLI entry point.

    python -m collector                 # fetch live feeds, write docs/
    python -m collector --fixtures DIR  # build from local XML fixtures (offline)
    python -m collector --out PATH      # output directory (default: docs)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .feeds import FEEDS, SECTIONS, Feed
from .fetch import fetch_all
from .parse import parse_feed
from .rank import select
from .render import render_page, to_json


def _load_fixtures(fixture_dir: Path) -> list:
    """Fixture files are named <source-slug>__<section>.xml."""
    articles = []
    for path in sorted(fixture_dir.glob("*.xml")):
        stem_parts = path.stem.split("__")
        source = stem_parts[0].replace("-", " ").title()
        section = stem_parts[1].title() if len(stem_parts) > 1 else "World"
        articles.extend(parse_feed(path.read_text(encoding="utf-8"), source, section))
    return articles


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="collector", description=__doc__)
    parser.add_argument("--fixtures", type=Path, help="build from local XML fixtures")
    parser.add_argument("--out", type=Path, default=Path("docs"), help="output directory")
    args = parser.parse_args(argv)

    if args.fixtures:
        articles = _load_fixtures(args.fixtures)
    else:
        articles = fetch_all(list(FEEDS))

    if not articles:
        print("error: no articles collected from any feed", file=sys.stderr)
        return 1

    page = select(articles, SECTIONS)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "index.html").write_text(render_page(page, SECTIONS), encoding="utf-8")
    (args.out / "news.json").write_text(to_json(page), encoding="utf-8")
    total = sum(len(v) for v in page["sections"].values()) + len(page["top"]) + len(
        page["latest"]
    ) + (1 if page["lead"] else 0)
    print(f"built {args.out}/index.html with {total} stories from {len(articles)} collected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
