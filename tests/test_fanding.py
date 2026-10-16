from datetime import datetime

import pytest

from desk import paths
from desk.errors import DomChanged, LockedPost
from desk.fanding import collector
from desk.fanding.parser import (DEFAULT_SELECTORS, parse_feed_urls, parse_post_html,
                                 parse_relative_datetime)
from desk.store import PostStore, read_json
from tests.fakes import FakeSession, feed_html, post_html

NOW = datetime(2026, 10, 16, 21, 0, tzinfo=paths.KST)
URL = "https://fanding.kr/@T3chfeed/post/{}/"


def test_feed_urls_are_deduplicated_and_absolute():
    html = feed_html(["1", "2", "1"])
    assert parse_feed_urls(html) == [URL.format(1), URL.format(2)]


def test_post_parse_extracts_fields_and_kst_time():
    post = parse_post_html(post_html(when="3시간 전"), URL.format(42), NOW)
    assert post.post_id == "42"
    assert post.author == "T3chfeed_테크피드"
    assert post.published_at.hour == 18 and post.published_at.tzinfo is not None


def test_locked_post_is_skipped_not_bypassed():
    with pytest.raises(LockedPost):
        parse_post_html(post_html(locked=True), URL.format(1), NOW)


def test_missing_body_means_dom_changed():
    with pytest.raises(DomChanged):
        parse_post_html("<html><h1>nothing</h1></html>", URL.format(1), NOW)


@pytest.mark.parametrize("raw,expected", [
    ("10월 5일", (2026, 10, 5)), ("12월 30일", (2025, 12, 30)), ("2일 전", (2026, 10, 14)),
])
def test_relative_dates(raw, expected):
    value = parse_relative_datetime(raw, NOW)
    assert (value.year, value.month, value.day) == expected


def _session(ids, **kw):
    return FakeSession(feed_html(ids), {i: post_html(title=f"t{i}", body=f"본문 {i}") for i in ids}, **kw)


def test_check_creates_then_unchanged_then_updated(root):
    store = PostStore()
    first = collector.run_check(_session(["1", "2"]), store, DEFAULT_SELECTORS, NOW, sleep=lambda s: None)
    assert first["created"] == ["1", "2"]
    second = collector.run_check(_session(["1", "2"]), store, DEFAULT_SELECTORS, NOW, sleep=lambda s: None)
    assert second["unchanged"] == 2 and not second["created"]
    changed = _session(["1"])
    changed.posts["1"] = post_html(title="t1", body="수정된 본문")
    third = collector.run_check(changed, store, DEFAULT_SELECTORS, NOW, sleep=lambda s: None)
    assert third["updated"] == ["1"]
    assert store.get("1").revision == 2


def test_transient_timeout_is_retried(root):
    session = _session(["1"], timeouts={"1": 2})
    result = collector.run_check(session, PostStore(), DEFAULT_SELECTORS, NOW, sleep=lambda s: None)
    assert result["created"] == ["1"] and len(session.calls) == 3


def test_persistent_failure_is_partial_and_tracked(root):
    session = _session(["1", "2"], timeouts={"2": 99})
    result = collector.run_check(session, PostStore(), DEFAULT_SELECTORS, NOW, sleep=lambda s: None)
    assert result["status"] == "PARTIAL"
    assert read_json(paths.STATUS / "post_failures.json")["2"]["attempts"] == 1


def test_auth_failure_is_recorded_with_since(root):
    collector.record_status(collector.failure_result("AUTH_REQUIRED", "x"), NOW)
    later = NOW.replace(hour=23)
    status = collector.record_status(collector.failure_result("AUTH_REQUIRED", "x"), later)
    assert status["auth_required_since"] == NOW.isoformat()
    assert status["consecutive_failures"] == 2
    assert (paths.STATUS / "collector-history.jsonl").read_text(encoding="utf-8").count("\n") == 2


def test_pending_analysis_tracks_content_hash(root):
    store = PostStore()
    collector.run_check(_session(["1"]), store, DEFAULT_SELECTORS, NOW, sleep=lambda s: None)
    assert [p.post_id for p in store.pending_analysis()] == ["1"]
    from desk.store import write_json
    write_json(paths.ANALYSES / "1.json", {"content_hash": store.get("1").content_hash})
    assert store.pending_analysis() == []
