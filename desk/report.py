"""Markdown action-plan report."""
from __future__ import annotations

from datetime import datetime

from desk import paths
from desk.chatgpt_feed import load_recent_analyses
from desk.portfolio import SCORE_LABELS, SCORE_WEIGHTS, Action, Plan, Portfolio, Universe
from desk.store import PostStore, read_json


def _pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def _pp(x: float) -> str:
    return f"{x * 100:+.2f}%p"


def health_lines(now: datetime) -> list[str]:
    lines = []
    status = read_json(paths.STATUS / "collector.json", {}) or {}
    if status:
        lines.append(f"- Fanding 수집: **{status.get('status')}** "
                     f"(마지막 실행 {status.get('last_run_at', '-')[:16]}, "
                     f"마지막 성공 {str(status.get('last_success_at') or '-')[:16]})")
        if status.get("status") == "AUTH_REQUIRED":
            lines.append("  - ⚠️ 로그인이 만료됐습니다. PC에서 `python -m desk login`을 실행해야 합니다.")
    else:
        lines.append("- Fanding 수집: 아직 실행 기록이 없습니다.")
    store = PostStore()
    pending = store.pending_analysis()
    lines.append(f"- 저장된 글 {len(store.known_ids())}개, Claude 분석 대기 {len(pending)}개")
    official = read_json(paths.CONFIG / "official_research.json", {}) or {}
    if official.get("as_of"):
        age = (now.date() - datetime.fromisoformat(official["as_of"]).date()).days
        lines.append(f"- 공식 근거 기준일: {official['as_of']} ({age}일 전)")
    new_filings = read_json(paths.MARKET / "new_filings.json", []) or []
    recent = [f"{t}({', '.join(r['form'] for r in rows)})"
              for entry in new_filings[-5:] for t, rows in entry["filings"].items()]
    if recent:
        lines.append(f"- 최근 감지된 신규 SEC 공시: {', '.join(recent[-10:])}")
    return lines


def score_lines(plan: Plan) -> list[str]:
    cur, tgt = plan.score, plan.target_score
    lines = [f"## 포트폴리오 점수: **{cur.total:.1f} / 100** (목표 실행 시 {tgt.total:.1f})", "",
             "| 항목 | 비중 | 현재 | 목표 실행 시 |", "|---|---:|---:|---:|"]
    for key, label in SCORE_LABELS.items():
        lines.append(f"| {label} | {SCORE_WEIGHTS[key]:.0%} | {cur.components[key]:.1f} | "
                     f"{tgt.components[key]:.1f} |")
    if cur.notes:
        lines += ["", f"- 감점 요인: {'; '.join(cur.notes)}"]
    return lines


def price_freshness_lines(plan: Plan, portfolio: Portfolio, now: datetime) -> list[str]:
    if not plan.priced_at:
        freshness = "시장가격 수집 시각 없음"
    else:
        try:
            fetched_at = datetime.fromisoformat(plan.priced_at)
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=now.tzinfo)
            age_hours = max((now - fetched_at).total_seconds() / 3600, 0)
            state = "최신" if age_hours <= 24 else "오래됨"
            freshness = f"{state} · 수집 후 {age_hours:.1f}시간"
        except ValueError:
            freshness = "수집 시각 형식 확인 필요"
    fx = ("환율 적용 없음(USD 기준)" if portfolio.currency == "USD"
          else f"{portfolio.currency} 환율 데이터 별도 확인 필요")
    return [f"- 시장가격 최신성: {freshness}", f"- 통화/환율: {fx}"]


def funding_lines(plan: Plan) -> list[str]:
    cash_first = ", ".join(
        f"{ticker} ${amount:,.2f}" for ticker, amount in plan.cash_first_allocations.items()
    ) or "해당 없음"
    return [
        f"- 총자산: **${plan.total_value:,.2f}** "
        f"(주식 ${plan.equity_value:,.2f} + 투자 가능 현금 "
        f"${plan.cash_available_for_investing:,.2f} + 부채상환 예약 현금 "
        f"${plan.cash_reserved_for_debt:,.2f})",
        f"- 신규 투자 가능 현금: **${plan.cash_available_for_investing:,.2f}** · "
        f"현금 목표 ${plan.cash_target_amount:,.2f} 유지 시 즉시 배분 가능 "
        f"${plan.cash_available_for_buys:,.2f}",
        f"- 기존 종목 매도 없이 우선 집행 검토: {cash_first}",
        f"- 추천 매수 합계 ${plan.recommended_buy_amount:,.2f} · "
        f"계획 매도 재원 ${plan.planned_sell_proceeds:,.2f} · "
        f"매도 재원 필요분 ${plan.sales_funded_buy_amount:,.2f}",
        "- 현금 보유 자체는 매수 신호가 아닙니다. 종합점수·펀더멘털·시장행동을 통과한 "
        "ADD/INITIATE만 위 재원 안에서 배분합니다.",
    ]


