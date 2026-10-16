"""Markdown action-plan report."""
from __future__ import annotations

from datetime import datetime

from desk import paths
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


def render(plan: Plan, portfolio: Portfolio, universe: Universe, now: datetime) -> str:
    out = [
        "# 12개월 포트폴리오 액션플랜",
        "",
        f"- 생성 시각(KST): {now.strftime('%Y-%m-%d %H:%M')}",
        f"- 판단 입력 기준일(decision_universe): {universe.as_of}",
        f"- 보유 수량 기준일: {portfolio.as_of}"
        + (f" (사용자 확인 {portfolio.confirmed_at})" if portfolio.confirmed_at else ""),
        f"- 가격 기준: {(plan.priced_at or '저장 평가액')[:16]} · 평가액 ${plan.total_value:,.2f}",
        "",
        "> 실제 주문이 아닌 제안입니다. 참고 수량은 가격에 따라 바뀝니다. 세금·거래비용 미반영.",
        "",
        *score_lines(plan),
        "",
        "## 시스템 상태",
        "",
        *health_lines(now),
    ]
    if plan.missing_prices or plan.stale_prices:
        out.append(f"- 가격 누락: {plan.missing_prices or '-'} / 이전 가격 사용: {plan.stale_prices or '-'}")
    if plan.target_errors:
        out += ["", "## ⚠️ 목표 비중 검증 실패", "", *[f"- {e}" for e in plan.target_errors]]
    if plan.alerts:
        out += ["", "## 위험 알림", "", *[f"- {a}" for a in plan.alerts]]

    out += ["", "## 현재 → 목표", "",
            "| 종목 | 현재 | 목표 | 변화 | 판단 | 긴급도 | 금액 | 참고 수량 |",
            "|---|---:|---:|---:|---|---|---:|---:|"]
    for r in plan.rows:
        shares = f"{r.shares:+.2f}주" if r.shares is not None else "-"
        out.append(f"| {r.ticker} | {_pct(r.current)} | {_pct(r.target)} | {_pp(r.change)} | "
                   f"{r.action.value} | {r.urgency} | ${r.amount:+,.0f} | {shares} |")

    out += ["", "## 실행 순서와 이유", ""]
    actionable = [r for r in plan.rows if r.action not in (Action.HOLD, Action.WATCH) and r.urgency != "없음"]
    for i, r in enumerate(actionable, 1):
        out.append(f"### {i}. {r.ticker} — {r.action.value}")
        out.append("")
        if r.security:
            s = r.security
            out.append(f"- 이유: {s.why_now}")
            out.append(f"- 핵심 위험: {s.main_risk}")
            out.append(f"- 실행: {s.execution_plan}")
            if s.funding_from and r.change > 0:
                out.append(f"- 재원: {', '.join(s.funding_from)}")
            if s.kpis_12m:
                out.append(f"- 12개월 KPI: {'; '.join(s.kpis_12m)}")
            out.append(f"- 생각을 바꿀 신호: {'; '.join(s.invalidation_signals)}")
        else:
            out.append("- 현금 목표를 복원해 실적 발표·급락 시 대응 여력을 확보합니다.")
        out.append("")

    out += ["## 추가 자본 매력도 순위", "",
            "| 순위 | 종목 | 종합점수 | 근거 신뢰도 | 현재 | 목표 | 상태 |",
            "|---:|---|---:|---:|---:|---:|---|"]
    by = {s.ticker: s for s in universe.securities}
    for i, (ticker, score) in enumerate(plan.ranked, 1):
        s = by[ticker]
        out.append(f"| {i} | {ticker} | {score:.1f} | {s.evidence_confidence:.0%} | "
                   f"{_pct(plan.current.get(ticker, 0))} | {_pct(s.target_weight)} | {s.thesis_status.value} |")

    watch = [s for s in universe.securities if s.target_weight == 0 and plan.current.get(s.ticker, 0) == 0]
    if watch:
        out += ["", "## 편입하지 않은 후보", ""]
        out += [f"- **{s.ticker}**: {s.watch_reason or s.main_risk}" for s in watch]
    out.append("")
    return "\n".join(out)


def write(text: str, now: datetime) -> list[str]:
    paths.REPORTS.mkdir(parents=True, exist_ok=True)
    latest = paths.REPORTS / "decision-latest.md"
    daily = paths.REPORTS / "archive" / f"decision-{now.strftime('%Y-%m-%d')}.md"
    for target in (latest, daily):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
    return [str(latest), str(daily)]
