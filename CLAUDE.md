# 개인 AI 투자 리서치 데스크

Fanding 새 글을 감지 → 주장을 구조화 → 공식 자료(IR·SEC·정부)로 검증 → 보유 종목과 신규 후보를
같은 기준으로 비교 → 매번 `유지 / 추가매수 / 축소 / 전량 정리 / 신규 편입`과 목표 비중,
자금 출처를 제안한다. 요약기가 아니다.

## 절대 원칙

- **주문 기능 없음.** 증권사 API·자동매매를 만들거나 연결하지 않는다. 모든 액션은 제안이다.
- **계정 정보 저장 금지.** Fanding ID/PW를 코드·설정·로그·문서에 두지 않는다. 로그인은 사용자가
  `python -m desk login`으로 연 브라우저에서 직접 한다. paywall·잠긴 글·인증 우회 금지.
- **숫자 생성 금지.** 없는 값은 `UNKNOWN`. 출처 없는 수치를 쓰지 않는다.
- **`config/portfolio.json`은 사용자가 실제 거래를 확인해 준 경우에만 수정한다.** 추천 수량을 보유
  수량으로 착각하지 않는다. 수정 시 `as_of`/`confirmed_at` 갱신.
- `.secrets/`(평문 세션·키)는 절대 커밋·출력하지 않는다. `data/secure/*.enc`는 암호화본이라 커밋한다.

## 투자 성향 (상세: `config/investment_policy.md`)

- 판단 기간 12개월(4개 분기). 기간 만료 ≠ 매도. 논리가 살아 있으면 새 12개월 thesis를 쓴다.
- "증거 전에 작게 진입, 증거가 나오면 늘리고, 12개월 안에 증거가 없으면 기회비용을 따져 회수."
- 단순 하락·신고가는 단독 매도 사유가 아니다. thesis 훼손·촉매 지연·더 나은 기회가 사유다.
- 보유 종목보다 매력 없는 신규 종목은 편입하지 않는다. 포트폴리오를 불필요하게 늘리지 않는다.
- 판단을 회피하지 말고 구체적 목표 비중과 자금 이동을 제시하되, 불확실성을 함께 적는다.

## 구조

```
desk/                     Python 패키지 (python -m desk <command>)
  fanding/                수집: browser.py(Playwright) parser.py collector.py state.py(세션 암호화)
  market.py               Yahoo 가격 + SEC 공시 목록
  portfolio.py            현재 비중, 목표 검증, current→target 액션
  report.py               reports/decision-latest.md 생성
  analysis.py             Claude 분석 JSON 스키마(PostAnalysis) + 검증
config/
  portfolio.json          실제 보유 수량 (source of truth, 사용자 확인만)
  decision_universe.json  종목별 점수·목표 비중·이유·위험·KPI (분석 루틴이 근거와 함께 갱신)
  official_research.json  공식 근거 스냅샷 (as_of 기준일 필수)
  portfolio_constraints.json / investment_policy.md / watchlist.json / sources.json
data/posts/<id>.json      수집된 Fanding 글
data/analyses/<id>.json   Claude 분석 결과 (content_hash로 재분석 필요 여부 판단)
data/status/              수집 상태·이력·글별 실패
data/market/              quotes.json, filings.json, new_filings.json
reports/                  decision-latest.md, archive/
docs/ROUTINE.md           클라우드 분석 루틴 작업 지침
docs/decision-log.md      목표 비중·점수 변경 이력 (변경마다 한 항목)
```

## 실행 흐름

1. **GitHub Actions `collect`** (3시간마다, `.github/workflows/collect.yml`):
   `desk check` → `desk market` → `desk recommend` → `data/`, `reports/` 커밋.
   로그인 만료(`AUTH_REQUIRED`)나 DOM 변경이면 run을 실패시켜 GitHub이 이메일로 알린다.
2. **Claude 클라우드 루틴** (`docs/ROUTINE.md`): 분석 대기 글 해석·검증, 공식 근거 갱신,
   `decision_universe.json` 검토, 보고서 재생성, 커밋.
3. **PC(사용자)**: 로그인 만료 시 `python -m desk login` 후 `data/secure/fanding_state.enc` 커밋·푸시.

## 명령

```
python -m desk login      # 브라우저를 띄워 사용자가 직접 로그인 (PC 전용)
python -m desk check      # Fanding 1회 수집 (--headed로 화면 표시)
python -m desk market     # 가격·SEC 공시 갱신
python -m desk recommend  # 액션플랜 보고서
python -m desk pending    # 분석 대기 글
python -m desk validate   # 분석 JSON·목표 비중 검증
python -m desk status     # 상태 요약
python -m pytest
```

## 작업 규칙

- 코드 변경 후 `python -m pytest`와 `python -m desk validate` 통과.
- 보고서가 자동 생성됐다고 최신 Fanding 내용이 목표 비중에 반영됐다고 말하지 않는다.
  반영은 `decision_universe.json`이 근거와 함께 바뀌었을 때만이다.
- 공식 근거 기준일(`official_research.json` as_of)과 보고서 생성일을 구분한다.
