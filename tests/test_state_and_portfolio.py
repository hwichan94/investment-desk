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


def test_real_config_is_valid():
    pf, uni, c = portfolio.load_portfolio(), portfolio.load_universe(), portfolio.load_constraints()
    assert portfolio.validate_targets(uni, pf, c) == []


def test_confirmed_portfolio_snapshot_is_synced():
    pf, uni = portfolio.load_portfolio(), portfolio.load_universe()
    expected = {"TSLA": 23, "PLTR": 45, "AVGO": 12, "CCJ": 21,
                "INTC": 11, "VRT": 4, "NVDA": 8, "AMZN": 6}

    assert {position.ticker: position.shares for position in pf.positions} == expected
    assert all(position.market_value is None for position in pf.positions)
    costs = {position.ticker: position.average_cost for position in pf.positions}
    assert costs["AVGO"] is None
    assert costs["NVDA"] == pytest.approx(216.79)
    assert costs["AMZN"] == pytest.approx(251.17)
    assert pf.cash_available_for_investing == pytest.approx(201.50)
    assert pf.cash_reserved_for_debt == 0
    assert pf.as_of.isoformat() == "2026-10-29"
    assert pf.confirmed_at.isoformat() == "2026-10-29"
    assert "FLNC" not in {security.ticker for security in uni.securities}
    assert {"NVDA", "AMZN"} <= {security.ticker for security in uni.securities}
    watchlist = json.loads((paths.CONFIG / "watchlist.json").read_text(encoding="utf-8"))
    assert "NVDA" not in watchlist["tickers"]


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
    assert "FLNC" not in text
    assert "매수재원 검증" in text and "$201.50" in text
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