def append_score_history(plan: Plan, now: datetime) -> None:
    path = paths.REPORTS / "score-history.csv"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("at,total,target_total," + ",".join(SCORE_WEIGHTS) + "\n", encoding="utf-8",
                        newline="\n")
    row = [now.strftime("%Y-%m-%d %H:%M"), f"{plan.score.total:.1f}", f"{plan.target_score.total:.1f}"]
    row += [f"{plan.score.components[k]:.1f}" for k in SCORE_WEIGHTS]
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(",".join(row) + "\n")


def _one_line_conclusion(plan: Plan) -> str:
    if plan.target_errors:
        return "목표 검증 오류를 먼저 해소할 때까지 해당 축소·편입안은 실행 보류가 Base Case입니다."
    actionable = [row for row in plan.rows
                  if row.action not in (Action.HOLD, Action.WATCH, Action.CASH)
                  and row.urgency != "없음"]
    if not actionable:
        return "새로 실행할 비중 변경 없이 기존 목표와 thesis를 유지하는 것이 Base Case입니다."
    if plan.cash_first_allocations:
        cash_first = ", ".join(
            f"{ticker} ${amount:,.0f}" for ticker, amount in plan.cash_first_allocations.items()
        )
        return (f"기존 종목 매도 전 현금으로 {cash_first}를 우선 검토하고, "
                "나머지 목표 조정은 시장·실적 신호를 확인해 단계적으로 실행하는 것이 "
                "Base Case입니다.")
    summary = ", ".join(f"{row.ticker} {row.action.value}({_pct(row.target)})"
                        for row in actionable[:3])
    return f"Base Case는 {summary}이며, 각 무효화 신호가 나오면 즉시 재평가합니다."


def _recent_change_lines(now: datetime) -> tuple[list[str], list[str]]:
    recent = load_recent_analyses(now)
    changes = list(dict.fromkeys(item.portfolio_implication for item in recent))[:3]
    market = []
    for item in recent:
        if item.relevance not in ("HIGH", "MEDIUM"):
            continue
        market.append(f"- **{item.title}**: {item.summary} → {item.portfolio_implication}")
        if len(market) == 3:
            break
    if not changes:
        changes = ["최근 72시간 내 새 구조화 분석이 없어 기존 Base Case와 목표 비중을 유지합니다."]
    if not market:
        market = ["- 최근 72시간 내 HIGH/MEDIUM 시황 분석 없음 → 기존 포트폴리오 영향 판단 유지"]
    return [f"- {line}" for line in changes], market


def technical_context_lines(plan: Plan) -> list[str]:
    regime_effect = {
        "RISK_ON": "신규 Starter/Tactical 정상 운용, Core 유지",
        "NEUTRAL": "종목별 신호 우선, Core 유지",
        "RISK_OFF": "신규 Starter·Tactical 크기 축소, Core 자동매도 금지",
        "UNKNOWN": "데이터 부족으로 비중 조정 없음",
    }[plan.regime if plan.regime in {"RISK_ON", "NEUTRAL", "RISK_OFF"} else "UNKNOWN"]
    priorities = ("VIX", "credit", "breadth", "QQQ", "SPY")
    ordered_reasons = sorted(
        plan.regime_reasons,
        key=lambda value: next((index for index, key in enumerate(priorities) if key in value), 99),
    )
    reason = "; ".join(ordered_reasons[:3]) or "구성요소 데이터 부족"
    lines = [f"- **Regime: {plan.regime}** — {reason} → {regime_effect}"]
    priority = sorted(
        (row for row in plan.rows if row.ticker != "CASH" and row.technical_signal),
        key=lambda row: (not row.winner_protection_active,
                         row.relative_momentum.value not in ("STRONG", "WEAK"), row.ticker),
    )
    for row in priority[:3]:
        implication = row.timing_note
        if row.winner_protection_active:
            implication = implication or "RSI 과열만으로 축소 금지"
        elif row.relative_momentum.value == "WEAK" and row.security and row.security.fundamentals_improving:
            implication = implication or "추격매수 금지, 분할·반전 확인"
        line = row.technical_signal
        if implication and implication not in line:
            line += f" → {implication}"
        lines.append(f"- {line}")
    return lines


