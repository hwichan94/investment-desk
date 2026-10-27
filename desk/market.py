"""Public market data: Yahoo chart quotes and SEC EDGAR filing lists.

Failures are isolated per ticker; missing values stay missing (never estimated).
"""
from __future__ import annotations

import gzip
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, urlopen

from desk import paths
from desk.store import read_json, write_json

LOGGER = logging.getLogger(__name__)
YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
TRACKED_FORMS = {"10-Q", "10-K", "8-K", "20-F", "40-F", "6-K"}


def get_json(url: str, headers: dict[str, str], retries: int = 2, timeout: int = 20) -> Any:
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urlopen(Request(url, headers=headers), timeout=timeout) as response:
                raw = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            last = exc
            time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"{url}: {type(last).__name__}: {last}")


def parse_yahoo(payload: dict[str, Any]) -> dict[str, Any]:
    chart = payload.get("chart", {})
    result = (chart.get("result") or [None])[0]
    if chart.get("error") or not result:
        raise ValueError("quote unavailable")
    meta = result.get("meta", {})
    price = meta.get("regularMarketPrice")
    if price is None:
        closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
        price = next((c for c in reversed(closes) if c is not None), None)
    if price is None or meta.get("regularMarketTime") is None:
        raise ValueError("incomplete quote")
    return {
        "price": float(price),
        "currency": meta.get("currency"),
        "previous_close": meta.get("chartPreviousClose") or meta.get("previousClose"),
        "market_time": datetime.fromtimestamp(meta["regularMarketTime"], tz=timezone.utc).isoformat(),
    }


def fetch_quotes(tickers: list[str]) -> tuple[dict[str, Any], dict[str, str]]:
    quotes, errors = {}, {}
    for ticker in tickers:
        try:
            payload = get_json(YAHOO_URL.format(ticker=ticker), {"User-Agent": "Mozilla/5.0"})
            quotes[ticker] = parse_yahoo(payload)
        except Exception as exc:
            errors[ticker] = str(exc)[:200]
    return quotes, errors


def sec_headers() -> dict[str, str]:
    agent = os.environ.get("SEC_USER_AGENT", "PersonalInvestmentDesk/1.0 personal-research")
    return {"User-Agent": agent, "Accept-Encoding": "gzip, deflate"}


def fetch_filings(tickers: list[str], per_ticker: int = 15) -> tuple[dict[str, Any], dict[str, str]]:
    filings, errors = {}, {}
    try:
        table = get_json(SEC_TICKERS_URL, sec_headers())
    except Exception as exc:
        return {}, {"*": str(exc)[:200]}
    ciks = {str(v["ticker"]).upper(): str(v["cik_str"]).zfill(10) for v in table.values()}
    for ticker in tickers:
        cik = ciks.get(ticker)
        if not cik:
            errors[ticker] = "no SEC CIK (foreign filer or not listed)"
            continue
        try:
            time.sleep(0.15)  # SEC fair-access throttle
            recent = get_json(SEC_SUBMISSIONS_URL.format(cik=cik), sec_headers())["filings"]["recent"]
            rows = []
            for acc, filed, report, form, doc in zip(recent["accessionNumber"], recent["filingDate"],
                                                     recent["reportDate"], recent["form"],
                                                     recent["primaryDocument"]):
                if form not in TRACKED_FORMS:
                    continue
                rows.append({
                    "form": form, "filed": filed, "report_date": report or None,
                    "cik": cik, "accession": acc,
                    "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{doc}",
                })
                if len(rows) >= per_ticker:
                    break
            filings[ticker] = rows
        except Exception as exc:
            errors[ticker] = str(exc)[:200]
    return filings, errors


def tracked_tickers() -> list[str]:
    portfolio = read_json(paths.CONFIG / "portfolio.json", {})
    universe = read_json(paths.CONFIG / "decision_universe.json", {})
    watch = read_json(paths.CONFIG / "watchlist.json", {})
    tickers = [p["ticker"] for p in portfolio.get("positions", [])]
    tickers += [s["ticker"] for s in universe.get("securities", [])]
    tickers += watch.get("tickers", [])
    return sorted(set(tickers))


def update(now: datetime, with_filings: bool = True) -> dict[str, Any]:
    tickers = tracked_tickers()
    quotes, quote_errors = fetch_quotes(tickers)
    previous = read_json(paths.MARKET / "quotes.json", {}) or {}
    # Keep the last good quote (marked stale) rather than dropping the ticker.
    for ticker in quote_errors:
        if ticker in previous.get("quotes", {}):
            quotes[ticker] = {**previous["quotes"][ticker], "stale": True}
    write_json(paths.MARKET / "quotes.json",
               {"fetched_at": now.isoformat(), "quotes": quotes, "errors": quote_errors})
    summary = {"quotes": len(quotes), "quote_errors": quote_errors}
    from desk import regime, technicals

    history_cache: dict[str, list[dict[str, Any]]] = {}

    def cached_history(symbol: str) -> list[dict[str, Any]]:
        if symbol not in history_cache:
            history_cache[symbol] = technicals.fetch_history(symbol)
        return history_cache[symbol]

    technical_snapshot = technicals.update(now, tickers, history_fetcher=cached_history)
    regime_snapshot = regime.update(now, history_fetcher=cached_history)
    summary.update({
        "technicals": len(technical_snapshot["securities"]),
        "technical_errors": technical_snapshot["errors"],
        "regime": regime_snapshot["regime"],
        "regime_errors": regime_snapshot["errors"],
    })
    if with_filings:
        filings, filing_errors = fetch_filings(tickers)
        old = (read_json(paths.MARKET / "filings.json", {}) or {}).get("filings", {})
        def is_new(ticker: str, filing: dict[str, Any]) -> bool:
            seen = old.get(ticker, [])
            latest = max((o["filed"] for o in seen), default="")
            return filing["url"] not in {o["url"] for o in seen} and filing["filed"] >= latest

        new_since_last = {t: [f for f in rows if is_new(t, f)]
                          for t, rows in filings.items()} if old else {}
        new_since_last = {t: rows for t, rows in new_since_last.items() if rows}
        if filings:
            write_json(paths.MARKET / "filings.json",
                       {"fetched_at": now.isoformat(), "filings": filings, "errors": filing_errors})
        if new_since_last:
            log = read_json(paths.MARKET / "new_filings.json", []) or []
            log.append({"detected_at": now.isoformat(), "filings": new_since_last})
            write_json(paths.MARKET / "new_filings.json", log[-100:])
        summary.update({"filings": len(filings), "filing_errors": filing_errors,
                        "new_filings": new_since_last})
        if filings:
            from desk import sec_docs

            summary["docs"] = sec_docs.sync(filings)
    return summary
