"""Observed market-regime snapshot derived from Yahoo daily history."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from desk import paths
from desk.store import write_json
from desk.technicals import fetch_history, period_return, sma


SYMBOLS = {
    "vix": "^VIX",
    "us_10y": "^TNX",
    "dollar": "DX-Y.NYB",
    "qqq": "QQQ",
    "spy": "SPY",
    "hyg": "HYG",
    "lqd": "LQD",
    "rsp": "RSP",
}
HistoryFetcher = Callable[[str], list[dict[str, Any]]]


def _series(bars: list[dict[str, Any]]) -> list[float]:
    return [float(bar["close"]) for bar in bars]


def _asset_snapshot(bars: list[dict[str, Any]]) -> dict[str, Any]:
    closes = _series(bars)
    average_20, average_50 = sma(closes, 20), sma(closes, 50)
    return {
        "as_of": bars[-1]["date"],
        "price": round(closes[-1], 6),
        "sma_20": round(average_20, 6) if average_20 is not None else None,
        "sma_50": round(average_50, 6) if average_50 is not None else None,
        "return_20d": round(period_return(closes, 20), 6)
        if period_return(closes, 20) is not None else None,
    }


def _ratio_snapshot(numerator: list[dict[str, Any]], denominator: list[dict[str, Any]]) -> dict[str, Any]:
    denominator_by_date = {bar["date"]: float(bar["close"]) for bar in denominator}
    ratios = [float(bar["close"]) / denominator_by_date[bar["date"]]
              for bar in numerator if bar["date"] in denominator_by_date
              and denominator_by_date[bar["date"]] != 0]
    if len(ratios) < 21:
        return {"value": None, "sma_20": None, "return_20d": None, "trend": "UNKNOWN"}
    average = sma(ratios, 20)
    change = period_return(ratios, 20)
    trend = "RISING" if ratios[-1] > average and change > 0 else (
        "FALLING" if ratios[-1] < average and change < 0 else "FLAT"
    )
    return {"value": round(ratios[-1], 6), "sma_20": round(average, 6),
            "return_20d": round(change, 6), "trend": trend}


def build_snapshot(histories: dict[str, list[dict[str, Any]]], now: datetime,
                   errors: dict[str, str] | None = None) -> dict[str, Any]:
    components = {name: _asset_snapshot(histories[symbol])
                  for name, symbol in SYMBOLS.items() if symbol in histories}
    if SYMBOLS["hyg"] in histories and SYMBOLS["lqd"] in histories:
        components["credit_hyg_lqd"] = _ratio_snapshot(
            histories[SYMBOLS["hyg"]], histories[SYMBOLS["lqd"]]
        )
    if SYMBOLS["rsp"] in histories and SYMBOLS["spy"] in histories:
        components["breadth_rsp_spy"] = _ratio_snapshot(
            histories[SYMBOLS["rsp"]], histories[SYMBOLS["spy"]]
        )

    votes: list[int] = []
    reasons: list[str] = []
    for name in ("qqq", "spy"):
        item = components.get(name, {})
        if item.get("sma_50") is not None:
            positive = item["price"] > item["sma_50"]
            votes.append(1 if positive else -1)
            item["reason"] = f"{name.upper()} {'above' if positive else 'below'} SMA50"
            reasons.append(item["reason"])
    vix = components.get("vix", {})
    if vix.get("sma_20") is not None and vix.get("return_20d") is not None:
        if vix["price"] > vix["sma_20"] and vix["return_20d"] > 0:
            votes.append(-1)
            vix["reason"] = "VIX rising above SMA20"
            reasons.append(vix["reason"])
        elif vix["price"] < vix["sma_20"] and vix["return_20d"] < 0:
            votes.append(1)
            vix["reason"] = "VIX falling below SMA20"
            reasons.append(vix["reason"])
    for name, label in (("credit_hyg_lqd", "credit HYG/LQD"),
                        ("breadth_rsp_spy", "breadth RSP/SPY")):
        trend = components.get(name, {}).get("trend")
        if trend in ("RISING", "FALLING"):
            votes.append(1 if trend == "RISING" else -1)
            components[name]["reason"] = f"{label} {trend.lower()}"
            reasons.append(components[name]["reason"])
    for name, label in (("us_10y", "US 10Y yield"), ("dollar", "Dollar index")):
        item = components.get(name, {})
        change = item.get("return_20d")
        if change is not None:
            direction = "rising" if change > 0 else "falling" if change < 0 else "flat"
            item["reason"] = f"{label} {direction} over 20 sessions ({change:+.1%})"
    for name, item in components.items():
        item.setdefault("reason", f"{name} mixed or insufficient directional signal")

    score = sum(votes)
    if len(votes) < 3:
        state = "UNKNOWN"
        reasons.append("insufficient regime components")
    elif score >= 2:
        state = "RISK_ON"
    elif score <= -2:
        state = "RISK_OFF"
    else:
        state = "NEUTRAL"
    return {
        "schema_version": "1.0",
        "generated_at": now.isoformat(),
        "as_of": max((item.get("as_of", "") for item in components.values()), default=None),
        "regime": state,
        "score": score,
        "reasons": reasons,
        "components": components,
        "errors": errors or {},
        "usage": "starter size, tactical exposure, buy timing, and portfolio risk; never automatic Core sale",
    }


def update(now: datetime, history_fetcher: HistoryFetcher = fetch_history) -> dict[str, Any]:
    histories, errors = {}, {}
    for symbol in SYMBOLS.values():
        try:
            histories[symbol] = history_fetcher(symbol)
        except Exception as exc:
            errors[symbol] = str(exc)[:200]
    snapshot = build_snapshot(histories, now, errors)
    write_json(paths.MARKET / "regime.json", snapshot)
    return snapshot


def validate_snapshot(snapshot: dict[str, Any]) -> list[str]:
    errors = []
    if snapshot.get("schema_version") != "1.0":
        errors.append("regime.json: unsupported schema_version")
    if snapshot.get("regime") not in {"RISK_ON", "NEUTRAL", "RISK_OFF", "UNKNOWN"}:
        errors.append("regime.json: invalid regime")
    if not isinstance(snapshot.get("reasons"), list):
        errors.append("regime.json: reasons must be a list")
    if not isinstance(snapshot.get("components"), dict):
        errors.append("regime.json: components must be an object")
    return errors
