# 클라우드 분석 루틴 작업 지침

이 문서는 Claude 클라우드 루틴이 실행될 때마다 따르는 절차다. 먼저 `CLAUDE.md`를 읽는다.
실제 주문은 절대 하지 않는다. `config/portfolio.json`은 수정하지 않는다.

## 0. 준비

```
pip install -e . -q
git pull --rebase
python -m desk status
python -m desk pending
```

`data/status/collector.json`의 상태가 `AUTH_REQUIRED`이면 보고서 맨 위 경고로 남기고 계속 진행한다
(수집만 멈춘 것이고 분석·가격 갱신은 계속할 수 있다).

## 1. 새 글 분석 (pending 목록 전부)

각 글 `data/posts/<id>.json`을 읽고 `data/analyses/<id>.json`을 작성한다. 스키마는
`desk/analysis.py`의 `PostAnalysis`다.

- `content_hash`, `title`, `author`는 원본 글의 값을 그대로 복사한다.
- `summary`: 3~5문장. 글의 핵심 주장.
- `relevance`: 보유·후보 종목이나 포트폴리오 판단과의 관련도.
- `claims`: 투자 판단에 의미 있는 주장만 (보통 3~12개). 문장을 길게 인용하지 말고 요약한다.
  - `FACT`는 공식 자료로 확인을 시도한다. 확인되면 `CONFIRMED`와 `evidence_url`,
    방향만 맞으면 `PARTIAL`, 반대 근거가 있으면 `CONFLICT`, 못 찾으면 `UNVERIFIED`.
  - `PREDICTION`은 채점 가능한 시점을 `due`에 넣는다.
  - `OPINION`은 `NOT_APPLICABLE`.
- `thesis_impacts`: 종목별 STRENGTHEN/WEAKEN/NEUTRAL과 이유. 근거가 약하면 magnitude LOW.
- `new_candidates`: 글에서 언급된, 아직 universe에 없는 의미 있는 티커.
- `portfolio_implication`: 이 글 때문에 바뀌어야 할 것이 있는가. 없으면 "변경 없음"과 이유.

공지·라이브 안내처럼 투자 내용이 없는 글은 relevance NONE, claims 비움으로 짧게 처리한다.

## 2. 공식 근거 확인

**1순위 근거: `data/market/docs/`.** GitHub Actions가 추적 종목마다 최신 정기보고서(10-Q/10-K/20-F/40-F)
2건과 실적 보도자료(8-K/6-K exhibit 99) 최대 4건의 SEC 원문을 텍스트로 받아 둔다. 목록과 경로는
`data/market/docs/index.json`. 수치 확인은 이 파일들을 `grep`/Read로 먼저 하고, `evidence_url`에는
index의 `sources` URL(원문 sec.gov 주소)을 적는다. 여기 없을 때만 웹 도구를 쓴다.

**검증을 건너뛰지 않는다.** 클라우드 샌드박스에서 `curl`/Python HTTP는 프록시로 막힐 수 있으므로
공식 자료는 **WebSearch / WebFetch 도구**로 찾고 읽는다 (회사 IR 보도자료, sec.gov 원문).
relevance HIGH/MEDIUM 글에서 보유·후보 종목에 관한 FACT 주장은 최소한 핵심 1~3개씩 확인을 시도하고
결과(CONFIRMED/PARTIAL/CONFLICT)와 `evidence_url`을 해당 분석 JSON에 갱신한다. 끝내 확인하지 못한 것만
UNVERIFIED로 남기고 보고서에 이유를 적는다.

- `data/market/new_filings.json`의 최근 공시와 실적 발표 일정을 확인한다.
- 보유·후보 종목에 새 분기 실적(10-Q/10-K/8-K 실적 보도자료)이 나왔으면 회사 IR·SEC 원문을 읽고
  `config/official_research.json`에 출처를 추가하고 `as_of`를 오늘로 바꾼다.
- 웹 검색 결과는 출처 신뢰도(`config/sources.json`)를 따진다. 블로그·SNS 단독 근거로 점수를 바꾸지 않는다.

## 3. 판단 갱신 (`config/decision_universe.json`)

변경은 근거가 있을 때만, 그리고 **thesis inertia**를 지킨다.

- 한 번의 글·의견만으로 점수를 5점 넘게 바꾸지 않는다. 공식 실적·가이던스 변경은 크게 반영할 수 있다.
- 핵심 종목마다 5개 렌즈를 확인한다: Fundamentals / Estimate Revisions / Expectations Gap /
  Relative Momentum / Position & Correlation Risk. 시장이 보상·처벌하는 요인과의 Regime/Narrative 정합성도
  확인한다. 근거가 없으면 반드시 `UNKNOWN`으로 두고 값을 만들지 않는다.
- Fundamentals=`STRENGTHENING`, Estimate Revisions=`IMPROVING`, Relative Momentum=`STRONG`이면
  Winner Protection을 적용한다. 밸류에이션·신고가만으로 축소하지 않으며, 예외 축소는
  `winner_protection_override_reason`에 구체적 근거를 남긴다.
