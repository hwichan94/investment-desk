"""Compact, body-free decision feed for downstream ChatGPT use."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from desk import paths
from desk.analysis import PostAnalysis
from desk.portfolio import Plan, Portfolio, Universe
from desk.store import read_json, write_json


SCHEMA_VERSION = "1.0"
DEFAULT_HORIZON_HOURS = 72


def _aware(value: datetime, reference: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=reference.tzinfo or paths.KST)
    return value


def load_recent_analyses(now: datetime, horizon_hours: int = DEFAULT_HORIZON_HOURS) -> list[PostAnalysis]:
    """Load only structured analyses; paid post bodies are never opened here."""
    cutoff = now - timedelta(hours=horizon_hours)
    recent: list[PostAnalysis] = []
    for path in paths.ANALYSES.glob("*.json"):
        analysis = PostAnalysis.model_validate(read_json(path))
        analyzed_at = _aware(analysis.analyzed_at, now)
        if cutoff <= analyzed_at <= now:
            recent.append(analysis)
    return sorted(recent, key=lambda item: _aware(item.analyzed_at, now), reverse=True)


def _relative(path: Path) -> str:
    try:
        return path.relative_to(paths.ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _analysis_payload(analysis: PostAnalysis) -> dict[str, Any]:
    # Deliberately enumerate fields instead of dumping the source post model. This is the
    # privacy boundary that keeps paid article raw text out of the shareable feed.
    return {
        "post_id": analysis.post_id,
        "analyzed_at": analysis.analyzed_at.isoformat(),
        "title": analysis.title,
        "author": analysis.author,
        "summary": analysis.summary,
        "relevance": analysis.relevance,
        "claims": [claim.model_dump(mode="json") for claim in analysis.claims],
        "thesis_impacts": [impact.model_dump(mode="json") for impact in analysis.thesis_impacts],
        "new_candidates": analysis.new_candidates,
        "portfolio_implication": analysis.portfolio_implication,
    }


def build_feed(plan: Plan, portfolio: Portfolio, universe: Universe, now: datetime,
               horizon_hours: int = DEFAULT_HORIZON_HOURS) -> dict[str, Any]:
    recent = load_recent_analyses(now, horizon_hours)
    by_ticker = {security.ticker: security for security in universe.securities}
    candidates = list(dict.fromkeys(ticker for item in recent for ticker in item.new_candidates))
    holdings = []
    for position in portfolio.positions:
        holdings.append({
            "ticker": position.ticker,
            "shares": position.shares,
            "average_cost": position.average_cost,
            "current_value": round(plan.current.get(position.ticker, 0) * plan.total_value, 6),
            "current_weight": round(plan.current.get(position.ticker, 0), 8),
            "category": position.category,
            "themes": position.themes,
            "core_position": position.core_position,
        })

    actions = []
    for row in plan.rows:
        security = by_ticker.get(row.ticker)
        actions.append({
            "ticker": row.ticker,
            "current_weight": round(row.current, 8),
            "target_weight": round(row.target, 8),
            "change_weight": round(row.change, 8),
            "action": row.action.value,
            "urgency": row.urgency,
            "estimated_amount": round(row.amount, 2),
            "fundamentals": security.thesis_status.value if security else "NOT_APPLICABLE",
            "estimate_revisions": security.estimate_revisions.value if security else "NOT_APPLICABLE",
            "expectations_gap": security.expectations_gap.value if security else "NOT_APPLICABLE",
            "relative_momentum": security.relative_momentum.value if security else "NOT_APPLICABLE",
            "position_and_correlation_risk": (
                {"risk_control": security.risk_control, "portfolio_fit": security.portfolio_fit}
                if security else None
            ),
            "regime_alignment": security.regime_alignment.value if security else "NOT_APPLICABLE",
            "asymmetry": security.asymmetry.value if security else "NOT_APPLICABLE",
            "core_floor_weight": security.core_floor_weight if security else None,
            "tactical_weight": security.tactical_weight if security else None,
            "trim_source": row.trim_source,
            "winner_protection_active": row.winner_protection_active,
            "winner_protection_blocked": row.winner_protection_blocked,
            "asymmetric_starter": row.asymmetric_starter,
            "winner_protection_override_reason": (
                security.winner_protection_override_reason if security else None
            ),
            "invalidation_signals": security.invalidation_signals if security else [],
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now.isoformat(),
        "horizon_hours": horizon_hours,
        "portfolio": {
            "as_of": portfolio.as_of.isoformat(),
            "confirmed_at": portfolio.confirmed_at.isoformat() if portfolio.confirmed_at else None,
            "currency": portfolio.currency,
            "investable_total": round(plan.total_value, 6),
            "cash_available_for_investing": portfolio.cash_available_for_investing,
            "cash_reserved_for_debt": portfolio.cash_reserved_for_debt,
            "holdings": holdings,
        },
        "decision_context": {
            "as_of": universe.as_of.isoformat(),
            "horizon_months": universe.horizon_months,
            "objective": "maximize expected return within acceptable loss and concentration constraints",
            "cash_target": universe.cash_target,
            "portfolio_score": plan.score.model_dump(mode="json"),
            "target_portfolio_score": plan.target_score.model_dump(mode="json"),
            "alerts": plan.alerts,
            "target_errors": plan.target_errors,
            "actions": actions,
        },
        "recent_analyses": [_analysis_payload(item) for item in recent],
        "new_candidates": candidates,
        "report_paths": {
            "analyst_latest": _relative(paths.REPORTS / "analyst-latest.md"),
            "decision_latest": _relative(paths.REPORTS / "decision-latest.md"),
            "decision_journal": _relative(paths.ROOT / "docs" / "trader-decision-journal.md"),
        },
    }


def write(plan: Plan, portfolio: Portfolio, universe: Universe, now: datetime,
          horizon_hours: int = DEFAULT_HORIZON_HOURS) -> str:
    target = paths.REPORTS / "chatgpt-feed.json"
    write_json(target, build_feed(plan, portfolio, universe, now, horizon_hours))
    return str(target)
