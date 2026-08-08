"""Render the selected stories into a self-contained FT-style front page."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone

from .parse import Article

PAPER_NAME = "The Daily Dispatch"
TAGLINE = "News from all over the web, gathered every hour"


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _iso(dt: datetime | None) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if dt else ""


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(".,;: ") + "…"


def _time_el(dt: datetime | None) -> str:
    if not dt:
        return ""
    return (
        f'<time datetime="{_iso(dt)}" data-reltime>'
        f'{dt.astimezone(timezone.utc).strftime("%H:%M")} UTC</time>'
    )


def _meta_line(art: Article) -> str:
    parts = [f'<span class="source">{_esc(art.source)}</span>']
    time_el = _time_el(art.published)
    if time_el:
        parts.append(time_el)
    return f'<p class="meta">{" · ".join(parts)}</p>'


def _img(art: Article, cls: str = "") -> str:
    if not art.image:
        return ""
    return (
        f'<img class="{cls}" src="{_esc(art.image)}" alt="{_esc(art.title)}" '
        f'loading="lazy" onerror="this.remove()">'
    )


def _lead_html(art: Article) -> str:
    return f"""
    <article class="lead-story">
      <div class="lead-text">
        <p class="kicker">{_esc(art.section)}</p>
        <h2><a href="{_esc(art.link)}">{_esc(art.title)}</a></h2>
        <p class="standfirst">{_esc(_clip(art.summary, 320))}</p>
        {_meta_line(art)}
      </div>
      {f'<figure class="lead-figure">{_img(art, "lead-img")}</figure>' if art.image else ""}
    </article>"""


def _top_card(art: Article) -> str:
    return f"""
      <article class="top-card">
        {_img(art, "card-img")}
        <p class="kicker">{_esc(art.section)}</p>
        <h3><a href="{_esc(art.link)}">{_esc(art.title)}</a></h3>
        <p class="card-summary">{_esc(_clip(art.summary, 140))}</p>
        {_meta_line(art)}
      </article>"""


def _latest_item(art: Article) -> str:
    return f"""
        <li>
          <a href="{_esc(art.link)}">{_esc(art.title)}</a>
          {_meta_line(art)}
        </li>"""


def _section_block(name: str, arts: list[Article]) -> str:
    first, rest = arts[0], arts[1:]
    lead = f"""
        <article class="section-lead">
          {_img(first, "section-img")}
          <h4><a href="{_esc(first.link)}">{_esc(first.title)}</a></h4>
          <p class="card-summary">{_esc(_clip(first.summary, 150))}</p>
          {_meta_line(first)}
        </article>"""
    items = "\n".join(
        f"""
          <li>
            <a href="{_esc(a.link)}">{_esc(a.title)}</a>
            {_meta_line(a)}
          </li>"""
        for a in rest
    )
    return f"""
    <section class="news-section" id="{name.lower()}" aria-label="{_esc(name)}">
      <h3 class="section-title"><span>{_esc(name)}</span></h3>
      <div class="section-grid">
        {lead}
        <ul class="section-list">{items}</ul>
      </div>
    </section>"""


CSS = """
:root {
  --paper: #fff1e5; --paper-deep: #f2e5da; --ink: #33302e; --ink-soft: #66605c;
  --accent: #990f3d; --rule: #ccc1b7; --rule-dark: #33302e; --link-hover: #0d7680;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: var(--paper); color: var(--ink);
  font-family: Georgia, 'Times New Roman', serif;
  line-height: 1.45; -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 1220px; margin: 0 auto; padding: 0 20px; }
a { color: inherit; text-decoration: none; }
a:hover { color: var(--link-hover); }
img { max-width: 100%; display: block; }

.topbar {
  display: flex; justify-content: space-between; align-items: center;
  font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 12px;
  letter-spacing: .04em; color: var(--ink-soft);
  padding: 10px 0; border-bottom: 1px solid var(--rule);
}
.masthead { text-align: center; padding: 26px 0 14px; }
.masthead h1 {
  font-size: clamp(40px, 7vw, 74px); font-weight: 400; letter-spacing: .01em;
  font-variant: small-caps;
}
.masthead .tagline {
  font-style: italic; color: var(--ink-soft); font-size: 15px; margin-top: 4px;
}
.nav {
  border-top: 1px solid var(--rule-dark); border-bottom: 3px double var(--rule-dark);
  margin-top: 16px;
}
.nav ul {
  display: flex; flex-wrap: wrap; justify-content: center; gap: 6px 30px;
  list-style: none; padding: 10px 0;
  font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 13px;
  letter-spacing: .12em; text-transform: uppercase;
}
.nav a:hover { color: var(--accent); }

.front { display: grid; grid-template-columns: 1fr 300px; gap: 34px; padding: 30px 0; }
.lead-story { display: grid; grid-template-columns: 1fr 1fr; gap: 26px; align-items: start; }
.lead-story.no-image { grid-template-columns: 1fr; }
.kicker {
  font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 12px;
  letter-spacing: .14em; text-transform: uppercase; color: var(--accent);
  margin-bottom: 8px;
}
.lead-story h2 { font-size: clamp(28px, 3.4vw, 42px); font-weight: 500; line-height: 1.12; margin-bottom: 14px; }
.standfirst { font-size: 18px; color: var(--ink-soft); margin-bottom: 12px; }
.meta {
  font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 12px;
  color: var(--ink-soft); margin-top: 6px;
}
.meta .source { font-weight: 600; }
.lead-figure { border: 1px solid var(--rule); }
.lead-img, .card-img, .section-img { width: 100%; aspect-ratio: 3 / 2; object-fit: cover; }

