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

- `data/market/new_filings.json`의 최근 공시와 실적 발표 일정을 확인한다.
- 보유·후보 종목에 새 분기 실적(10-Q/10-K/8-K 실적 보도자료)이 나왔으면 회사 IR·SEC 원문을 읽고
  `config/official_research.json`에 출처를 추가하고 `as_of`를 오늘로 바꾼다.
- 웹 검색 결과는 출처 신뢰도(`config/sources.json`)를 따진다. 블로그·SNS 단독 근거로 점수를 바꾸지 않는다.

## 3. 판단 갱신 (`config/decision_universe.json`)

변경은 근거가 있을 때만, 그리고 **thesis inertia**를 지킨다.

- 한 번의 글·의견만으로 점수를 5점 넘게 바꾸지 않는다. 공식 실적·가이던스 변경은 크게 반영할 수 있다.
- 목표 비중은 정책 실행 규칙을 따른다: 1%p 미만 변화 금지, 신규 편입은 2회 분할.
- 신규 후보를 추가할 때는 다섯 가지를 모두 적는다:
  1) 기존 어느 보유 종목보다 나은가, 2) 12개월 KPI·촉매(`kpis_12m`), 3) 생각을 바꿀 조건
  (`invalidation_signals`), 4) 편입 재원(`funding_from`), 5) 현재 가격에서 기대수익이 충분한가.
  못 채우면 target 0%와 `watch_reason`으로 둔다.
- 합계(현금 포함) 100%, 현금 5~20%, 단일 30%(핵심 35%) 상한.
- 바꿨다면 `as_of`를 오늘로 하고 `docs/decision-log.md`에 항목을 추가한다:
  날짜, 무엇을(이전→이후), 왜(근거 링크·글 ID), 생각을 되돌릴 조건.

## 3-1. 투자 아이디어 수신함 (`inbox/ideas.md`)

'대기' 섹션에 항목이 있으면 각 항목을 `CLAUDE.md`의 "투자 아이디어 평가" 절차대로 평가하고
`reports/ideas/YYYY-MM-DD-<ticker-or-theme>.md`를 작성한 뒤, 항목을 '처리 완료'로 옮기고
결론 한 줄과 보고서 경로를 붙인다. 신규 편입 결론이어도 `decision_universe.json`에는 사용자가
수락하기 전까지 target 0%와 `watch_reason`("사용자 수락 대기: 제안 목표 X%")으로만 추가한다.

## 4. 보고서와 커밋

```
python -m desk market --no-filings
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

검증이 통과하면 커밋한다. 메시지 예: `analyst: 3 posts, AVGO target 14%→15%`.
푸시 충돌 시 `git pull --rebase` 후 재시도한다. `data/posts`, `data/status`, `data/market`은
수집기 소유이므로 내용을 직접 고치지 않는다.

## 하지 말 것

- 주문, 증권사 연결, 보유 수량 수정
- `.secrets/` 접근, 세션 복호화 시도
- 근거 없는 숫자, 단일 의견에 따른 급격한 비중 변경
