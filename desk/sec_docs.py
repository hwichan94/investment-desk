"""Download official SEC filing text so the cloud analyst can verify claims offline.

GitHub Actions has open internet; the Claude routine sandbox does not reach sec.gov. So the
collector saves plain-text copies of each tracked company's latest periodic report and recent
earnings press releases (8-K/6-K exhibit 99) under data/market/docs/<TICKER>/.
"""
from __future__ import annotations

import gzip
import logging
import re
import time
from collections.abc import Callable
from typing import Any
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from desk import paths
from desk.store import read_json, write_json

LOGGER = logging.getLogger(__name__)
PERIODIC = {"10-Q", "10-K", "20-F", "40-F"}
CURRENT = {"8-K", "6-K"}
KEEP_PERIODIC = 2        # latest periodic reports kept per ticker
KEEP_CURRENT = 4         # latest press-release exhibits kept per ticker
MAX_CHARS = 400_000      # cap per document to keep the repo small
EXHIBIT = re.compile(r"ex-?99", re.IGNORECASE)
INDEX_FILE = "index.json"

Fetcher = Callable[[str], bytes]


def http_get(url: str) -> bytes:
    from desk.market import sec_headers

    time.sleep(0.15)  # SEC fair-access throttle (<10 req/s)
    with urlopen(Request(url, headers=sec_headers()), timeout=30) as response:
        raw = response.read()
        if response.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return raw


def html_to_text(raw: bytes) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup.find_all(["script", "style", "ix:header"]):
        tag.decompose()
    for tag in soup.find_all(style=re.compile(r"display:\s*none", re.IGNORECASE)):
        tag.decompose()
    text = soup.get_text("\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text[:MAX_CHARS]


def _base(filing: dict[str, Any]) -> str:
    return (f"https://www.sec.gov/Archives/edgar/data/{int(filing['cik'])}/"
            f"{filing['accession'].replace('-', '')}/")


def exhibit_urls(filing: dict[str, Any], fetch: Fetcher) -> list[str]:
    import json

    index = json.loads(fetch(_base(filing) + "index.json"))
    names = [item["name"] for item in index.get("directory", {}).get("item", [])]
    return [_base(filing) + n for n in names
            if EXHIBIT.search(n) and n.lower().endswith((".htm", ".html", ".txt"))]


def wanted(filings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    periodic = [f for f in filings if f["form"] in PERIODIC][:KEEP_PERIODIC]
    current = [f for f in filings if f["form"] in CURRENT][:KEEP_CURRENT]
    return periodic + current


def sync(filings_by_ticker: dict[str, list[dict[str, Any]]], fetch: Fetcher = http_get) -> dict[str, Any]:
    """Download missing docs, drop ones no longer wanted. Returns a summary."""
    root = paths.MARKET / "docs"
    index: dict[str, list[dict[str, Any]]] = read_json(root / INDEX_FILE, {}) or {}
    added, errors = [], {}
    for ticker, filings in filings_by_ticker.items():
        keep = [f for f in wanted(filings) if f.get("accession")]
        have = {d["accession"]: d for d in index.get(ticker, [])}
        entries = []
        for filing in keep:
            if filing["accession"] in have:
                entries.append(have[filing["accession"]])
                continue
            try:
                if filing["form"] in CURRENT:
                    urls = exhibit_urls(filing, fetch)
                    if not urls:  # 8-K without a press release; remember so we don't re-check
                        entries.append({"form": filing["form"], "filed": filing["filed"],
                                        "accession": filing["accession"], "path": None})
                        continue
                else:
                    urls = [filing["url"]]
                text = "\n\n".join(f"[source] {u}\n" + html_to_text(fetch(u)) for u in urls)
            except Exception as exc:
                errors[f"{ticker} {filing['form']} {filing['filed']}"] = str(exc)[:200]
                continue
            name = f"{filing['filed']}-{filing['form'].replace('/', '')}-{filing['accession']}.txt"
            path = root / ticker / name
            path.parent.mkdir(parents=True, exist_ok=True)
            header = (f"{ticker} {filing['form']} filed {filing['filed']} "
                      f"(period {filing.get('report_date') or '-'})\n")
            path.write_text(header + text + "\n", encoding="utf-8", newline="\n")
            entry = {"form": filing["form"], "filed": filing["filed"],
                     "report_date": filing.get("report_date"), "accession": filing["accession"],
                     "path": str(path.relative_to(paths.ROOT)).replace("\\", "/"),
                     "sources": urls, "chars": len(text)}
            entries.append(entry)
            added.append(f"{ticker} {filing['form']} {filing['filed']}")
        kept = {e["path"] for e in entries}
        for old in index.get(ticker, []):
            if old["path"] and old["path"] not in kept:
                (paths.ROOT / old["path"]).unlink(missing_ok=True)
        if entries:
            index[ticker] = entries
    write_json(root / INDEX_FILE, index)
    return {"added": added, "errors": errors}
