from datetime import datetime, timezone

from collector.parse import parse_feed

RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
<channel>
  <title>Sample</title>
  <item>
    <title>Markets rally as &amp; inflation cools</title>
    <link>https://example.com/story-1</link>
    <description>&lt;p&gt;Stocks &lt;b&gt;jumped&lt;/b&gt; on Friday.&lt;/p&gt;</description>
    <pubDate>Fri, 07 Aug 2026 09:30:00 GMT</pubDate>
    <media:content url="https://img.example.com/a.jpg" medium="image"/>
  </item>
  <item>
    <title>Story without image</title>
    <link>https://example.com/story-2</link>
    <description>Plain text summary with an inline &lt;img src="https://img.example.com/inline.png"&gt; tag.</description>
    <pubDate>Fri, 07 Aug 2026 08:00:00 +0000</pubDate>
  </item>
  <item>
    <title>Missing link is skipped</title>
  </item>
</channel>
</rss>"""

ATOM_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Sample</title>
  <entry>
    <title>Probe reaches outer moon</title>
    <link rel="self" href="https://example.com/self"/>
    <link rel="alternate" href="https://example.com/atom-1"/>
    <summary>The spacecraft made its closest approach.</summary>
    <published>2026-08-07T10:15:00Z</published>
  </entry>
</feed>"""


def test_rss_parsing_extracts_fields():
    articles = parse_feed(RSS_SAMPLE, "Sample Wire", "Markets")
    assert len(articles) == 2  # item without link dropped
    first = articles[0]
    assert first.title == "Markets rally as & inflation cools"
    assert first.link == "https://example.com/story-1"
    assert first.summary == "Stocks jumped on Friday."
    assert first.published == datetime(2026, 8, 7, 9, 30, tzinfo=timezone.utc)
    assert first.image == "https://img.example.com/a.jpg"
    assert first.source == "Sample Wire"
    assert first.section == "Markets"


def test_rss_image_falls_back_to_inline_img_tag():
    articles = parse_feed(RSS_SAMPLE, "Sample Wire", "Markets")
    assert articles[1].image == "https://img.example.com/inline.png"


def test_atom_parsing_uses_alternate_link():
    articles = parse_feed(ATOM_SAMPLE, "Atom Wire", "Science")
    assert len(articles) == 1
    art = articles[0]
    assert art.title == "Probe reaches outer moon"
    assert art.link == "https://example.com/atom-1"
    assert art.published == datetime(2026, 8, 7, 10, 15, tzinfo=timezone.utc)


def test_malformed_xml_returns_empty_list():
    assert parse_feed("<rss><channel><item>", "X", "World") == []
    assert parse_feed("not xml at all", "X", "World") == []
