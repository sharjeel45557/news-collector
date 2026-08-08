from datetime import datetime, timedelta, timezone

from collector.parse import Article
from collector.rank import dedupe, select

NOW = datetime(2026, 8, 8, 5, 0, tzinfo=timezone.utc)


def art(title, link, hours_ago=1.0, image=None, summary="A reasonably long summary "
        "so the story qualifies for lead placement on the page.", section="World"):
    return Article(
        title=title,
        link=link,
        summary=summary,
        published=NOW - timedelta(hours=hours_ago),
        image=image,
        source="Test Wire",
        section=section,
    )


def test_dedupe_same_url_keeps_richest_copy():
    plain = art("Summit ends with agreement", "https://a.com/x")
    rich = art("Summit ends with agreement", "https://www.a.com/x/", image="https://i.jpg")
    kept = dedupe([plain, rich])
    assert len(kept) == 1
    assert kept[0].image == "https://i.jpg"


def test_dedupe_drops_near_identical_headlines_across_sources():
    a = art("Central bank raises interest rates to fight inflation", "https://a.com/1")
    b = art("Central bank raises interest rates to combat inflation", "https://b.com/2")
    c = art("Local team wins championship final", "https://c.com/3")
    kept = dedupe([a, b, c])
    titles = {k.title for k in kept}
    assert len(kept) == 2
    assert "Local team wins championship final" in titles


def test_select_filters_stale_stories():
    fresh = art("Fresh story about the morning markets", "https://a.com/fresh", hours_ago=2)
    stale = art("Stale story from last week entirely", "https://a.com/stale", hours_ago=100)
    page = select([fresh, stale], ["World"], now=NOW)
    all_titles = [a.title for arts in page["sections"].values() for a in arts]
    if page["lead"]:
        all_titles.append(page["lead"].title)
    assert any("Fresh" in t for t in all_titles)
    assert not any("Stale" in t for t in all_titles)


def test_select_builds_full_page_structure():
    articles = [
        art(f"Distinct headline number {i} about topic {chr(65 + i)}",
            f"https://site{i}.com/{i}", hours_ago=i * 0.5,
            image=f"https://img/{i}.jpg" if i % 2 == 0 else None,
            section=["World", "Business", "Technology"][i % 3])
        for i in range(15)
    ]
    page = select(articles, ["World", "Business", "Technology"], now=NOW)
    assert page["lead"] is not None
    assert page["lead"].image  # lead must carry an image
    assert 1 <= len(page["top"]) <= 3
    assert all(a.image for a in page["top"])
    assert page["latest"]
    assert set(page["sections"]) <= {"World", "Business", "Technology"}
    # no story appears twice on the page
    ids = [id(page["lead"])] + [id(a) for a in page["top"]] + [
        id(a) for arts in page["sections"].values() for a in arts
    ]
    assert len(ids) == len(set(ids))
