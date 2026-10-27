import json
from datetime import datetime, timedelta

import pytest

from desk import chatgpt_feed, cli, paths, portfolio
from desk.store import write_json


NOW = datetime(2026, 10, 27, 12, 0, tzinfo=paths.KST)


def _market(prices=None):
    return {
        "fetched_at": NOW.isoformat(),
        "quotes": {ticker: {"price": price} for ticker, price in (prices or {}).items()},
    }


def _winner_prices():
    return {"TSLA": 100.0, "PLTR": 300.0, "AVGO": 100.0, "CCJ": 100.0,
            "INTC": 100.0, "VRT": 100.0, "NVDA": 100.0}


def _contains_key(value, key):
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


def test_reserved_cash_is_in_total_weights_but_excluded_from_funding(root):
    raw = json.loads((paths.CONFIG / "portfolio.json").read_text(encoding="utf-8"))
    raw["cash_reserved_for_debt"] = 1_000_000
    pf = portfolio.Portfolio.model_validate(raw)
    quotes = {position.ticker: 100.0 for position in pf.positions}

    total, weights, missing, _ = portfolio.current_weights(pf, _market(quotes)["quotes"])

    equity = sum(position.shares * quotes[position.ticker] for position in pf.positions)
    expected = pf.cash_available_for_investing + pf.cash_reserved_for_debt + equity
    assert total == pytest.approx(expected)
    assert weights["CASH"] == pytest.approx(pf.cash_available_for_investing / expected)
    assert weights["RESERVED_CASH"] == pytest.approx(pf.cash_reserved_for_debt / expected)
    assert sum(weights.values()) == pytest.approx(1)
    assert missing == []

    plan = portfolio.build_plan(pf, portfolio.load_universe(),
                                portfolio.load_constraints(), _market(quotes))
    assert plan.deployable_value == pytest.approx(equity + pf.cash_available_for_investing)
    assert plan.cash_available_for_buys < pf.cash_available_for_investing
    assert plan.recommended_buy_amount <= (
        plan.cash_available_for_buys + plan.planned_sell_proceeds + 1e-9
    )
    assert sum(plan.cash_first_allocations.values()) <= plan.cash_available_for_buys + 1e-9


def test_legacy_cash_config_is_migrated_in_memory(root):
    raw = json.loads((paths.CONFIG / "portfolio.json").read_text(encoding="utf-8"))
    expected = raw.pop("cash_available_for_investing")
    raw.pop("cash_reserved_for_debt")
    raw["cash"] = expected

    pf = portfolio.Portfolio.model_validate(raw)

    assert pf.cash_available_for_investing == expected
    assert pf.cash_reserved_for_debt == 0
    assert pf.cash == expected
    assert "cash" not in pf.model_dump()


def _winner_universe(override_reason=None):
    raw = json.loads((paths.CONFIG / "decision_universe.json").read_text(encoding="utf-8"))
    raw["cash_target"] += 0.03
    pltr = next(item for item in raw["securities"] if item["ticker"] == "PLTR")
    pltr.update({
        "target_weight": 0.30,
        "tactical_weight": 0.0,
        "estimate_revisions": "IMPROVING",
        "relative_momentum": "STRONG",
    })
    if override_reason is not None:
        pltr["winner_protection_override_reason"] = override_reason
    return portfolio.Universe.model_validate(raw)


def test_winner_protection_blocks_reduce_without_override(root):
    pf, c = portfolio.load_portfolio(), portfolio.load_constraints()
    plan = portfolio.build_plan(pf, _winner_universe(), c, _market(_winner_prices()))
    row = next(item for item in plan.rows if item.ticker == "PLTR")

    assert row.winner_protection_active is True
    assert row.winner_protection_blocked is True
    assert row.action == portfolio.Action.HOLD
    assert row.amount == 0
    assert any("축소를 차단" in alert for alert in plan.alerts)
    assert not plan.target_errors  # protected HOLD is a valid plan, not a broken target file