def render(plan: Plan, portfolio: Portfolio, universe: Universe, now: datetime) -> str:
    conclusion = _one_line_conclusion(plan)
    changed_lines, market_lines = _recent_change_lines(now)
    by = {s.ticker: s for s in universe.securities}
    out = [
        "# 12개월 포트폴리오 액션플랜",
        "",
        f"- 생성 시각(KST): {now.strftime('%Y-%m-%d %H:%M')}",
        f"- 판단 입력 기준일(decision_universe): {universe.as_of}",
        f"- 보유 수량 기준일: {portfolio.as_of}"
        + (f" (사용자 확인 {portfolio.confirmed_at})" if portfolio.confirmed_at else ""),
        f"- 가격 기준: {(plan.priced_at or '시장가격 미수집')[:16]} · 총자산 ${plan.total_value:,.2f}",
        f"- 투자 가능 현금: ${plan.cash_available_for_investing:,.2f}",
        f"- 부채상환 예약 현금: ${plan.cash_reserved_for_debt:,.2f} "
        "(총자산·비중에는 포함, 신규매수 재원에서는 제외)",
        "",
        "> 실제 주문이 아닌 제안입니다. 참고 수량은 가격에 따라 바뀝니다. 세금·거래비용 미반영.",
        "",
        "## 1. 한 줄 결론",
        "",
        f"> {conclusion}",
        "",
        *score_lines(plan),
        "",
        "## 데이터 상태",
        "",
        *health_lines(now),
        *price_freshness_lines(plan, portfolio, now),
    ]
    if plan.missing_prices or plan.stale_prices:
        out.append(f"- 가격 누락: {plan.missing_prices or '-'} / 이전 가격 사용: {plan.stale_prices or '-'}")
    if plan.target_errors:
        out += ["", "## ⚠️ 목표 비중 검증 실패", "", *[f"- {e}" for e in plan.target_errors]]
    if plan.alerts:
        out += ["", "## 위험 알림", "", *[f"- {a}" for a in plan.alerts]]

    out += ["", "## 매수재원 검증", "", *funding_lines(plan)]

    out += ["", "## Technical / Regime 핵심 신호", "", *technical_context_lines(plan)]

    out += ["", "## 2. 오늘 바뀐 점", "", *changed_lines,
            "", "## 3. 놓치면 안 되는 시황", "", *market_lines,
            "", "## 4. 보유 종목 Action (현재 → 목표)", "",
            "| 종목 | 현재 | 목표 | 변화 | 판단 | 구분 | 긴급도 | 금액 | 참고 수량 |",
            "|---|---:|---:|---:|---|---|---|---:|---:|"]
    holding_rows = [row for row in plan.rows if row.ticker == "CASH" or row.current > 0]
    for r in holding_rows:
        shares = f"{r.shares:+.2f}주" if r.shares is not None else "-"
        sleeve = r.trim_source or "-"
        if r.security and r.security.core_floor_weight is not None:
            sleeve = (f"Core≥{_pct(r.security.core_floor_weight)}"
                      + (f" / Tactical {_pct(r.security.tactical_weight)}"
                         if r.security.tactical_weight is not None else ""))
        ticker_label = "부채상환 예약현금" if r.ticker == "RESERVED_CASH" else r.ticker
        out.append(f"| {ticker_label} | {_pct(r.current)} | {_pct(r.target)} | {_pp(r.change)} | "
                   f"{r.action.value} | {sleeve} | {r.urgency} | ${r.amount:+,.0f} | {shares} |")

    out += ["", "### 5개 렌즈 + Regime", "",
            "| 종목 | Fundamentals | Estimate Revisions | Expectations Gap | Relative Momentum | Position & Correlation Risk | Regime |",
            "|---|---|---|---|---|---|---|"]
    for r in holding_rows:
        if not r.security:
            continue
        s = r.security
        out.append(f"| {r.ticker} | {s.thesis_status.value} | {s.estimate_revisions.value} | "
                   f"{s.expectations_gap.value} | {r.relative_momentum.value} | "
                   f"risk {s.risk_control:.0f} / fit {s.portfolio_fit:.0f} | "
                   f"{r.regime_alignment.value} |")

    out += ["", "### Base Case 실행 순서와 이유", ""]
    actionable = [r for r in plan.rows
                  if r.action not in (Action.HOLD, Action.WATCH, Action.CASH)
                  and r.urgency != "없음"]
    for i, r in enumerate(actionable[:3], 1):
        out.append(f"#### {i}. {r.ticker} — {r.action.value}")
        out.append("")
        if r.security:
            s = r.security
            out.append(f"- 이유: {s.why_now}")
            out.append(f"- 핵심 위험: {s.main_risk}")
            out.append(f"- 실행: {s.execution_plan}")
            if r.technical_signal:
                out.append(f"- 시장행동: {r.technical_signal}")
            if r.timing_note:
                out.append(f"- 타이밍 조정: {r.timing_note}")
            if s.funding_from and r.change > 0:
                out.append(f"- 재원: {', '.join(s.funding_from)}")
            if s.kpis_12m:
                out.append(f"- 12개월 KPI: {'; '.join(s.kpis_12m)}")
            out.append(f"- 생각을 바꿀 신호: {'; '.join(s.invalidation_signals)}")
        else:
            out.append("- 현금 목표를 복원해 실적 발표·급락 시 대응 여력을 확보합니다.")
        out.append("")

    candidates = [r for r in plan.rows
                  if r.ticker not in {"CASH", "RESERVED_CASH"} and r.current == 0 and r.security]
    candidates.sort(key=lambda r: (r.target <= 0, -(r.score or 0), r.ticker))
    out += ["## 5. 신규 후보 (최대 2개)", ""]
    if candidates:
        for r in candidates[:2]:
            s = r.security
            starter = " · Asymmetric Starter" if r.asymmetric_starter else ""
            out += [f"- **{r.ticker} — {r.action.value}, 목표 {_pct(r.target)}{starter}**: {s.why_now}",
                    f"  - 기존 보유 대비/재원: {', '.join(s.funding_from) if s.funding_from else '지정 없음'}",
                    f"  - 무효화: {'; '.join(s.invalidation_signals)}"]
            if r.technical_signal:
                out.append(f"  - 시장행동: {r.technical_signal}")
            if r.timing_note:
                out.append(f"  - 타이밍 조정: {r.timing_note}")
    else:
        out.append("- 없음")

    checkpoints = []
    for r in [*actionable, *holding_rows]:
        if not r.security:
            continue
        signal = (r.security.kpis_12m[0] if r.security.kpis_12m
                  else r.security.invalidation_signals[0])
        item = f"- **{r.ticker}**: {signal}"
        if item not in checkpoints:
            checkpoints.append(item)
        if len(checkpoints) == 5:
            break
    out += ["", "## 6. 다음 체크포인트", "", *(checkpoints or ["- 새 체크포인트 없음"]),
            "", "## 부록: 추가 자본 매력도 순위", "",
            "| 순위 | 종목 | 종합점수 | 근거 신뢰도 | 현재 | 목표 | 상태 |",
            "|---:|---|---:|---:|---:|---:|---|"]
    for i, (ticker, score) in enumerate(plan.ranked, 1):
        s = by[ticker]
        out.append(f"| {i} | {ticker} | {score:.1f} | {s.evidence_confidence:.0%} | "
                   f"{_pct(plan.current.get(ticker, 0))} | {_pct(s.target_weight)} | {s.thesis_status.value} |")

    out += ["", "## 7. 결론", "", conclusion, "",
            "실제 주문은 사용자가 결정하며, 무효화 조건이나 공식 실적 변화가 확인되면 Base Case를 갱신합니다.", ""]
    return "\n".join(out)


def write(text: str, now: datetime) -> list[str]:
    paths.REPORTS.mkdir(parents=True, exist_ok=True)
    latest = paths.REPORTS / "decision-latest.md"
    daily = paths.REPORTS / "archive" / f"decision-{now.strftime('%Y-%m-%d')}.md"
    for target in (latest, daily):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
    return [str(latest), str(daily)]
