import json

from desk import paths, sec_docs
from desk.store import read_json

CIK = "0001234567"


def filing(form, filed, acc, doc="main.htm"):
    return {"form": form, "filed": filed, "report_date": filed, "cik": CIK, "accession": acc,
            "url": f"https://www.sec.gov/Archives/edgar/data/1234567/{acc.replace('-', '')}/{doc}"}


class FakeSec:
    def __init__(self):
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        if url.endswith("index.json"):
            acc = url.rstrip("/").split("/")[-2]
            items = [{"name": "form8k.htm"}]
            if acc.endswith("2"):  # only one of the 8-Ks carries a press release
                items.append({"name": "ex99-1.htm"})
            return json.dumps({"directory": {"item": items}}).encode()
        return (b"<html><ix:header>XBRL junk</ix:header><p>Revenue  was   $1.2B</p>"
                b"<div style='display:none'>hidden</div></html>")


def test_html_to_text_strips_hidden_and_xbrl():
    text = sec_docs.html_to_text(b"<ix:header>x</ix:header><p>A  b</p><div style='display: none'>h</div>")
    assert text == "A b"


def test_sync_downloads_periodic_and_press_releases_then_caches(root):
    filings = {"ABC": [filing("8-K", "2026-10-02", "0000-26-000002"),
                       filing("8-K", "2026-09-01", "0000-26-000001"),
                       filing("10-Q", "2026-08-01", "0000-26-000010")]}
    fake = FakeSec()
    result = sec_docs.sync(filings, fetch=fake)
    assert sorted(result["added"]) == ["ABC 10-Q 2026-08-01", "ABC 8-K 2026-10-02"]
    index = read_json(paths.MARKET / "docs" / "index.json")
    saved = [e for e in index["ABC"] if e["path"]]
    assert len(saved) == 2
    text = (paths.ROOT / saved[0]["path"]).read_text(encoding="utf-8")
    assert "Revenue was $1.2B" in text and "junk" not in text and "hidden" not in text

    calls_before = len(fake.calls)
    assert sec_docs.sync(filings, fetch=fake)["added"] == []
    assert len(fake.calls) == calls_before  # nothing re-downloaded, empty 8-K remembered


def test_sync_drops_docs_that_fall_out_of_window(root):
    fake = FakeSec()
    older = {"ABC": [filing("10-Q", "2026-05-01", "0000-26-000020")]}
    sec_docs.sync(older, fetch=fake)
    old_path = paths.ROOT / read_json(paths.MARKET / "docs" / "index.json")["ABC"][0]["path"]
    newer = {"ABC": [filing("10-Q", "2026-11-01", "0000-26-000030"),
                     filing("10-K", "2026-08-01", "0000-26-000031")]}
    sec_docs.sync(newer, fetch=fake)
    assert not old_path.exists()
