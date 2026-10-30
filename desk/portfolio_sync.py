"""Guards that keep config/portfolio.json on GitHub the single source of truth for holdings and cash."""
from __future__ import annotations

import hashlib
import json
import subprocess

from desk import paths

REMOTE_REF = "origin/main"
REL_PATH = "config/portfolio.json"


def fingerprint(raw: dict) -> str:
    """Hash of what drives the analysis: shares, average costs, cash and the confirmation dates."""
    positions = sorted(
        (p["ticker"], p["shares"], p.get("average_cost")) for p in raw.get("positions", [])
    )
    payload = {
        "positions": positions,
        "cash_available_for_investing": raw.get("cash_available_for_investing"),
        "cash_reserved_for_debt": raw.get("cash_reserved_for_debt"),
        "as_of": raw.get("as_of"),
        "confirmed_at": raw.get("confirmed_at"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def local_raw() -> dict:
    return json.loads((paths.CONFIG / "portfolio.json").read_text(encoding="utf-8"))


def remote_raw(fetch: bool = True) -> dict:
    """portfolio.json as currently on GitHub main (fetches first)."""
    if fetch:
        subprocess.run(["git", "fetch", "origin", "main"], cwd=paths.ROOT, check=True,
                       capture_output=True, text=True)
    shown = subprocess.run(["git", "show", f"{REMOTE_REF}:{REL_PATH}"], cwd=paths.ROOT,
                           check=True, capture_output=True, text=True)
    return json.loads(shown.stdout)


def check(expect: str | None = None, remote: bool = False, fetch: bool = True) -> tuple[bool, list[str]]:
    """Return (ok, messages). Not ok means holdings/cash changed and the report must be recomputed."""
    local = fingerprint(local_raw())
    messages = [f"portfolio fingerprint: {local}"]
    ok = True
    if expect and expect != local:
        ok = False
        messages.append(f"STALE: 분석 시작 시점 지문 {expect} 와 현재 {local} 가 다릅니다. "
                        "최신 portfolio.json으로 다시 계산하세요.")
    if remote:
        remote_fp = fingerprint(remote_raw(fetch))
        if remote_fp != local:
            ok = False
            messages.append(f"STALE: GitHub {REMOTE_REF} 지문 {remote_fp} != 로컬 {local}. "
                            "git pull --rebase origin main 후 recommend부터 다시 실행하세요.")
        else:
            messages.append(f"GitHub {REMOTE_REF} 와 일치")
    return ok, messages