- Core floor / Tactical sleeve가 있는 종목의 valuation·event-risk 축소는 Tactical부터 한다.
- 상방 비대칭이 `FAVORABLE`이고 빠른 무효화가 가능하면 불확실성을 이유로 대기하지 말고 2~3% starter를
  Base Case로 검토한다.
- `data/market/technicals.json`의 자동 Relative Momentum과 `regime.json`을 확인한다. 수동 lens가
  `UNKNOWN`일 때만 자동값을 사용하며 RSI 과매수만으로 WEAK/축소를 만들지 않는다.
- `RISK_OFF`는 신규 Starter, Tactical 크기와 매수 타이밍을 줄이는 신호다. 강한 Core를 자동 매도하지 않는다.
- 실적·뉴스 이후 시장반응을 평가할 때 `desk.technicals.calculate_event_reaction`으로 당일/익일 수익률,
  QQQ 초과수익과 거래량 배수를 계산할 수 있다. 뉴스 방향과 결합하기 전에는 반응 분류를 임의 생성하지 않는다.
- 목표 비중은 정책 실행 규칙을 따른다: 1%p 미만 변화 금지, 신규 편입은 2회 분할.
- 신규 후보를 추가할 때는 다섯 가지를 모두 적는다:
  1) 기존 어느 보유 종목보다 나은가, 2) 12개월 KPI·촉매(`kpis_12m`), 3) 생각을 바꿀 조건
  (`invalidation_signals`), 4) 편입 재원(`funding_from`), 5) 현재 가격에서 기대수익이 충분한가.
  못 채우면 target 0%와 `watch_reason`으로 둔다.
- 합계(현금 포함) 100%, 현금 5~20%, 단일 30%(핵심 35%) 상한.
- 바꿨다면 `as_of`를 오늘로 하고 `docs/decision-log.md`에 항목을 추가한다:
  날짜, 무엇을(이전→이후), 왜(근거 링크·글 ID), 생각을 되돌릴 조건.
- 매 실행마다 `docs/trader-decision-journal.md` 업데이트 필요 여부를 확인한다. 이전 추천이 합리적 대안보다
  부진했다면 결과, 과대·과소평가 요인, 재발 방지 룰을 기록한다. 단순 가격 변동만으로 오답 처리하지 않는다.

## 3-1. 투자 아이디어 수신함 (`inbox/ideas.md`)

'대기' 섹션에 항목이 있으면 각 항목을 `CLAUDE.md`의 "투자 아이디어 평가" 절차대로 평가하고
`reports/ideas/YYYY-MM-DD-<ticker-or-theme>.md`를 작성한 뒤, 항목을 '처리 완료'로 옮기고
결론 한 줄과 보고서 경로를 붙인다. 신규 편입 결론이어도 `decision_universe.json`에는 사용자가
수락하기 전까지 target 0%와 `watch_reason`("사용자 수락 대기: 제안 목표 X%")으로만 추가한다.

## 4. 보고서와 커밋

가격·공시는 GitHub Actions가 3시간마다 `data/market/`에 갱신한다. 루틴에서 `desk market`을 실행하지
않는다 (샌드박스에서 막히고, 수집기 소유 파일이다).

```
python -m desk recommend
python -m desk validate
python -m pytest -q
```

`reports/analyst-latest.md`를 쓴다 (덮어쓰기, 같은 내용을 `reports/archive/analyst-YYYY-MM-DD.md`에도):

0. 맨 위: **포트폴리오 점수 X / 100 (목표 실행 시 Y)** — `desk recommend` 출력값 그대로,
   직전 analyst 보고서 대비 변화와 가장 큰 감점 요인
1. 이번에 분석한 글과 핵심 신호 (없으면 "새 글 없음"), 처리한 투자 아이디어
2. 판단 변경 여부와 이유 (없으면 왜 유지하는지)
3. 지금 실행할 액션 상위 3개: 종목, 방향, 목표 비중, 재원, 참고 수량
4. 수집·데이터 상태 경고 (로그인 만료, 오래된 공식 근거 등)

`python -m desk recommend`가 만드는 `reports/decision-latest.md`는 한 줄 결론 → 오늘 바뀐 점 → 핵심 시황
→ 보유 Action → 신규 후보(최대 2개) → 체크포인트 → 결론 순서를 유지한다. 함께 생성되는
`reports/chatgpt-feed.json`은 최근 72시간 구조화 분석만 포함하며 paid article 원문을 넣지 않는다.

검증이 통과하면 커밋한다. 메시지 예: `analyst: 3 posts, AVGO target 14%→15%`.
푸시 충돌 시 `git pull --rebase` 후 재시도한다. `data/posts`, `data/status`, `data/market`은
수집기 소유이므로 내용을 직접 고치지 않는다.

## 하지 말 것

- 주문, 증권사 연결, 보유 수량 수정
- `.secrets/` 접근, 세션 복호화 시도
- 근거 없는 숫자, 단일 의견에 따른 급격한 비중 변경
