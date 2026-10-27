import json
from datetime import date, datetime, timedelta

import pytest

from desk import chatgpt_feed, paths, portfolio, regime, technicals


NOW = datetime(2026, 10, 27, 15, 0, tzinfo=paths.KST)


def make_bars(closes, volumes=None, start=date(2025, 1, 1)):
    volumes = volumes or [1_000] * len(closes)
    return [{
        "date": (start + timedelta(days=index)).isoformat(),
        "open": float(close) - 0.5,
        "high": float(close) + 1,
        "low": float(close) - 1,
        "close": float(close),
        "volume": float(volumes[index]),
    } for index, close in enumerate(closes)]


def rising_bars(start=100, step=1.0, count=300):
    return make_bars([start + step * index for index in range(count)])


def test_rsi_sma_and_atr_are_wilder_accurate():
    wilder_example = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10,
                      45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28]
    values = list(range(1, 201))
    bars = make_bars(values)

    assert technicals.rsi_wilder(wilder_example) == pytest.approx(70.464135, rel=1e-6)
    assert technicals.sma(values, 20) == pytest.approx(190.5)
    assert technicals.sma(values, 50) == pytest.approx(175.5)
    assert technicals.sma(values, 200) == pytest.approx(100.5)
    assert technicals.atr_wilder(bars) == pytest.approx(2.0)


def test_insufficient_history_keeps_values_and_momentum_unknown():
    result = technicals.calculate_technicals(rising_bars(count=10), rising_bars(count=10))

    assert result["sma_20"] is None
    assert result["sma_200"] is None
    assert result["rsi_14"] is None
    assert result["distance_from_52w_high"] is None
    assert result["relative_momentum"] == "UNKNOWN"


def test_rsi_overbought_alone_never_makes_momentum_weak():
    stock = rising_bars(start=40, step=1.2)
    qqq = rising_bars(start=100, step=0.25)

    result = technicals.calculate_technicals(stock, qqq)

    assert result["rsi_14"] >= 80
    assert result["relative_momentum"] == "STRONG"


def _market():
    return {"fetched_at": NOW.isoformat(), "quotes": {}}


def _technical_snapshot(momentum="STRONG"):
    return {
        "schema_version": "1.0",
        "generated_at": NOW.isoformat(),
        "benchmark": "QQQ",
        "errors": {},
        "securities": {
            "PLTR": {
                "as_of": "2026-10-27", "price": 200.0, "rsi_14": 82.0,
                "sma_20": 190.0, "sma_50": 175.0, "sma_200": 130.0,
                "above_sma_20": True, "above_sma_50": True, "above_sma_200": True,
                "relative_volume_20": 1.1, "atr_14": 7.0,
                "distance_from_52w_high": -0.01, "return_20d": 0.12,
                "return_60d": 0.30, "return_120d": 0.60,
                "relative_strength_qqq": 0.22,
                "relative_strength_qqq_trend": "RISING",
                "relative_momentum": momentum, "heavy_volume_decline": False,
            }
        },
    }


def _pltr_reduction_universe():
    raw = json.loads((paths.CONFIG / "decision_universe.json").read_text(encoding="utf-8"))
    raw["cash_target"] += 0.03
    pltr = next(item for item in raw["securities"] if item["ticker"] == "PLTR")
    pltr["target_weight"] = 0.30
    pltr["tactical_weight"] = 0.0
    pltr["estimate_revisions"] = "UNKNOWN"
    pltr["relative_momentum"] = "UNKNOWN"
    return portfolio.Universe.model_validate(raw)


def test_strong_observed_momentum_activates_pltr_winner_protection(root):
    plan = portfolio.build_plan(
        portfolio.load_portfolio(), _pltr_reduction_universe(), portfolio.load_constraints(),
        _market(), _technical_snapshot(), {"regime": "RISK_ON", "reasons": []},
    )
    row = next(item for item in plan.rows if item.ticker == "PLTR")

    assert row.winner_protection_active is True
    assert row.winner_protection_source == "TECHNICAL_CONFIRMATION"
    assert row.winner_protection_blocked is True
    assert row.action == portfolio.Action.HOLD
    assert "RSI 과열만으로 축소 금지" in row.technical_signal


