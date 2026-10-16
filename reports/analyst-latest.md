# 애널리스트 루틴 보고서 (2026-10-16 22:45 KST)

**포트폴리오 점수 63.1 / 100 (목표 실행 시 83.8)** — `desk recommend` 출력값. 직전 기록(score-history 2026-10-16 22:20) 63.1 / 83.8 대비 변화 없음. 가장 큰 감점 요인: 목표 정렬과 집중도(TSLA 33.3%·PLTR 36.1% 상한 초과), 현금 0.5%(최소 5% 미달).

## 1. 이번 실행: 새 글 0개, 아이디어 수신함 비어 있음
- 직전 보고서에서 전부 UNVERIFIED였던 HIGH/MEDIUM 분석의 FACT 주장을 WebSearch로 재검증했다. (WebFetch는 sec.gov·bls.gov가 프록시로 막혀 원문 직접 열람 불가. 검색 요약 기준이라 확인 강도가 낮음.)
- 결과:
  - TSMC 3Q26 매출 US$46.72B: PARTIAL (SEC 6-K 확인, EPS $4.60·설비투자 문구는 미확인) — 글 224472
  - 테슬라 독일 9월 등록 12,552대(+268.7%): CONFIRMED (KBA 수치를 복수 매체가 인용) — 글 222147
  - 9월 CPI 3.7%(예상 3.6%), 근원 2.6%: PARTIAL (Morningstar 2차 인용) — 글 224188
  - Axon 2Q26 매출 +35%, 유지율 126%, 2028 목표 매출 약 $6B·EBITDA 마진 28%: PARTIAL (2차 요약) — 글 223348
  - 미확인 유지: PPI 6.3%(8월 5.4%까지만 확인), 팔란티어 은행 AI 계약, IonQ 2026 $20억 조달(2025-10 증자와 혼동 가능), 로켓랩 Neutron 2027 연기(공식 목표는 2026 4Q 이후로만 확인)
- 아직 UNVERIFIED인 나머지 FACT(주로 LOW/MEDIUM)는 다음 실행에서 이어서 시도한다.

## 2. 판단 변경
- **변경 없음.** `decision_universe.json`·`official_research.json` 미수정, decision-log 항목 없음. 확인된 사실(TSMC 호조, 테슬라 독일 판매 급증)은 기존 방향과 같고, 공식 실적·가이던스 변경이 아니어서 thesis inertia에 따라 점수·비중을 유지한다.

## 3. 지금 실행할 액션 상위 3개 (reports/decision-latest.md)
1. TSLA 축소: 33.3% → 24%, 2회 분할(실적 전 절반). 재원 → NVDA·VRT 등.
2. NVDA 신규 편입 5% (2회 분할). 재원: FLNC·INTC·TSLA.
3. 현금 0.5% → 5% 복원, PLTR 36.1% → 33%, FLNC 전량 정리.
(참고 수량은 decision-latest.md 참조. 모두 제안이며 주문 아님.)

## 4. 경고
- 공식 근거 기준일 2026-10-06(10일 경과). 이번 실행에서 TSMC 3Q 실적이 나왔으나 보유·후보 종목이 아니라 official_research는 갱신하지 않았다. TSLA 실적 발표 예정이라 발표 후 갱신 필요.
- `data/market/new_filings.json` 없음(수집기 산출물). Fanding 수집 상태 OK.
- sec.gov·bls.gov 직접 접속 불가(프록시)로 원문 대조는 못 했다.
