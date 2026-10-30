import json
from datetime import datetime

import pytest

from desk import paths, portfolio, report
from desk.errors import SessionUnavailable
from desk.fanding import state

NOW = datetime(2026, 10, 16, 21, 0, tzinfo=paths.KST)
PRICES = {
    "TSLA": 400.0,
    "PLTR": 200.0,
    "AVGO": 330.0,
    "CCJ": 80.0,
    "INTC": 90.0,
    "VRT": 200.0,
    "NVDA": 200.0,
    "AMZN": 250.0,
}
STATE = {
    "cookies": [{"name": "sid", "value": "abc", "domain": ".fanding.kr"},
                {"name": "x", "value": "y", "domain": ".google.com"}],
    "origins": [{"origin": "https://fanding.kr", "localStorage": []}],
}


def test_encrypt_roundtrip_and_wrong_key():
    key = state.generate_key()
    blob = state.encrypt(STATE, key)
    assert b"abc" not in blob
    assert state.decrypt(blob, key) == STATE
    with pytest.raises(SessionUnavailable):
        state.decrypt(blob, state.generate_key())


def test_save_state_keeps_only_fanding_and_skips_unchanged(root, monkeypatch):
    key = state.generate_key()
    monkeypatch.setenv(state.KEY_ENV, key)
    assert state.save_state(STATE) is True
    assert state.save_state(STATE) is False  # no rewrite -> no needless commit
    loaded = state.load_state()
    assert [c["domain"] for c in loaded["cookies"]] == [".fanding.kr"]
    assert not paths.STATE_PLAIN.exists()  # CI never writes plaintext


def test_load_state_without_key_is_unavailable(root, monkeypatch):
    monkeypatch.setenv(state.KEY_ENV, state.generate_key())
    state.save_state(STATE)
    monkeypatch.delenv(state.KEY_ENV)
    with pytest.raises(SessionUnavailable):
        state.load_state()


def _market(prices):
    return {"fetched_at": NOW.isoformat(), "quotes": {t: {"price": p} for t, p in prices.items()}}


def test_real_config_is_valid(real_config):
    pf, uni, c = portfolio.load_portfolio(), portfolio.load_universe(), portfolio.load_constraints()
    assert portfolio.validate_targets(uni, pf, c) == []


def test_live_portfolio_json_is_wellformed_and_consistent(real_config):
    """Checks config/portfolio.json (the single source of truth) without pinning today's quantities."""
    pf, uni = portfolio.load_portfolio(), portfolio.load_universe()
    tickers = [position.ticker for position in pf.positions]
    universe_tickers = {security.ticker for security in uni.securities}

    assert tickers and len(tickers) == len(set(tickers))
    assert all(position.shares > 0 for position in pf.positions)
    assert all(position.average_cost is None or position.average_cost > 0 for position in pf.positions)
    assert all(position.market_value is None for position in pf.positions)
    assert pf.cash_available_for_investing >= 0 and pf.cash_reserved_for_debt >= 0
    assert pf.confirmed_at <= pf.as_of
    assert set(tickers) <= universe_tickers


def test_fixture_portfolio_is_isolated_from_live_holdings(root):
    pf = portfolio.load_portfolio()
    assert pf.as_of.isoformat() == "2026-01-01"
    assert pf.cash_available_for_investing == pytest.approx(500.0)


def test_plan_classifies_actions(root):
    pf, uni, c = portfolio.load_portfolio(), portfolio.load_universe(), portfolio.load_constraints()
    plan = portfolio.build_plan(pf, uni, c, _market(PRICES))
    rows = {r.ticker: r for r in plan.rows}
    assert "FLNC" not in rows
    assert rows["NVDA"].current > 0
    assert rows["NVDA"].action != portfolio.Action.INITIATE
    assert rows["NVDA"].shares == pytest.approx(rows["NVDA"].amount / 200.0)
    assert rows["CCJ"].action == portfolio.Action.HOLD
    assert rows["CCJ"].amount == 0
    assert abs(sum(r.target for r in plan.rows) - 1) < 1e-6
    assert abs(sum(plan.current.values()) - 1) < 1e-6
    assert plan.recommended_buy_amount <= (
        plan.cash_available_for_buys + plan.planned_sell_proceeds + 1e-9
    )