def test_winner_protection_override_allows_reduce_and_is_validated(root):
    pf, c = portfolio.load_portfolio(), portfolio.load_constraints()
    plan = portfolio.build_plan(
        pf,
        _winner_universe("공식 가이던스 하향으로 핵심 성장 thesis가 훼손됨"),
        c,
        _market(_winner_prices()),
    )
    row = next(item for item in plan.rows if item.ticker == "PLTR")

    assert row.winner_protection_active is True
    assert row.winner_protection_blocked is False
    assert row.action == portfolio.Action.REDUCE
    assert not any("Winner Protection" in error for error in plan.target_errors)

    with pytest.raises(ValueError, match="cannot be blank"):
        _winner_universe("          ")
    with pytest.raises(ValueError, match="cannot override Winner Protection"):
        _winner_universe("신고가이고 밸류에이션이 너무 높음")


def test_asymmetric_starter_requires_favorable_asymmetry_and_two_to_three_percent(root):
    raw = json.loads((paths.CONFIG / "decision_universe.json").read_text(encoding="utf-8"))
    candidate = next(item for item in raw["securities"] if item["ticker"] == "ORCL")
    candidate["target_weight"] = 0.025
    candidate["asymmetry"] = "FAVORABLE"

    security = portfolio.Security.model_validate(candidate)

    assert security.asymmetric_starter is True
    assert security.model_copy(update={"target_weight": 0.04}).asymmetric_starter is False


def _analysis(post_id, analyzed_at, title):
    return {
        "post_id": post_id,
        "content_hash": f"hash-{post_id}",
        "analyzed_at": analyzed_at.isoformat(),
        "title": title,
        "author": "analyst",
        "summary": f"{title} 구조화 요약",
        "relevance": "HIGH",
        "claims": [{
            "kind": "FACT",
            "text": f"{title} 확인 대상 주장",
            "tickers": ["PLTR"],
            "verification": "UNVERIFIED",
        }],
        "thesis_impacts": [{
            "ticker": "PLTR",
            "direction": "NEUTRAL",
            "magnitude": "LOW",
            "rationale": "공식 근거 확인 전",
        }],
        "new_candidates": ["NEW"],
        "portfolio_implication": "공식 확인 전 목표 비중 변경 없음",
    }


def test_chatgpt_feed_uses_recent_analyses_and_never_raw_body(root):
    secret_body = "PAID-ARTICLE-RAW-BODY-MUST-NEVER-LEAK"
    write_json(paths.POSTS / "recent.json", {"body": secret_body})
    write_json(paths.ANALYSES / "recent.json", _analysis("recent", NOW - timedelta(hours=2), "최근"))
    write_json(paths.ANALYSES / "old.json", _analysis("old", NOW - timedelta(hours=73), "과거"))
    pf, uni, c = portfolio.load_portfolio(), portfolio.load_universe(), portfolio.load_constraints()
    plan = portfolio.build_plan(pf, uni, c, _market())

    feed = chatgpt_feed.build_feed(plan, pf, uni, NOW)
    encoded = json.dumps(feed, ensure_ascii=False)

    assert [item["post_id"] for item in feed["recent_analyses"]] == ["recent"]
    assert feed["horizon_hours"] == 72
    assert feed["portfolio"]["cash_reserved_for_debt"] == 0
    assert feed["portfolio"]["total_portfolio_value"] == pytest.approx(plan.total_value)
    assert feed["portfolio"]["investable_total"] == pytest.approx(plan.deployable_value)
    assert feed["decision_context"]["funding"]["cash_is_not_an_automatic_buy_signal"] is True
    assert secret_body not in encoded
    assert not _contains_key(feed, "body")
    assert feed["report_paths"]["decision_latest"] == "reports/decision-latest.md"


def test_recommend_also_writes_chatgpt_feed(root):
    write_json(paths.MARKET / "quotes.json", _market())

    assert cli.main(["recommend"]) == 0
    feed_path = paths.REPORTS / "chatgpt-feed.json"
    assert feed_path.exists()
    assert json.loads(feed_path.read_text(encoding="utf-8"))["schema_version"] == "1.0"
