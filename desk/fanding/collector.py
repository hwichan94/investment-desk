"""One Fanding check: feed -> new/changed posts -> JSON files + status record."""
from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any, Protocol

from desk import paths
from desk.errors import AuthRequired, DomChanged, LockedPost, PageTimeout, SessionUnavailable
from desk.fanding.parser import parse_feed_urls, parse_post_html, post_id_from_url
from desk.store import PostStore, read_json, write_json

LOGGER = logging.getLogger(__name__)
STATUS_FILE = "collector.json"
HISTORY_FILE = "collector-history.jsonl"
HISTORY_KEEP = 300

# Exit codes so the scheduler (GitHub Actions) can fail loudly and notify the user.
EXIT_OK = 0
EXIT_AUTH = 2
EXIT_DOM = 3
EXIT_BROWSER = 4


class Session(Protocol):
    def feed_html(self, feed_url: str) -> str: ...
    def post_html(self, url: str) -> str: ...


def _retry(op: Callable[[], str], attempts: int = 3, sleep: Callable[[float], None] = time.sleep) -> str:
    for attempt in range(attempts):
        try:
            return op()
        except PageTimeout:
            if attempt == attempts - 1:
                raise
            sleep(3 * (attempt + 1))
    raise AssertionError("unreachable")


def run_check(session: Session, store: PostStore, selectors: dict[str, str], now: datetime,
              feed_url: str = paths.FEED_URL, sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "OK", "message": "", "discovered": 0, "created": [], "updated": [],
        "unchanged": 0, "locked": 0, "failures": [],
    }
    feed = _retry(lambda: session.feed_html(feed_url), sleep=sleep)
    urls = parse_feed_urls(feed, selectors)
    result["discovered"] = len(urls)
    if not urls:
        raise DomChanged("feed rendered but no post links were parsed")
    known = store.known_ids()
    failed_before = read_json(paths.STATUS / "post_failures.json", {}) or {}
    for url in urls:
        post_id = post_id_from_url(url)
        try:
            html = _retry(lambda url=url: session.post_html(url), sleep=sleep)
            post = parse_post_html(html, url, now, selectors)
        except LockedPost:
            result["locked"] += 1
            continue
        except (PageTimeout, DomChanged) as exc:
            result["failures"].append({"post_id": post_id, "error": type(exc).__name__,
                                       "known": post_id in known})
            continue
        outcome = store.upsert(post)
        if outcome == "CREATED":
            result["created"].append(post_id)
        elif outcome == "UPDATED":
            result["updated"].append(post_id)
        else:
            result["unchanged"] += 1
        failed_before.pop(post_id, None)

    for failure in result["failures"]:
        entry = failed_before.setdefault(failure["post_id"], {"attempts": 0})
        entry["attempts"] += 1
        entry["last_error"] = failure["error"]
        entry["last_at"] = now.isoformat()
    write_json(paths.STATUS / "post_failures.json", failed_before)

    new_failures = [f for f in result["failures"] if not f["known"]]
    if new_failures:
        result["status"] = "PARTIAL"
        result["message"] = f"{len(new_failures)} new post(s) could not be read; will retry."
    if result["failures"] and len(result["failures"]) == len(urls) - result["locked"]:
        raise DomChanged("every readable post failed to parse")
    return result


def record_status(result: dict[str, Any], now: datetime) -> dict[str, Any]:
    previous = read_json(paths.STATUS / STATUS_FILE, {}) or {}
    status = dict(result)
    status["last_run_at"] = now.isoformat()
    healthy = result["status"] in ("OK", "PARTIAL")
    status["last_success_at"] = now.isoformat() if healthy else previous.get("last_success_at")
    status["consecutive_failures"] = 0 if healthy else previous.get("consecutive_failures", 0) + 1
    if result["status"] == "AUTH_REQUIRED":
        status["auth_required_since"] = previous.get("auth_required_since") or now.isoformat()
    write_json(paths.STATUS / STATUS_FILE, status)

    history = paths.STATUS / HISTORY_FILE
    lines = history.read_text(encoding="utf-8").splitlines() if history.exists() else []
    summary = {
        "at": now.isoformat(), "status": result["status"], "discovered": result["discovered"],
        "created": len(result["created"]), "updated": len(result["updated"]),
        "locked": result["locked"], "failed": len(result["failures"]),
    }
    lines.append(json.dumps(summary, ensure_ascii=False))
    history.write_text("\n".join(lines[-HISTORY_KEEP:]) + "\n", encoding="utf-8", newline="\n")
    return status


def failure_result(status: str, message: str) -> dict[str, Any]:
    return {"status": status, "message": message, "discovered": 0, "created": [], "updated": [],
            "unchanged": 0, "locked": 0, "failures": []}


def check(now: datetime, headless: bool = True) -> int:
    """Full check with a real browser. Returns a process exit code."""
    from desk.fanding import state as session_state
    from desk.fanding.browser import FandingBrowser
    from desk.fanding.parser import load_selectors

    selectors = load_selectors()
    store = PostStore()
    try:
        storage = session_state.load_state()
        with FandingBrowser(selectors, storage, headless=headless) as browser:
            result = run_check(browser, store, selectors, now)
            try:
                if session_state.save_state(browser.current_state()):
                    LOGGER.info("Fanding session state refreshed")
            except Exception:
                LOGGER.exception("Could not persist refreshed session state")
        code = EXIT_OK
    except (AuthRequired, SessionUnavailable) as exc:
        result, code = failure_result("AUTH_REQUIRED", str(exc)), EXIT_AUTH
    except DomChanged as exc:
        result, code = failure_result("DOM_CHANGED", str(exc)), EXIT_DOM
    except Exception as exc:  # browser crash, network, unexpected
        LOGGER.exception("Fanding check failed")
        result, code = failure_result("BROWSER_ERROR", f"{type(exc).__name__}: {exc}"[:500]), EXIT_BROWSER
    record_status(result, now)
    return code
