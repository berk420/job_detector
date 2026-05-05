"""
Browser-based LinkedIn scraper using Playwright.
Opens a real Chrome window, logs in once, and keeps the session alive.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Page, BrowserContext

COOKIES_FILE = Path(__file__).parent.parent / "data" / "li_cookies.json"

SEARCH_URL = (
    "https://www.linkedin.com/search/results/content/"
    "?keywords=%28%22%23hiring%22%20OR%20%C4%B0%C5%9Fe%20al%C4%B1m%29%20AND%20%28Yaz%C4%B1l%C4%B1m%20OR%20Software%29"
    "&origin=FACETED_SEARCH"
    "&sortBy=%5B%22date_posted%22%5D"
)


class LinkedInBrowser:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self._pw = None
        self._browser = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def start(self):
        self._pw = sync_playwright().start()
        # Try installed Chrome first, fall back to Playwright's Chromium
        try:
            self._browser = self._pw.chromium.launch(
                headless=self.headless,
                channel="chrome",
                args=["--start-maximized"],
            )
        except Exception:
            self._browser = self._pw.chromium.launch(
                headless=self.headless,
                args=["--start-maximized"],
            )

        self._context = self._browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        self._page = self._context.new_page()

        # Load saved cookies if they exist
        if COOKIES_FILE.exists():
            try:
                cookies = json.loads(COOKIES_FILE.read_text(encoding="utf-8"))
                self._context.add_cookies(cookies)
                print("Loaded saved session cookies")
            except Exception:
                pass

    def is_logged_in(self) -> bool:
        try:
            self._page.goto("https://www.linkedin.com/feed/", timeout=20000, wait_until="domcontentloaded")
            time.sleep(2)
            return "/login" not in self._page.url and "/checkpoint" not in self._page.url
        except Exception:
            return False

    def login(self, email: str, password: str) -> bool:
        print("Opening LinkedIn login page...")
        self._page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        time.sleep(1)

        self._page.fill("#username", email)
        time.sleep(0.5)
        self._page.fill("#password", password)
        time.sleep(0.5)
        self._page.click('button[type="submit"]')

        # Wait up to 30s for redirect away from login page
        try:
            self._page.wait_for_function(
                "() => !window.location.href.includes('/login')",
                timeout=30000,
            )
        except Exception:
            pass

        current_url = self._page.url
        if "/checkpoint" in current_url or "/challenge" in current_url:
            print("LinkedIn security check triggered — please complete it in the browser window")
            # Wait up to 2 minutes for manual completion
            try:
                self._page.wait_for_function(
                    "() => window.location.href.includes('/feed')",
                    timeout=120000,
                )
            except Exception:
                return False

        if "/feed" in self._page.url or "linkedin.com" in self._page.url and "/login" not in self._page.url:
            self._save_cookies()
            print("Login successful")
            return True

        print(f"Login failed — current URL: {self._page.url}")
        return False

    def fetch_posts(self) -> list[dict]:
        print("Navigating to search page...")
        self._page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)  # wait for dynamic content

        # Scroll down a bit to trigger lazy loading
        self._page.evaluate("window.scrollBy(0, 600)")
        time.sleep(2)

        posts = self._page.evaluate(_JS_EXTRACT_POSTS)
        print(f"Found {len(posts)} posts on page")
        self._save_cookies()
        return posts

    def close(self):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def _save_cookies(self):
        try:
            COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            cookies = self._context.cookies()
            COOKIES_FILE.write_text(
                json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            print(f"Could not save cookies: {e}")


# JavaScript run inside the browser page to extract post data
_JS_EXTRACT_POSTS = """
() => {
    const results = [];
    const seen = new Set();

    // LinkedIn search result containers
    const containers = document.querySelectorAll(
        '[data-chameleon-result-urn], .reusable-search__result-container'
    );

    containers.forEach(container => {
        // Get URN (unique post ID)
        const urn = container.getAttribute('data-chameleon-result-urn')
            || container.querySelector('[data-id]')?.getAttribute('data-id')
            || '';

        if (!urn || seen.has(urn)) return;
        seen.add(urn);

        // Post text — try multiple selectors
        const textEl = container.querySelector(
            '.update-components-text__text-view, ' +
            '.feed-shared-update-v2__description-wrapper, ' +
            '.update-components-text, ' +
            '.break-words'
        );
        const text = textEl ? textEl.innerText.trim() : '';
        if (!text || text.length < 20) return;

        // Author name
        const nameEl = container.querySelector(
            '.update-components-actor__name span[aria-hidden="true"], ' +
            '.update-components-actor__name, ' +
            '.app-aware-link .visually-hidden'
        );
        const authorName = nameEl ? nameEl.innerText.trim() : '';

        // Author title/description
        const titleEl = container.querySelector(
            '.update-components-actor__description, ' +
            '.update-components-actor__sub-description'
        );
        const authorTitle = titleEl ? titleEl.innerText.trim() : '';

        // Timestamp
        const timeEl = container.querySelector('time');
        const timeStr = timeEl ? (timeEl.getAttribute('datetime') || timeEl.innerText) : '';

        // Post URL
        const url = urn.startsWith('urn:li:activity:')
            ? 'https://www.linkedin.com/feed/update/' + urn + '/'
            : urn.startsWith('urn:li:ugcPost:')
            ? 'https://www.linkedin.com/feed/update/' + urn + '/'
            : '';

        results.push({ id: urn, text, authorName, authorTitle, url, timeStr });
    });

    return results;
}
"""
