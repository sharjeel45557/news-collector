"""End-to-end test: build the page from fixtures, serve it over HTTP, and
verify it renders and behaves correctly in a real Chromium browser."""

from __future__ import annotations

import http.server
import os
import socket
import subprocess
import sys
import threading
from functools import partial
from pathlib import Path

import pytest

playwright_api = pytest.importorskip(
    "playwright.sync_api", reason="playwright not installed; pip install -r requirements-dev.txt"
)

REPO = Path(__file__).resolve().parents[2]


def _chromium_path() -> str | None:
    """Prefer a pre-provisioned Chromium if playwright's own isn't installed."""
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if not base:
        return None
    for pattern in ("chromium-*/chrome-linux/chrome", "chromium-*/chrome-linux/headless_shell",
                    "chromium_headless_shell-*/chrome-linux/headless_shell"):
        matches = sorted(Path(base).glob(pattern))
        if matches:
            return str(matches[0])
    return None


@pytest.fixture(scope="module")
def site_url(tmp_path_factory):
    """Generate fixtures, run the collector, serve the output directory."""
    workdir = tmp_path_factory.mktemp("e2e")
    fixtures = workdir / "fixtures"
    out = workdir / "docs"
    subprocess.run(
        [sys.executable, "tests/gen_fixtures.py", str(fixtures)],
        cwd=REPO, check=True, capture_output=True,
    )
    build = subprocess.run(
        [sys.executable, "-m", "collector", "--fixtures", str(fixtures), "--out", str(out)],
        cwd=REPO, check=True, capture_output=True, text=True,
    )
    assert "built" in build.stdout
    assert (out / "index.html").exists() and (out / "news.json").exists()

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}/index.html"
    server.shutdown()


@pytest.fixture(scope="module")
def browser():
    with playwright_api.sync_playwright() as pw:
        launch_kwargs = {}
        exe = _chromium_path()
        if exe:
            launch_kwargs["executable_path"] = exe
        browser = pw.chromium.launch(**launch_kwargs)
        yield browser
        browser.close()


@pytest.fixture(scope="module")
def page(browser, site_url):
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    pg.goto(site_url, wait_until="load")
    yield pg
    pg.close()


def test_masthead_and_title(page):
    assert "The Daily Dispatch" in page.title()
    masthead = page.locator(".masthead h1")
    assert masthead.is_visible()
    assert masthead.inner_text().strip() == "The Daily Dispatch"


def test_lead_story_renders_with_image_and_link(page):
    lead = page.locator(".lead-story")
    assert lead.count() == 1
    headline = lead.locator("h2 a")
    assert headline.is_visible()
    assert len(headline.inner_text()) > 10
    assert headline.get_attribute("href").startswith("https://")
    img = lead.locator("img")
    assert img.count() == 1
    assert page.evaluate("el => el.naturalWidth > 0", img.element_handle())


def test_latest_rail_has_stories_with_relative_times(page):
    items = page.locator(".latest li")
    assert items.count() >= 5
    first_time = page.locator(".latest li time").first
    assert "ago" in first_time.inner_text() or "just now" in first_time.inner_text()


def test_all_sections_present_and_populated(page):
    sections = page.locator(".news-section")
    assert sections.count() >= 5
    for i in range(sections.count()):
        section = sections.nth(i)
        assert section.locator(".section-lead h4 a").count() == 1
        assert section.locator(".section-list li").count() >= 1


def test_nav_links_jump_to_sections(page):
    nav_links = page.locator(".nav a")
    assert nav_links.count() >= 5
    target = nav_links.last.get_attribute("href").lstrip("#")
    nav_links.last.click()
    page.wait_for_function(f"location.hash === '#{target}'")
    assert page.locator(f"#{target}").is_visible()


def test_every_story_links_to_publisher(page):
    hrefs = page.eval_on_selector_all(
        "main a[href]", "els => els.map(e => e.getAttribute('href'))"
    )
    assert len(hrefs) >= 25
    assert all(h.startswith("https://") for h in hrefs)


def test_images_all_load(page):
    broken = page.evaluate(
        "() => [...document.querySelectorAll('img')].filter(i => !i.naturalWidth).length"
    )
    assert broken == 0


def test_news_json_is_served_and_valid(page, site_url):
    data = page.evaluate(
        "url => fetch(url).then(r => r.json())", site_url.replace("index.html", "news.json")
    )
    assert data["lead"]["title"]
    assert data["sections"]


def test_mobile_layout_has_no_horizontal_overflow(browser, site_url):
    pg = browser.new_page(viewport={"width": 390, "height": 844})
    pg.goto(site_url, wait_until="load")
    overflow = pg.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0
    assert pg.locator(".masthead h1").is_visible()
    pg.close()
