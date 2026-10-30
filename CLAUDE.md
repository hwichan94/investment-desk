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
- **실제 보유 수량·현금의 유일한 기준은 GitHub `main`의 `config/portfolio.json`이다.** 채팅 기억·이전 보고서·
  테스트 값을 기준으로 삼지 않는다. 사용자(또는 ChatGPT)가 GitHub에 반영해 두었다면 같은 정보를 다시 묻지 않는다.
  분석 시작 전 동기화하고, 보고서 커밋 직전 `python -m desk portfolio-check --remote --expect <시작 지문>`으로
  바뀌지 않았는지 확인한다. 바뀌었으면 기존 데이터로 커밋하지 말고 `git pull --rebase` 후 다시 계산한다.
- 테스트에 실제 보유 수량·현금을 하드코딩하지 않는다. 계산 로직은 `tests/fixtures/portfolio.json`(합성 데이터)으로,
  실제 파일은 구조·정합성만 `config/portfolio.json`에서 검증한다.
- `.secrets/`(평문 세션·키)는 절대 커밋·출력하지 않는다. `data/secure/*.enc`는 암호화본이라 커밋한다.

## 투자 성향 (상세: `config/investment_policy.md`)

- 판단 기간 12개월(4개 분기). 기간 만료 ≠ 매도. 논리가 살아 있으면 새 12개월 thesis를 쓴다.
- "증거 전에 작게 진입, 증거가 나오면 늘리고, 12개월 안에 증거가 없으면 기회비용을 따져 회수."
- 단순 하락·신고가는 단독 매도 사유가 아니다. thesis 훼손·촉매 지연·더 나은 기회가 사유다.
- 보유 종목보다 매력 없는 신규 종목은 편입하지 않는다. 포트폴리오를 불필요하게 늘리지 않는다.
- 판단을 회피하지 말고 구체적 목표 비중과 자금 이동을 제시하되, 불확실성을 함께 적는다.
- 불확실성은 기본적으로 `WAIT`가 아니라 포지션 크기로 처리하고 Base Case 행동 + 무효화 조건을 제시한다.
- Fundamentals + Estimate Revisions + Relative Momentum이 모두 개선 중인 강한 승자는 밸류에이션·신고가만으로
  축소하지 않는다(Winner Protection). 축소가 필요하면 명시적 override 사유를 남긴다.
- Core/Tactical이 지정된 종목의 밸류에이션·이벤트 위험 조정은 Tactical부터 한다.
- 핵심 종목은 5개 렌즈(Fundamentals / Estimate Revisions / Expectations Gap / Relative Momentum /
  Position & Correlation Risk)와 Regime/Narrative 정합성을 매번 확인한다. 근거가 없으면 `UNKNOWN`이다.
- 상방 비대칭이 좋고 빠른 무효화가 가능하면 2~3% Asymmetric Starter를 허용한다.

## CIS 사례 선별 적용: Thesis × Trend × Asymmetric Payoff

- 2026-10-29 전략 개선: [CIS adaptation](docs/strategy/cis-adaptation-2026-10-29.md). 상세 운영 원칙은 `config/investment_policy.md`의 CIS 반영 절과 `docs/ROUTINE.md` 3-2항을 따른다.
- **매매를 복제하지 않는다.** CIS의 사례에서 손익비 우선, 승자 보유, 감정적 물타기 배제, 추세·거래량 신호, 빠른 실패 인정만 선택적으로 통합한다. 검증되지 않은 승률·현금비중을 그대로 입력하지 않는다.
- **Core**는 사업 thesis·4개 분기 KPI로 재평가한다. 단기 가격 하락/RSI 과열만으로 청산하지 않고 Winner Protection을 유지한다.
- **Tactical**은 촉매·유효기간·가격/구조적 무효화·사전 위험예산을 갖춘다. 기본 1R(계획 손실)은 투자자산의 0.5% 이내, 고신뢰도 최대 1%로 검토하되, 갭손실로 한도 초과 가능하다. 실제 주문은 실행하지 않는다.
- 최소 투자 가능 현금 목표 5% 및 부채상환 예약 현금 제외를 유지한다. 동일 AI CAPEX 테마의 상관집중과 대안 대비 기대값을 필수 검토한다.
- 실거래 로그가 없는 승률/손익비/리스크수치는 만들지 않는다. 기존 보유 수량, 목표 비중, 점수 산식은 본 원칙만으로 자동 변경하지 않는다.

## 구조