def test_missing_price_does_not_use_removed_historical_market_values(root):
    pf, uni, c = portfolio.load_portfolio(), portfolio.load_universe(), portfolio.load_constraints()
    plan = portfolio.build_plan(pf, uni, c, _market({}))
    assert set(plan.missing_prices) == {p.ticker for p in pf.positions}
    assert plan.total_value == pytest.approx(
        pf.cash_available_for_investing + pf.cash_reserved_for_debt
    )


def test_target_over_limit_is_reported(root):
    raw = json.loads((paths.CONFIG / "decision_universe.json").read_text(encoding="utf-8"))
    for s in raw["securities"]:
        if s["ticker"] == "AVGO":
            s["target_weight"] += 0.20
        if s["ticker"] == "TSLA":
            s["target_weight"] -= 0.20
    uni = portfolio.Universe.model_validate(raw)
    errors = portfolio.validate_targets(uni, portfolio.load_portfolio(), portfolio.load_constraints())
    assert any("AVGO" in e for e in errors)


def test_report_renders(root):
    pf, uni, c = portfolio.load_portfolio(), portfolio.load_universe(), portfolio.load_constraints()
    text = report.render(portfolio.build_plan(pf, uni, c, _market(PRICES)), pf, uni, NOW)
    assert "현재 → 목표" in text and "NVDA" in text and "실제 주문이 아닌" in text
    assert "FLNC" not in text  # FLNC is not in the universe
    assert "매수재원 검증" in text and f"${pf.cash_available_for_investing:,.2f}" in text
    written = report.write(text, NOW)
    assert (paths.REPORTS / "decision-latest.md").exists() and len(written) == 2


def test_portfolio_score_is_bounded_and_target_scores_higher(root):
    pf, uni, c = portfolio.load_portfolio(), portfolio.load_universe(), portfolio.load_constraints()
    plan = portfolio.build_plan(pf, uni, c, _market({}))
    for s in (plan.score, plan.target_score):
        assert 0 <= s.total <= 100
        assert set(s.components) == set(portfolio.SCORE_WEIGHTS)
    assert plan.target_score.components["alignment"] == 100
    assert plan.target_score.total > plan.score.total


def test_score_penalizes_concentration(root):
    uni, c = portfolio.load_universe(), portfolio.load_constraints()
    calm = portfolio.portfolio_score({"AVGO": 0.25, "NVDA": 0.25, "AMZN": 0.25, "VRT": 0.20, "CASH": 0.05}, uni, c, set())
    hot = portfolio.portfolio_score({"AVGO": 0.70, "NVDA": 0.25, "CASH": 0.05}, uni, c, set())
    assert hot.components["concentration"] < calm.components["concentration"]


def test_portfolio_fingerprint_changes_with_holdings_or_cash(root):
    from desk import portfolio_sync

    raw = portfolio_sync.local_raw()
    base = portfolio_sync.fingerprint(raw)
    assert portfolio_sync.fingerprint(json.loads(json.dumps(raw))) == base

    more = json.loads(json.dumps(raw))
    more["positions"][0]["shares"] += 1
    assert portfolio_sync.fingerprint(more) != base
    cash = json.loads(json.dumps(raw))
    cash["cash_available_for_investing"] += 1
    assert portfolio_sync.fingerprint(cash) != base
    dated = json.loads(json.dumps(raw))
    dated["confirmed_at"] = "2099-01-01"
    assert portfolio_sync.fingerprint(dated) != base


def test_portfolio_check_flags_stale_baseline_and_remote(root, monkeypatch):
    from desk import portfolio_sync

    ok, _ = portfolio_sync.check()
    assert ok
    ok, messages = portfolio_sync.check(expect="deadbeefdeadbeef")
    assert not ok and any("STALE" in m for m in messages)

    changed = portfolio_sync.local_raw()
    changed["cash_available_for_investing"] += 100
    monkeypatch.setattr(portfolio_sync, "remote_raw", lambda fetch=True: changed)
    ok, messages = portfolio_sync.check(remote=True)
    assert not ok and any("GitHub" in m for m in messages)
    monkeypatch.setattr(portfolio_sync, "remote_raw", lambda fetch=True: portfolio_sync.local_raw())
    assert portfolio_sync.check(remote=True)[0]
