import json
from datetime import datetime

import pytest

from desk import paths, portfolio, report
from desk.errors import SessionUnavailable
from desk.fanding import state

NOW = datetime(2026, 10, 16, 21, 0, tzinfo=paths.KST)
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


def test_plan_classifies_actions(root):
    pf, uni, c = portfolio.load_portfolio(), portfolio.load_universe(), portfolio.load_constraints()
    prices = {p.ticker: p.market_value / p.shares for p in pf.positions}
    prices |= {"NVDA": 200.0, "AMZN": 250.0}
    plan = portfolio.build_plan(pf, uni, c, _market(prices))
    rows = {r.ticker: r for r in plan.rows}
    assert rows["FLNC"].action == portfolio.Action.EXIT
    assert rows["NVDA"].action == portfolio.Action.INITIATE
    assert rows["NVDA"].shares == pytest.approx(rows["NVDA"].amount / 200.0)
    assert abs(sum(r.target for r in plan.rows) - 1) < 1e-6
    assert abs(sum(plan.current.values()) - 1) < 1e-6
    assert any("현금" in a for a in plan.alerts)


def test_missing_price_falls_back_to_stored_value(root):
    pf, uni, c = portfolio.load_portfolio(), portfolio.load_universe(), portfolio.load_constraints()
    plan = portfolio.build_plan(pf, uni, c, _market({}))
    assert set(plan.missing_prices) == {p.ticker for p in pf.positions}
    assert plan.total_value == pytest.approx(pf.cash + sum(p.market_value for p in pf.positions))


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
    text = report.render(portfolio.build_plan(pf, uni, c, _market({})), pf, uni, NOW)
    assert "현재 → 목표" in text and "FLNC" in text and "실제 주문이 아닌" in text
    written = report.write(text, NOW)
    assert (paths.REPORTS / "decision-latest.md").exists() and len(written) == 2