def test_risk_off_does_not_auto_sell_core_positions(root):
    pf, universe, constraints = (portfolio.load_portfolio(), portfolio.load_universe(),
                                 portfolio.load_constraints())
    neutral = portfolio.build_plan(pf, universe, constraints, _market())
    risk_off = portfolio.build_plan(
        pf, universe, constraints, _market(), {},
        {"regime": "RISK_OFF", "as_of": "2026-10-27", "reasons": ["VIX rising"]},
    )
    core = {position.ticker for position in pf.positions if position.core_position}
    neutral_rows = {row.ticker: row for row in neutral.rows}
    risk_rows = {row.ticker: row for row in risk_off.rows}

    assert all(risk_rows[ticker].action == neutral_rows[ticker].action for ticker in core)
    assert all(risk_rows[ticker].action != portfolio.Action.EXIT for ticker in core)


def test_technical_and_regime_snapshots_are_written(root):
    histories = {
        "PLTR": rising_bars(start=40, step=1.2),
        "QQQ": rising_bars(start=100, step=0.4),
        "IGV": rising_bars(start=80, step=0.5),
        "SPY": rising_bars(start=100, step=0.35),
        "^VIX": rising_bars(start=40, step=-0.08),
        "^TNX": rising_bars(start=40, step=0.0),
        "DX-Y.NYB": rising_bars(start=100, step=0.0),
        "HYG": rising_bars(start=70, step=0.12),
        "LQD": rising_bars(start=100, step=0.03),
        "RSP": rising_bars(start=100, step=0.50),
    }

    def fetch(symbol):
        return histories[symbol]

    technical_snapshot = technicals.update(NOW, ["PLTR"], history_fetcher=fetch)
    regime_snapshot = regime.update(NOW, history_fetcher=fetch)

    assert (paths.MARKET / "technicals.json").exists()
    assert (paths.MARKET / "regime.json").exists()
    assert technical_snapshot["securities"]["PLTR"]["relative_momentum"] == "STRONG"
    assert regime_snapshot["regime"] == "RISK_ON"
    assert all(regime_snapshot["components"][name].get("reason")
               for name in ("vix", "us_10y", "dollar", "qqq", "spy",
                            "credit_hyg_lqd", "breadth_rsp_spy"))
    assert technicals.validate_snapshot(technical_snapshot) == []
    assert regime.validate_snapshot(regime_snapshot) == []


def test_event_reaction_has_returns_excess_return_and_volume_multiple():
    closes = [100 + index for index in range(35)]
    volumes = [1_000] * 35
    closes[25] += 10
    volumes[25] = 2_000
    stock = make_bars(closes, volumes)
    qqq = rising_bars(start=200, step=0.2, count=35)

    result = technicals.calculate_event_reaction(stock, stock[25]["date"], qqq)

    assert result["status"] == "OK"
    assert result["event_day_return"] > 0
    assert result["excess_return_qqq_event"] > 0
    assert result["volume_multiple_20"] == pytest.approx(2.0)
    assert result["next_day_return"] is not None


def test_chatgpt_feed_contains_only_key_technical_and_regime_context(root):
    pf, universe, constraints = (portfolio.load_portfolio(), portfolio.load_universe(),
                                 portfolio.load_constraints())
    regime_data = {"regime": "RISK_OFF", "as_of": "2026-10-27",
                   "reasons": ["VIX rising", "credit HYG/LQD falling"]}
    plan = portfolio.build_plan(pf, universe, constraints, _market(), _technical_snapshot(), regime_data)

    feed = chatgpt_feed.build_feed(plan, pf, universe, NOW)
    pltr = next(item for item in feed["decision_context"]["actions"] if item["ticker"] == "PLTR")

    assert feed["technical_context"]["regime"]["state"] == "RISK_OFF"
    assert feed["technical_context"]["regime"]["core_auto_sell"] is False
    assert pltr["relative_momentum"] == "STRONG"
    assert pltr["key_technicals"]["above_sma_200"] is True
    assert "rsi_14" not in pltr["key_technicals"]  # feed carries decision signals, not an indicator dump
