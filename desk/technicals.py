"""Daily OHLCV indicators and market-behaviour overlays.

The module only derives values from observed Yahoo bars. Missing history produces
``None``/``UNKNOWN`` rather than an estimate. Technicals adjust timing and sizing;
they never replace the fundamental thesis.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Callable
from urllib.parse import quote

from desk import paths
from desk.store import write_json


HISTORY_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    "?interval=1d&range=2y&events=history&includeAdjustedClose=true"
)
SECTOR_ETF_BY_TICKER = {
    "TSLA": "XLY", "AMZN": "XLY",
    "PLTR": "IGV", "ORCL": "IGV",
    "AVGO": "SOXX", "NVDA": "SOXX", "INTC": "SOXX",
    "CCJ": "URA", "FLNC": "ICLN",
    "VRT": "XLI", "ETN": "XLI", "AXON": "XLI",
    "ANET": "SKYY", "CRWV": "SKYY", "GOOG": "XLC",
}
Momentum = str
HistoryFetcher = Callable[[str], list[dict[str, Any]]]


def parse_yahoo_history(payload: dict[str, Any]) -> list[dict[str, Any]]:
    chart = payload.get("chart", {})
    result = (chart.get("result") or [None])[0]
    if chart.get("error") or not result:
        raise ValueError("history unavailable")
    timestamps = result.get("timestamp") or []
    quote_data = (result.get("indicators", {}).get("quote") or [{}])[0]
    adjusted_data = (result.get("indicators", {}).get("adjclose") or [{}])[0]
    adjusted = adjusted_data.get("adjclose") or []

    def at(values: list[Any] | None, index: int) -> Any:
        return values[index] if values and index < len(values) else None

    bars = []
    for index, stamp in enumerate(timestamps):
        raw_close = at(quote_data.get("close"), index)
        raw_open = at(quote_data.get("open"), index)
        raw_high = at(quote_data.get("high"), index)
        raw_low = at(quote_data.get("low"), index)
        if None in (raw_open, raw_high, raw_low, raw_close):
            continue
        adj_close = at(adjusted, index)
        factor = float(adj_close) / float(raw_close) if adj_close is not None and raw_close else 1.0
        bars.append({
            "date": datetime.fromtimestamp(stamp, tz=timezone.utc).date().isoformat(),
            "open": float(raw_open) * factor,
            "high": float(raw_high) * factor,
            "low": float(raw_low) * factor,
            "close": float(raw_close) * factor,
            "volume": float(at(quote_data.get("volume"), index))
            if at(quote_data.get("volume"), index) is not None else None,
        })
    if not bars:
        raise ValueError("no complete OHLC bars")
    return bars


def fetch_history(ticker: str) -> list[dict[str, Any]]:
    from desk.market import get_json

    payload = get_json(
        HISTORY_URL.format(ticker=quote(ticker, safe="")),
        {"User-Agent": "Mozilla/5.0"},
    )
    return parse_yahoo_history(payload)


def sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def period_return(values: list[float], sessions: int) -> float | None:
    if len(values) < sessions + 1 or values[-sessions - 1] == 0:
        return None
    return values[-1] / values[-sessions - 1] - 1


def rsi_wilder(values: list[float], period: int = 14) -> float | None:
    if len(values) < period + 1:
        return None
    changes = [current - previous for previous, current in zip(values, values[1:])]
    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = ((period - 1) * avg_gain + gain) / period
        avg_loss = ((period - 1) * avg_loss + loss) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    if avg_gain == 0:
        return 0.0
    relative_strength = avg_gain / avg_loss
    return 100 - 100 / (1 + relative_strength)


def atr_wilder(bars: list[dict[str, Any]], period: int = 14) -> float | None:
    if len(bars) < period:
        return None
    true_ranges = []
    previous_close = None
    for bar in bars:
        high, low = float(bar["high"]), float(bar["low"])
        true_range = high - low
        if previous_close is not None:
            true_range = max(true_range, abs(high - previous_close), abs(low - previous_close))
        true_ranges.append(true_range)
        previous_close = float(bar["close"])
    average = sum(true_ranges[:period]) / period
    for value in true_ranges[period:]:
        average = ((period - 1) * average + value) / period
    return average


def relative_volume_20(bars: list[dict[str, Any]]) -> float | None:
    if len(bars) < 21 or bars[-1].get("volume") is None:
        return None
    previous = [bar.get("volume") for bar in bars[-21:-1]]
    if any(value is None for value in previous):
        return None
    average = sum(float(value) for value in previous) / 20
    return float(bars[-1]["volume"]) / average if average else None


def relative_strength_metrics(stock: list[dict[str, Any]], benchmark: list[dict[str, Any]]) -> dict[str, Any]:
    benchmark_close = {bar["date"]: float(bar["close"]) for bar in benchmark}
    ratios = [float(bar["close"]) / benchmark_close[bar["date"]]
              for bar in stock if bar["date"] in benchmark_close and benchmark_close[bar["date"]] != 0]
    if len(ratios) < 61:
        return {"strength": None, "trend": "UNKNOWN"}
    strength = ratios[-1] / ratios[-61] - 1
    short_change = ratios[-1] / ratios[-21] - 1
    average_20 = sum(ratios[-20:]) / 20
    if ratios[-1] > average_20 and short_change > 0:
        trend = "RISING"
    elif ratios[-1] < average_20 and short_change < 0:
        trend = "FALLING"
    else:
        trend = "FLAT"
    return {"strength": strength, "trend": trend}


def classify_relative_momentum(metrics: dict[str, Any]) -> tuple[Momentum, list[str]]:
    required = ("price", "sma_50", "sma_200", "return_60d", "return_120d",
                "relative_volume_20", "latest_day_return", "relative_strength_qqq")
    if any(metrics.get(key) is None for key in required) or metrics.get("relative_strength_qqq_trend") == "UNKNOWN":
        return "UNKNOWN", ["insufficient price, volume, or benchmark history"]

    trend_up = metrics["price"] > metrics["sma_50"] > metrics["sma_200"]
    trend_down = metrics["price"] < metrics["sma_50"] < metrics["sma_200"]
    rs_up = metrics["relative_strength_qqq_trend"] == "RISING"
    rs_down = metrics["relative_strength_qqq_trend"] == "FALLING"
    score = (1 if trend_up else -1 if trend_down else 0)
    score += 1 if rs_up else -1 if rs_down else 0
    if metrics["return_60d"] > 0 and metrics["return_120d"] > 0:
        score += 1
    elif metrics["return_60d"] < 0 and metrics["return_120d"] < 0:
        score -= 1
    if metrics["relative_volume_20"] >= 1:
        score += 1 if metrics["latest_day_return"] > 0 else -1 if metrics["latest_day_return"] < 0 else 0

    reasons = [
        "price above SMA50/SMA200" if trend_up else "price below SMA50/SMA200" if trend_down
        else "mixed price trend",
        f"QQQ relative strength {metrics['relative_strength_qqq_trend'].lower()}",
        f"relative volume {metrics['relative_volume_20']:.2f}x",
    ]
    if trend_up and rs_up and score >= 2:
        return "STRONG", reasons
    if trend_down and rs_down and score <= -2:
        return "WEAK", reasons
    return "NEUTRAL", reasons


def _round(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None


def calculate_technicals(bars: list[dict[str, Any]], qqq_bars: list[dict[str, Any]] | None = None,
                         sector_bars: list[dict[str, Any]] | None = None,
                         sector_etf: str | None = None) -> dict[str, Any]:
    closes = [float(bar["close"]) for bar in bars]
    price = closes[-1]
    sma_20, sma_50, sma_200 = (sma(closes, period) for period in (20, 50, 200))
    rv = relative_volume_20(bars)
    high_52w = max(float(bar["high"]) for bar in bars[-252:]) if len(bars) >= 252 else None
    qqq = relative_strength_metrics(bars, qqq_bars) if qqq_bars else {"strength": None, "trend": "UNKNOWN"}
    sector = (relative_strength_metrics(bars, sector_bars)
              if sector_bars else {"strength": None, "trend": "UNKNOWN"})
    metrics = {
        "as_of": bars[-1]["date"],
        "price": price,
        "rsi_14": rsi_wilder(closes),
        "sma_20": sma_20,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "above_sma_20": price > sma_20 if sma_20 is not None else None,
        "above_sma_50": price > sma_50 if sma_50 is not None else None,
        "above_sma_200": price > sma_200 if sma_200 is not None else None,
        "relative_volume_20": rv,
        "atr_14": atr_wilder(bars),
        "distance_from_52w_high": price / high_52w - 1 if high_52w else None,
        "return_20d": period_return(closes, 20),
        "return_60d": period_return(closes, 60),
        "return_120d": period_return(closes, 120),
        "latest_day_return": period_return(closes, 1),
        "relative_strength_qqq": qqq["strength"],
        "relative_strength_qqq_trend": qqq["trend"],
        "sector_etf": sector_etf,
        "relative_strength_sector": sector["strength"],
        "relative_strength_sector_trend": sector["trend"],
    }
    momentum, reasons = classify_relative_momentum(metrics)
    metrics["relative_momentum"] = momentum
    metrics["relative_momentum_reasons"] = reasons
    metrics["heavy_volume_decline"] = bool(
        rv is not None and rv >= 1.2 and metrics["latest_day_return"] is not None
        and metrics["latest_day_return"] < 0
    )
    return {key: _round(value) if isinstance(value, float) else value for key, value in metrics.items()}


def calculate_event_reaction(bars: list[dict[str, Any]], event_date: str | date,
                             qqq_bars: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    target = event_date.isoformat() if isinstance(event_date, date) else event_date
    event_index = next((index for index, bar in enumerate(bars) if bar["date"] >= target), None)
    if event_index is None:
        return {"event_date": target, "market_date": None, "status": "UNKNOWN"}
    qqq_by_date = {bar["date"]: bar for bar in (qqq_bars or [])}

    def one_day_return(series: list[dict[str, Any]], index: int) -> float | None:
        if index <= 0 or float(series[index - 1]["close"]) == 0:
            return None
        return float(series[index]["close"]) / float(series[index - 1]["close"]) - 1

    event_return = one_day_return(bars, event_index)
    next_return = one_day_return(bars, event_index + 1) if event_index + 1 < len(bars) else None
    event_bar = bars[event_index]
    next_bar = bars[event_index + 1] if event_index + 1 < len(bars) else None

    def benchmark_return(day: dict[str, Any] | None) -> float | None:
        if not day or day["date"] not in qqq_by_date:
            return None
        dates = sorted(qqq_by_date)
        position = dates.index(day["date"])
        if position == 0:
            return None
        previous, current = qqq_by_date[dates[position - 1]], qqq_by_date[dates[position]]
        return float(current["close"]) / float(previous["close"]) - 1

    qqq_event = benchmark_return(event_bar)
    qqq_next = benchmark_return(next_bar)
    prior_volumes = [bar.get("volume") for bar in bars[max(0, event_index - 20):event_index]]
    volume_multiple = None
    if len(prior_volumes) == 20 and all(value is not None for value in prior_volumes) and event_bar.get("volume") is not None:
        average = sum(float(value) for value in prior_volumes) / 20
        volume_multiple = float(event_bar["volume"]) / average if average else None
    result = {
        "event_date": target,
        "market_date": event_bar["date"],
        "status": "OK" if event_return is not None else "UNKNOWN",
        "reaction_classification": "UNCLASSIFIED",
        "classification_options": [
            "GOOD_NEWS_STRONG", "GOOD_NEWS_WEAK", "BAD_NEWS_RESILIENT", "BAD_NEWS_WEAK",
        ],
        "event_day_return": event_return,
        "next_day_return": next_return,
        "excess_return_qqq_event": (
            (1 + event_return) / (1 + qqq_event) - 1
            if event_return is not None and qqq_event is not None and qqq_event != -1 else None
        ),
        "excess_return_qqq_next": (
            (1 + next_return) / (1 + qqq_next) - 1
            if next_return is not None and qqq_next is not None and qqq_next != -1 else None
        ),
        "volume_multiple_20": volume_multiple,
    }
    return {key: _round(value) if isinstance(value, float) else value for key, value in result.items()}


def update(now: datetime, tickers: list[str], history_fetcher: HistoryFetcher = fetch_history) -> dict[str, Any]:
    cache: dict[str, list[dict[str, Any]]] = {}
    errors: dict[str, str] = {}

    def load(symbol: str) -> list[dict[str, Any]] | None:
        if symbol in cache:
            return cache[symbol]
        try:
            cache[symbol] = history_fetcher(symbol)
            return cache[symbol]
        except Exception as exc:
            errors[symbol] = str(exc)[:200]
            return None

    qqq_bars = load("QQQ")
    securities = {}
    for ticker in tickers:
        bars = load(ticker)
        if not bars:
            continue
        sector_etf = SECTOR_ETF_BY_TICKER.get(ticker)
        sector_bars = load(sector_etf) if sector_etf else None
        securities[ticker] = calculate_technicals(bars, qqq_bars, sector_bars, sector_etf)
    snapshot = {
        "schema_version": "1.0",
        "generated_at": now.isoformat(),
        "benchmark": "QQQ",
        "securities": securities,
        "errors": errors,
    }
    write_json(paths.MARKET / "technicals.json", snapshot)
    return snapshot


def validate_snapshot(snapshot: dict[str, Any]) -> list[str]:
    errors = []
    if snapshot.get("schema_version") != "1.0":
        errors.append("technicals.json: unsupported schema_version")
    required = {
        "as_of", "price", "rsi_14", "sma_20", "sma_50", "sma_200",
        "above_sma_20", "above_sma_50", "above_sma_200", "relative_volume_20",
        "atr_14", "distance_from_52w_high", "return_20d", "return_60d",
        "return_120d", "relative_strength_qqq", "relative_momentum",
    }
    for ticker, item in (snapshot.get("securities") or {}).items():
        missing = required - set(item)
        if missing:
            errors.append(f"technicals.json {ticker}: missing {sorted(missing)}")
        if item.get("relative_momentum") not in {"STRONG", "NEUTRAL", "WEAK", "UNKNOWN"}:
            errors.append(f"technicals.json {ticker}: invalid relative_momentum")
    return errors
