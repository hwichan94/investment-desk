"""Playwright browser session for Fanding, driven by a stored session state."""
from __future__ import annotations

import logging
from typing import Any

from desk.errors import AuthRequired, DomChanged, PageTimeout

LOGGER = logging.getLogger(__name__)
NAV_TIMEOUT_MS = 45_000
RENDER_TIMEOUT_MS = 30_000
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _is_timeout(exc: Exception) -> bool:
    return "Timeout" in type(exc).__name__ or "timeout" in str(exc).lower()


class FandingBrowser:
    def __init__(self, selectors: dict[str, str], storage_state: dict[str, Any] | None,
                 headless: bool = True):
        self.selectors = selectors
        self.storage_state = storage_state
        self.headless = headless
        self._pw: Any = None
        self._browser: Any = None
        self.context: Any = None

    def __enter__(self) -> "FandingBrowser":
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.launch(headless=self.headless)
            self.context = self._browser.new_context(
                storage_state=self.storage_state,
                viewport={"width": 1440, "height": 1000},
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                user_agent=USER_AGENT,
            )
        except Exception:
            self.close()
            raise
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def close(self) -> None:
        for closer in (lambda: self.context and self.context.close(),
                       lambda: self._browser and self._browser.close(),
                       lambda: self._pw and self._pw.stop()):
            try:
                closer()
            except Exception:
                pass
        self.context = self._browser = self._pw = None

    def current_state(self) -> dict[str, Any]:
        return self.context.storage_state()

    def is_authenticated(self, page: Any) -> bool:
        try:
            page.wait_for_selector(self.selectors["authenticated_signal"], state="attached",
                                   timeout=10_000)
            return True
        except Exception:
            return False

    def feed_html(self, feed_url: str, scrolls: int = 2) -> str:
        page = self.context.new_page()
        try:
            try:
                page.goto(feed_url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
            except Exception as exc:
                raise PageTimeout(f"feed navigation failed: {exc}") from exc
            if not self.is_authenticated(page):
                raise AuthRequired("Fanding session expired or missing; log in again.")
            try:
                page.wait_for_selector(self.selectors["feed_container"], timeout=RENDER_TIMEOUT_MS)
            except Exception as exc:
                if _is_timeout(exc):
                    raise DomChanged("feed container not found after login check") from exc
                raise
            try:
                page.wait_for_selector(self.selectors["post_link"], timeout=15_000)
            except Exception:
                LOGGER.info("No post links rendered yet on the feed")
            for _ in range(scrolls):  # load a few more cards for catch-up after downtime
                page.mouse.wheel(0, 4000)
                page.wait_for_timeout(1500)
            return page.content()
        finally:
            page.close()

    def post_html(self, url: str) -> str:
        page = self.context.new_page()
        try:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
                page.wait_for_selector(self.selectors["post_root"], state="attached",
                                       timeout=RENDER_TIMEOUT_MS)
                page.wait_for_function(
                    """([bodySel, locked]) => {
                        const b = document.querySelector(bodySel);
                        return Boolean(b && b.textContent.trim().length > 0)
                            || (document.body.innerText || '').includes(locked);
                    }""",
                    arg=[self.selectors["post_body"], self.selectors["locked_marker"]],
                    timeout=RENDER_TIMEOUT_MS,
                )
            except Exception as exc:
                if _is_timeout(exc):
                    raise PageTimeout(f"post did not render: {url}") from exc
                raise
            return page.content()
        finally:
            page.close()


def interactive_login(selectors: dict[str, str], feed_url: str,
                      existing_state: dict[str, Any] | None, timeout_s: int = 600) -> dict[str, Any] | None:
    """Open a visible browser; the user signs in by hand. Returns the session state."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        try:
            context = browser.new_context(storage_state=existing_state, locale="ko-KR",
                                          timezone_id="Asia/Seoul", viewport=None)
            page = context.new_page()
            page.goto(feed_url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
            try:
                page.wait_for_selector(selectors["authenticated_signal"], state="attached",
                                       timeout=timeout_s * 1000)
            except Exception:
                return None
            page.wait_for_timeout(2000)  # let the app finish writing tokens
            return context.storage_state()
        finally:
            browser.close()
