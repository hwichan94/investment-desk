"""Current weights, target validation and current->target action plan.

Inputs are explicit files: config/portfolio.json (actual holdings, user-confirmed only),
config/decision_universe.json (scores/targets, reviewed by the analyst routine) and the
latest quotes. Output is a recommendation; nothing here can place an order.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from desk import paths
from desk.store import read_json


class ThesisStatus(str, Enum):
    STRENGTHENING = "STRENGTHENING"
    STABLE = "STABLE"
    EMERGING = "EMERGING"
    WEAKENING = "WEAKENING"
    BROKEN = "BROKEN"


class Position(BaseModel):
    ticker: str
    shares: float = Field(ge=0)
    average_cost: float | None = None
    market_value: float | None = None
    category: str = ""
    themes: list[str] = Field(default_factory=list)
    core_position: bool = False
    thesis: str = ""


class Portfolio(BaseModel):
    as_of: date
    confirmed_at: date | None = None
    currency: str = "USD"
    cash: float = Field(ge=0)
    positions: list[Position]


class Constraints(BaseModel):
    min_cash_weight: float
    max_cash_weight: float
    max_single_position_weight: float
    max_core_position_weight: float
    no_action_below: float = 0.01
    watch_below: float = 0.03
    consider_below: float = 0.05
    target_weight_tolerance: float = 0.0001
    transaction_cost_bps: float = 0
    tax_rate: float = 0


class ScoreWeights(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fundamental_quality: float
    fundamental_momentum: float
    catalyst_visibility: float
    valuation: float
    risk_control: float
    portfolio_fit: float

    @model_validator(mode="after")
    def _sum_one(self) -> "ScoreWeights":
        if abs(sum(self.model_dump().values()) - 1) > 1e-4:
            raise ValueError("score weights must total 1.0")
        return self


class Security(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticker: str
    company_name: str
    thesis_status: ThesisStatus
    fundamental_quality: float = Field(ge=0, le=100)
    fundamental_momentum: float = Field(ge=0, le=100)
    catalyst_visibility: float = Field(ge=0, le=100)
    valuation: float = Field(ge=0, le=100)
    risk_control: float = Field(ge=0, le=100)
    portfolio_fit: float = Field(ge=0, le=100)
    evidence_confidence: float = Field(ge=0, le=1)
    target_weight: float = Field(ge=0, le=1)
    why_now: str
    main_risk: str
    invalidation_signals: list[str] = Field(min_length=1)
    kpis_12m: list[str] = Field(default_factory=list)
    funding_from: list[str] = Field(default_factory=list)
    execution_plan: str
    watch_reason: str | None = None
    source_urls: list[str] = Field(default_factory=list)

    def score(self, w: ScoreWeights) -> float:
        return round(sum(getattr(self, k) * v for k, v in w.model_dump().items()), 1)


class Universe(BaseModel):
    model_config = ConfigDict(extra="forbid")
    as_of: date
    horizon_months: int = Field(ge=3, le=60)
    cash_target: float = Field(ge=0, le=1)
    score_weights: ScoreWeights
    securities: list[Security] = Field(min_length=1)

    @model_validator(mode="after")
    def _full_allocation(self) -> "Universe":
        tickers = [s.ticker for s in self.securities]
        if len(tickers) != len(set(tickers)):
            raise ValueError("duplicate tickers in decision universe")
        total = self.cash_target + sum(s.target_weight for s in self.securities)
        if abs(total - 1) > 1e-4:
            raise ValueError(f"targets incl. cash must total 100%, got {total:.2%}")
        return self


class Action(str, Enum):
    INITIATE = "신규 편입"
    ADD = "추가매수"
    HOLD = "유지"
    TRIM_WATCH = "소폭 조정 검토"
    REDUCE = "축소"
    EXIT = "전량 정리"
    WATCH = "관찰"
    CASH = "현금 조정"


class Row(BaseModel):
    ticker: str
    current: float
    target: float
    change: float
    action: Action
    urgency: str
    amount: float
    shares: float | None
    price: float | None
    score: float | None = None
    security: Security | None = None


class Plan(BaseModel):
    total_value: float
    priced_at: str | None
    missing_prices: list[str]
    stale_prices: list[str]
    current: dict[str, float]
    rows: list[Row]
    ranked: list[tuple[str, float]]
    alerts: list[str]
    target_errors: list[str]
    score: "PortfolioScore"
    target_score: "PortfolioScore"


# --- 100-point portfolio score -------------------------------------------------------------
# Fixed formula so the number is comparable run to run. Components (weight):
#   보유 종목 질 (50): 현재 비중 가중 평균 종합점수
#   thesis 건강도 (15): 비중 가중 thesis 상태 점수
#   집중도 (15): 상한 초과 1%p당 -5, 상위 2종목 합 60% 초과 1%p당 -2
#   현금 여력 (5): 최소 현금 이상이면 100, 미달이면 비례
#   목표 정렬 (15): 목표까지 회전율 0% = 100, 30% 이상 = 0
SCORE_WEIGHTS = {"quality": 0.50, "thesis": 0.15, "concentration": 0.15, "cash": 0.05,
                 "alignment": 0.15}
SCORE_LABELS = {"quality": "보유 종목 질", "thesis": "thesis 건강도", "concentration": "집중도",
                "cash": "현금 여력", "alignment": "목표 정렬"}
THESIS_POINTS = {ThesisStatus.STRENGTHENING: 100, ThesisStatus.STABLE: 75,
                 ThesisStatus.EMERGING: 60, ThesisStatus.WEAKENING: 30, ThesisStatus.BROKEN: 0}


class PortfolioScore(BaseModel):
    total: float
    components: dict[str, float]
    notes: list[str]


def portfolio_score(weights: dict[str, float], universe: Universe, c: Constraints,
                    core: set[str]) -> PortfolioScore:
    by = {s.ticker: s for s in universe.securities}
    held = {t: w for t, w in weights.items() if t != "CASH" and w > 0}
    invested = sum(held.values()) or 1.0
    notes = []
    unscored = [t for t in held if t not in by]
    if unscored:
        notes.append(f"판단 없는 보유 종목 {unscored}은 0점으로 계산")
    quality = sum(w * (by[t].score(universe.score_weights) if t in by else 0)
                  for t, w in held.items()) / invested
    thesis = sum(w * (THESIS_POINTS[by[t].thesis_status] if t in by else 0)
                 for t, w in held.items()) / invested
    penalty = 0.0
    for t, w in held.items():
        limit = c.max_core_position_weight if t in core else c.max_single_position_weight
        if w > limit:
            penalty += (w - limit) * 100 * 5
            notes.append(f"{t} 상한 초과 {(w - limit) * 100:.1f}%p")
    top2 = sum(sorted(held.values(), reverse=True)[:2])
    if top2 > 0.60:
        penalty += (top2 - 0.60) * 100 * 2
        notes.append(f"상위 2종목 합 {top2:.0%}")
    concentration = max(0.0, 100 - penalty)
    cash_w = weights.get("CASH", 0.0)
    cash = 100.0 if cash_w >= c.min_cash_weight else 100 * cash_w / c.min_cash_weight
    targets = {s.ticker: s.target_weight for s in universe.securities} | {"CASH": universe.cash_target}
    turnover = sum(abs(weights.get(t, 0) - targets.get(t, 0)) for t in set(weights) | set(targets)) / 2
    alignment = max(0.0, 100 * (1 - turnover / 0.30))
    components = {"quality": quality, "thesis": thesis, "concentration": concentration,
                  "cash": cash, "alignment": alignment}
    total = sum(components[k] * SCORE_WEIGHTS[k] for k in components)
    return PortfolioScore(total=round(total, 1),
                          components={k: round(v, 1) for k, v in components.items()}, notes=notes)


Plan.model_rebuild()


def load_portfolio() -> Portfolio:
    return Portfolio.model_validate(read_json(paths.CONFIG / "portfolio.json"))


def load_constraints() -> Constraints:
    return Constraints.model_validate(read_json(paths.CONFIG / "portfolio_constraints.json"))


def load_universe() -> Universe:
    return Universe.model_validate(read_json(paths.CONFIG / "decision_universe.json"))


def validate_targets(universe: Universe, portfolio: Portfolio, c: Constraints) -> list[str]:
    errors = []
    core = {p.ticker for p in portfolio.positions if p.core_position}
    if not c.min_cash_weight - 1e-9 <= universe.cash_target <= c.max_cash_weight + 1e-9:
        errors.append(f"현금 목표 {universe.cash_target:.0%}가 허용범위 "
                      f"{c.min_cash_weight:.0%}~{c.max_cash_weight:.0%} 밖입니다.")
    for s in universe.securities:
        limit = c.max_core_position_weight if s.ticker in core else c.max_single_position_weight
        if s.target_weight > limit + 1e-9:
            errors.append(f"{s.ticker} 목표 {s.target_weight:.0%}가 상한 {limit:.0%}를 넘습니다.")
    held = {p.ticker for p in portfolio.positions}
    missing = held - {s.ticker for s in universe.securities}
    if missing:
        errors.append(f"보유 종목 {sorted(missing)}에 대한 판단이 decision_universe에 없습니다.")
    return errors


def current_weights(portfolio: Portfolio, quotes: dict[str, Any]) -> tuple[float, dict[str, float], list[str], dict[str, float]]:
    values, missing = {}, []
    for p in portfolio.positions:
        quote = quotes.get(p.ticker)
        if quote and quote.get("price"):
            values[p.ticker] = p.shares * quote["price"]
        elif p.market_value is not None:
            values[p.ticker] = p.market_value
            missing.append(p.ticker)
        else:
            missing.append(p.ticker)
    total = portfolio.cash + sum(values.values())
    weights = {t: v / total for t, v in values.items()}
    weights["CASH"] = portfolio.cash / total
    return total, weights, missing, values


def classify(current: float, target: float, c: Constraints, is_candidate_watch: bool) -> tuple[Action, str]:
    change = target - current
    size = abs(change)
    if current == 0 and target == 0:
        return Action.WATCH, "없음"
    if current > 0 and target == 0:
        return Action.EXIT, "높음" if size >= c.consider_below else "중간"
    if current == 0 and target > 0:
        return Action.INITIATE, "높음" if size >= c.consider_below else "중간"
    if size < c.no_action_below:
        return Action.HOLD, "없음"
    if size < c.watch_below:
        return Action.TRIM_WATCH, "낮음"
    urgency = "높음" if size >= c.consider_below else "중간"
    return (Action.ADD if change > 0 else Action.REDUCE), urgency


def build_plan(portfolio: Portfolio, universe: Universe, c: Constraints,
               market: dict[str, Any]) -> Plan:
    quotes = market.get("quotes", {})
    total, current, missing, _ = current_weights(portfolio, quotes)
    rows: list[Row] = []
    by_ticker = {s.ticker: s for s in universe.securities}
    for ticker in sorted(set(by_ticker) | set(current) - {"CASH"}):
        s = by_ticker.get(ticker)
        cur, tgt = current.get(ticker, 0.0), (s.target_weight if s else 0.0)
        action, urgency = classify(cur, tgt, c, bool(s and s.watch_reason))
        price = (quotes.get(ticker) or {}).get("price")
        amount = (tgt - cur) * total
        rows.append(Row(ticker=ticker, current=cur, target=tgt, change=tgt - cur, action=action,
                        urgency=urgency, amount=amount, price=price,
                        shares=(amount / price) if price else None,
                        score=s.score(universe.score_weights) if s else None, security=s))
    cash_cur = current["CASH"]
    rows.append(Row(ticker="CASH", current=cash_cur, target=universe.cash_target,
                    change=universe.cash_target - cash_cur, action=Action.CASH,
                    urgency="중간" if abs(universe.cash_target - cash_cur) >= c.watch_below else "낮음",
                    amount=(universe.cash_target - cash_cur) * total, price=None, shares=None))
    order = {"높음": 0, "중간": 1, "낮음": 2, "없음": 3}
    rows.sort(key=lambda r: (order[r.urgency], -abs(r.change)))

    alerts = []
    core = {p.ticker for p in portfolio.positions if p.core_position}
    for t, w in current.items():
        if t == "CASH":
            continue
        limit = c.max_core_position_weight if t in core else c.max_single_position_weight
        if w > limit:
            alerts.append(f"{t} 현재 비중 {w:.1%}가 상한 {limit:.0%}를 넘습니다.")
    if cash_cur < c.min_cash_weight:
        alerts.append(f"현금 {cash_cur:.1%}가 최소 {c.min_cash_weight:.0%}보다 낮습니다.")
    stale = [t for t, q in quotes.items() if q.get("stale")]
    ranked = sorted(((s.ticker, s.score(universe.score_weights)) for s in universe.securities),
                    key=lambda x: (-x[1], x[0]))
    target_weights = {s.ticker: s.target_weight for s in universe.securities}
    target_weights["CASH"] = universe.cash_target
    return Plan(total_value=total, priced_at=market.get("fetched_at"), missing_prices=missing,
                stale_prices=stale, current=current, rows=rows, ranked=ranked, alerts=alerts,
                target_errors=validate_targets(universe, portfolio, c),
                score=portfolio_score(current, universe, c, core),
                target_score=portfolio_score(target_weights, universe, c, core))