```
desk/                     Python 패키지 (python -m desk <command>)
  fanding/                수집: browser.py(Playwright) parser.py collector.py state.py(세션 암호화)
  market.py               Yahoo 가격 + SEC 공시 목록
  technicals.py           OHLCV 지표·상대모멘텀·이벤트 가격반응
  regime.py               VIX·금리·달러·credit·breadth 시장 국면
  portfolio.py            현재 비중, 목표 검증, current→target 액션
  report.py               reports/decision-latest.md 생성
  chatgpt_feed.py          최근 72시간 구조화 분석만 담은 reports/chatgpt-feed.json 생성
  analysis.py             Claude 분석 JSON 스키마(PostAnalysis) + 검증
config/
  portfolio.json          실제 보유 수량 (source of truth, 사용자 확인만)
  decision_universe.json  종목별 점수·목표 비중·이유·위험·KPI (분석 루틴이 근거와 함께 갱신)
  official_research.json  공식 근거 스냅샷 (as_of 기준일 필수)
  portfolio_constraints.json / investment_policy.md / watchlist.json / sources.json
data/posts/<id>.json      수집된 Fanding 글
data/analyses/<id>.json   Claude 분석 결과 (content_hash로 재분석 필요 여부 판단)
data/status/              수집 상태·이력·글별 실패
data/market/              quotes/technicals/regime/filings JSON, docs/ (SEC 원문 텍스트)
reports/                  decision-latest.md, archive/
docs/ROUTINE.md           클라우드 분석 루틴 작업 지침
docs/decision-log.md      목표 비중·점수 변경 이력 (변경마다 한 항목)
docs/trader-decision-journal.md  과거 판단의 상대성과·오류 원인·룰 변경 기록
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
python -m desk portfolio-check [--remote] [--expect 지문]  # portfolio.json 지문, GitHub 최신본과 비교(다르면 exit 3)
python -m desk status     # 상태 요약
python -m pytest
```

## 포트폴리오 점수 (항상 함께 보고)

투자 관련 답변·보고서에는 **항상** 현재 포트폴리오 점수(100점 만점)와 목표 실행 시 점수를 함께 적는다.
점수는 `python -m desk recommend` 출력 또는 `reports/decision-latest.md` 상단 값을 쓰고 임의로 매기지
않는다. 공식은 `desk/portfolio.py`의 `portfolio_score` (보유 종목 질 50, thesis 15, 집중도 15,
현금 5, 목표 정렬 15). 이력: `reports/score-history.csv`.

## 투자 아이디어 평가 ("이런 거 투자하고 싶다")

사용자가 종목·테마·아이디어를 말하면 (채팅 또는 `inbox/ideas.md`) 회피하지 말고 가치판단을 한다.

1. 대상 특정: 테마면 대표 후보 2~3개 티커로 좁힌다.
2. 공식 근거: 최근 분기 실적·가이던스 (IR·SEC 원문, 링크와 기준일).
3. 점수: `decision_universe.json`과 같은 6개 항목(질·모멘텀·촉매·밸류에이션·위험·적합도)으로
   매기고 종합점수를 낸다. 보유 종목 점수표와 나란히 비교한다.
4. 다섯 가지 질문에 답한다: 기존 어느 보유 종목보다 나은가 / 12개월 KPI·촉매 / 생각을 바꿀 조건 /
   편입 재원(어느 종목에서 몇 %p) / 현재 가격에서 기대수익이 충분한가.
5. 결론: `신규 편입(목표 X%, 분할 계획)` / `관찰(어떤 조건이면 편입)` / `비추천(이유)` 중 하나.
   기존 포트폴리오와 테마가 겹치면(예: AI CAPEX) 집중도 영향을 명시한다.
6. 편입하면 포트폴리오 점수가 어떻게 바뀌는지 (전/후) 보여준다.
7. 사용자가 받아들이면 `decision_universe.json`과 `docs/decision-log.md`에 반영한다.
   사용자가 원하더라도 근거가 부족하면 그렇다고 말한다 — 듣기 좋은 결론을 만들지 않는다.
8. 5개 Trader Lens와 Regime/Narrative를 기록한다. 데이터가 없는 lens는 추정하지 않고 `UNKNOWN`으로 둔다.

결과는 `reports/ideas/YYYY-MM-DD-<ticker-or-theme>.md`로 남긴다.

## 작업 규칙

- 코드 변경 후 `python -m pytest`와 `python -m desk validate` 통과.
- 보고서가 자동 생성됐다고 최신 Fanding 내용이 목표 비중에 반영됐다고 말하지 않는다.
  반영은 `decision_universe.json`이 근거와 함께 바뀌었을 때만이다.
- 공식 근거 기준일(`official_research.json` as_of)과 보고서 생성일을 구분한다.
- 매 추천 실행에서 `docs/trader-decision-journal.md` 업데이트 필요 여부를 확인한다. 과거 추천이 합리적 대안보다
  부진했거나 룰 변경이 필요할 때만 새 항목을 추가한다.
- `reports/chatgpt-feed.json`에는 구조화 분석만 넣고 `data/posts/*`의 paid article 원문은 절대 넣지 않는다.
- Technical/Regime은 Fundamental thesis를 대체하지 않는다. RSI 과매수만으로 약세·매도를 만들지 않고,
  `RISK_OFF`만으로 Core를 자동 축소하지 않는다. 관측 데이터가 부족하면 `UNKNOWN`을 유지한다.
