"""Command line: python -m desk <command>"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from desk import paths


def _setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def cmd_login(args: argparse.Namespace) -> int:
    from desk.fanding import state
    from desk.fanding.browser import interactive_login
    from desk.fanding.parser import load_selectors

    existing = None
    try:
        existing = state.load_state()
    except Exception:
        pass
    print("브라우저가 열립니다. Fanding에 직접 로그인해 주세요. (최대 10분 대기)")
    result = interactive_login(load_selectors(), paths.FEED_URL, existing, timeout_s=args.timeout)
    if result is None:
        print("로그인이 확인되지 않았습니다. 다시 실행해 주세요.")
        return 2
    paths.SECRETS.mkdir(parents=True, exist_ok=True)
    key = state.ensure_local_key()
    state.save_state(result, key)
    print("로그인 세션을 저장했습니다.")
    print(f"- 로컬 원본: {paths.STATE_PLAIN} (git 제외)")
    print(f"- 암호화본: {paths.STATE_ENCRYPTED} (커밋 대상)")
    print(f"- 복호화 키: {paths.STATE_KEY_FILE} → GitHub Secret FANDING_STATE_KEY 에 한 번 등록")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    from desk.fanding.collector import check

    code = check(paths.now_kst(), headless=not args.headed)
    status = json.loads((paths.STATUS / "collector.json").read_text(encoding="utf-8"))
    print(json.dumps({k: status[k] for k in ("status", "message", "discovered", "created",
                                             "updated", "unchanged", "locked", "failures")},
                     ensure_ascii=False, indent=1))
    return code


def cmd_market(args: argparse.Namespace) -> int:
    from desk import market

    summary = market.update(paths.now_kst(), with_filings=not args.no_filings)
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0 if summary["quotes"] else 1


def cmd_recommend(args: argparse.Namespace) -> int:
    from desk import chatgpt_feed, portfolio, portfolio_sync, report
    from desk.store import read_json

    now = paths.now_kst()
    pf, universe, constraints = (portfolio.load_portfolio(), portfolio.load_universe(),
                                 portfolio.load_constraints())
    plan = portfolio.build_plan(pf, universe, constraints,
                                read_json(paths.MARKET / "quotes.json", {}) or {},
                                read_json(paths.MARKET / "technicals.json", {}) or {},
                                read_json(paths.MARKET / "regime.json", {}) or {})
    written = report.write(report.render(plan, pf, universe, now), now)
    feed_path = chatgpt_feed.write(plan, pf, universe, now)
    report.append_score_history(plan, now)
    print(f"포트폴리오 지문: {portfolio_sync.fingerprint(portfolio_sync.local_raw())}")
    print(f"포트폴리오 점수: {plan.score.total:.1f} / 100 (목표 실행 시 {plan.target_score.total:.1f})")
    print(f"보고서: {written[0]}")
    print(f"ChatGPT feed: {feed_path}")
    if plan.target_errors:
        print("목표 비중 검증 실패:", *plan.target_errors, sep="\n- ")
        return 1
    return 0


def cmd_pending(args: argparse.Namespace) -> int:
    from desk.store import PostStore

    for post in PostStore().pending_analysis():
        print(f"{post.post_id}\t{post.author}\t{post.title}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    from desk import analysis, portfolio, regime, technicals
    from desk.store import read_json

    errors = analysis.validate_all()
    try:
        pf, uni, c = portfolio.load_portfolio(), portfolio.load_universe(), portfolio.load_constraints()
        errors += portfolio.validate_targets(uni, pf, c)
    except Exception as exc:
        errors.append(f"config: {exc}")
    technical_snapshot = read_json(paths.MARKET / "technicals.json")
    if technical_snapshot is not None:
        errors += technicals.validate_snapshot(technical_snapshot)
    regime_snapshot = read_json(paths.MARKET / "regime.json")
    if regime_snapshot is not None:
        errors += regime.validate_snapshot(regime_snapshot)
    print("OK" if not errors else "\n".join(errors))
    return 1 if errors else 0


def cmd_portfolio_check(args: argparse.Namespace) -> int:
    from desk import portfolio_sync

    ok, messages = portfolio_sync.check(expect=args.expect, remote=args.remote)
    print("\n".join(messages))
    return 0 if ok else 3


def cmd_status(args: argparse.Namespace) -> int:
    from desk.report import health_lines

    print("\n".join(health_lines(paths.now_kst())))
    return 0


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    parser = argparse.ArgumentParser(prog="desk", description="개인 AI 투자 리서치 데스크")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("login", help="브라우저를 띄워 사용자가 직접 Fanding 로그인")
    p.add_argument("--timeout", type=int, default=600)
    p.set_defaults(func=cmd_login)
    p = sub.add_parser("check", help="Fanding 새 글·수정 글 1회 수집")
    p.add_argument("--headed", action="store_true")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("market", help="가격·SEC 공시 갱신")
    p.add_argument("--no-filings", action="store_true")
    p.set_defaults(func=cmd_market)
    sub.add_parser("recommend", help="액션플랜 보고서 생성").set_defaults(func=cmd_recommend)
    sub.add_parser("pending", help="Claude 분석 대기 글 목록").set_defaults(func=cmd_pending)
    sub.add_parser("validate", help="분석·설정 파일 검증").set_defaults(func=cmd_validate)
    p = sub.add_parser("portfolio-check", help="portfolio.json 지문 출력·GitHub 최신본과 비교")
    p.add_argument("--expect", help="분석 시작 때 기록한 지문. 다르면 exit 3")
    p.add_argument("--remote", action="store_true", help="origin/main의 portfolio.json과 비교(fetch 포함)")
    p.set_defaults(func=cmd_portfolio_check)
    sub.add_parser("status", help="시스템 상태 요약").set_defaults(func=cmd_status)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