.latest { border-left: 1px solid var(--rule); padding-left: 26px; }
.latest h3, .section-title {
  font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 13px;
  letter-spacing: .14em; text-transform: uppercase; font-weight: 700;
}
.latest h3 { margin-bottom: 14px; padding-bottom: 8px; border-bottom: 3px solid var(--rule-dark); }
.latest ul { list-style: none; }
.latest li { padding: 11px 0; border-bottom: 1px dotted var(--rule); font-size: 15px; line-height: 1.3; }
.latest li:last-child { border-bottom: none; }

.top-row {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px;
  padding: 26px 0 30px; border-top: 1px solid var(--rule-dark);
}
.top-card h3 { font-size: 20px; font-weight: 500; line-height: 1.2; margin: 8px 0; }
.top-card .card-img { margin-bottom: 12px; border: 1px solid var(--rule); }
.card-summary { font-size: 14px; color: var(--ink-soft); }

.news-section { border-top: 1px solid var(--rule-dark); padding: 20px 0 30px; }
.section-title { margin-bottom: 18px; }
.section-title span { color: var(--accent); }
.section-grid { display: grid; grid-template-columns: 340px 1fr; gap: 34px; }
.section-lead h4 { font-size: 21px; font-weight: 500; line-height: 1.2; margin: 10px 0 8px; }
.section-img { border: 1px solid var(--rule); }
.section-list { list-style: none; columns: 2; column-gap: 34px; }
.section-list li {
  break-inside: avoid; padding: 10px 0; border-bottom: 1px dotted var(--rule);
  font-size: 16px; line-height: 1.3;
}

.foot {
  border-top: 3px double var(--rule-dark); margin-top: 10px; padding: 22px 0 44px;
  text-align: center; font-family: 'Helvetica Neue', Arial, sans-serif;
  font-size: 12px; color: var(--ink-soft);
}
.foot a { text-decoration: underline; }

@media (max-width: 980px) {
  .front { grid-template-columns: 1fr; }
  .latest { border-left: none; padding-left: 0; border-top: 1px solid var(--rule-dark); padding-top: 18px; }
  .top-row { grid-template-columns: 1fr; }
  .section-grid { grid-template-columns: 1fr; }
  .section-list { columns: 1; }
}
@media (max-width: 700px) {
  .lead-story { grid-template-columns: 1fr; }
  .lead-figure { order: -1; }
}
"""

JS = """
(function () {
  var units = [[86400, 'day'], [3600, 'hour'], [60, 'minute']];
  function rel(iso) {
    var s = (Date.now() - new Date(iso).getTime()) / 1000;
    if (s < 60) return 'just now';
    for (var i = 0; i < units.length; i++) {
      var n = Math.floor(s / units[i][0]);
      if (n >= 1) return n + ' ' + units[i][1] + (n > 1 ? 's' : '') + ' ago';
    }
    return 'just now';
  }
  document.querySelectorAll('time[data-reltime]').forEach(function (el) {
    var iso = el.getAttribute('datetime');
    if (iso) el.textContent = rel(iso);
  });
})();
"""


def render_page(page: dict, sections_order: list[str]) -> str:
    now: datetime = page["generated"]
    dateline = now.strftime("%A, %d %B %Y")
    updated = now.strftime("%H:%M UTC")
    lead: Article | None = page["lead"]

    nav_items = "\n".join(
        f'<li><a href="#{s.lower()}">{_esc(s)}</a></li>'
        for s in sections_order
        if s in page["sections"]
    )
    top_cards = "\n".join(_top_card(a) for a in page["top"])
    latest_items = "\n".join(_latest_item(a) for a in page["latest"])
    section_blocks = "\n".join(
        _section_block(name, page["sections"][name])
        for name in sections_order
        if name in page["sections"]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="900">
<meta name="description" content="{_esc(TAGLINE)}.">
<title>{PAPER_NAME} — {dateline}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="topbar">
      <span class="dateline">{dateline}</span>
      <span>Updated <time datetime="{_iso(now)}">{updated}</time></span>
    </div>
    <div class="masthead">
      <h1>{PAPER_NAME}</h1>
      <p class="tagline">{TAGLINE}</p>
    </div>
    <nav class="nav" aria-label="Sections"><ul>
{nav_items}
    </ul></nav>
  </header>

  <main>
    <div class="front">
      <div class="front-main">
{_lead_html(lead) if lead else '<p class="standfirst">No stories collected yet — check back shortly.</p>'}
      </div>
      <aside class="latest" aria-label="Latest news">
        <h3>Latest</h3>
        <ul>
{latest_items}
        </ul>
      </aside>
    </div>

    <div class="top-row">
{top_cards}
    </div>

{section_blocks}
  </main>

  <footer class="foot">
    <p>{PAPER_NAME} is generated automatically from public RSS feeds. Headlines link to the
    original publishers, who retain all rights to their content.</p>
    <p>Built with <a href="https://github.com/sharjeel45557/news-collector">news-collector</a>.
    Page regenerates hourly; last build {dateline} at {updated}.</p>
  </footer>
</div>
<script>{JS}</script>
</body>
</html>
"""


def to_json(page: dict) -> str:
    def art(a: Article) -> dict:
        return {
            "title": a.title,
            "link": a.link,
            "summary": a.summary,
            "published": _iso(a.published) or None,
            "image": a.image,
            "source": a.source,
            "section": a.section,
        }

    return json.dumps(
        {
            "generated": _iso(page["generated"]),
            "lead": art(page["lead"]) if page["lead"] else None,
            "top": [art(a) for a in page["top"]],
            "latest": [art(a) for a in page["latest"]],
            "sections": {s: [art(a) for a in arts] for s, arts in page["sections"].items()},
        },
        indent=2,
        ensure_ascii=False,
    )
