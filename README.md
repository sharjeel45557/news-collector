# The Daily Dispatch — automated news front page

An automated news aggregator that collects headlines from ~30 RSS/Atom feeds
across major publishers (BBC, The Guardian, NYT, WSJ, CNBC, Al Jazeera,
TechCrunch, The Verge, ESPN, ScienceDaily, and more) and renders them as a
broadsheet-style front page inspired by the Financial Times / Wall Street
Journal — lead story, latest-news rail, top-story cards, and themed sections
(World, Business, Markets, Technology, Science, Sports, Culture).

The collector is **pure Python stdlib** — nothing to install to run it.

## How it works

```
collector/feeds.py   curated feed list, grouped by section
collector/fetch.py   parallel HTTP fetching with per-feed failure tolerance
collector/parse.py   RSS 2.0 + Atom parsing (images, dates, HTML stripping)
collector/rank.py    dedupe (URL + near-identical headlines), freshness
                     filter (48h), lead/top/latest/section selection
collector/render.py  self-contained FT-style HTML page + news.json
```

Output goes to `docs/` (`index.html` + `news.json`), ready for GitHub Pages.

## Automation

`.github/workflows/collect.yml` runs **hourly** (and on demand via
*Run workflow*): it fetches all feeds, rebuilds `docs/`, commits the refresh,
and deploys to GitHub Pages. The page also carries a 15-minute meta-refresh so
an open browser tab keeps itself current.

To enable hosting: repository **Settings → Pages → Source: GitHub Actions**.

## Run locally

```bash
python -m collector                    # live fetch → docs/index.html
python -m collector --out /tmp/site    # custom output dir

# fully offline (generated fixture feeds):
python tests/gen_fixtures.py /tmp/fixtures
python -m collector --fixtures /tmp/fixtures --out /tmp/site
```

Open `docs/index.html` in a browser.

## Tests

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium   # once, for e2e
pytest tests -k "not e2e"               # unit tests (parser, ranking, rendering)
pytest tests/e2e                        # end-to-end: build → serve → real Chromium
```

The e2e suite builds the page from fixture feeds, serves it over HTTP, and
drives a real browser: masthead, lead story with image, latest rail with
relative timestamps, section navigation, publisher links, image loading, JSON
endpoint, and mobile-viewport layout.

## Notes

- Headlines and summaries link to and credit the original publishers, who
  retain all rights to their content.
- Feeds are configured in `collector/feeds.py` — add or remove `Feed` entries
  and the page adapts automatically.
