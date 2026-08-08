from datetime import datetime, timezone

from collector.parse import Article
from collector.rank import select
from collector.render import PAPER_NAME, render_page, to_json

NOW = datetime(2026, 8, 8, 5, 0, tzinfo=timezone.utc)


TITLES = [
    "Summit ends with sweeping accord <script>alert('xss')</script>",
    "Markets climb on cooling inflation figures",
    "New chip factory breaks ground in desert town",
    "Rivers crest as storm system moves east",
    "Airline merger wins final approval",
    "Vaccine trial reports strong late-stage results",
    "Championship decided in dramatic penalty shootout",
    "Museum unveils long-lost masterpiece",
    "Satellite launch completes global network",
    "Harvest forecast raised after ideal weather",
]


def _page():
    articles = [
        Article(
            title=title,
            link=f"https://example.com/{i}",
            summary="A sufficiently long summary for placement on the front page, "
            "covering the essential details of the story at hand.",
            published=NOW,
            image=f"https://img.example.com/{i}.jpg" if i < 6 else None,
            source="Wire & Co",
            section=["World", "Business"][i % 2],
        )
        for i, title in enumerate(TITLES)
    ]
    return select(articles, ["World", "Business"], now=NOW)


def test_render_escapes_html_in_titles():
    html = render_page(_page(), ["World", "Business"])
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_render_contains_masthead_sections_and_dateline():
    html = render_page(_page(), ["World", "Business"])
    assert PAPER_NAME in html
    assert 'id="world"' in html
    assert 'id="business"' in html
    assert NOW.strftime("%A, %d %B %Y") in html
    assert "05:00 UTC" in html


def test_json_output_round_trips():
    import json

    data = json.loads(to_json(_page()))
    assert data["generated"] == "2026-08-08T05:00:00Z"
    assert data["lead"]["source"] == "Wire & Co"
    assert data["top"] and data["latest"] and data["sections"]
