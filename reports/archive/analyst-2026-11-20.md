# 애널리스트 루틴 보고서 (2026-11-20 12:10 KST)

**포트폴리오 점수 70.2 / 100 (목표 실행 시 83.8)** — `desk recommend` 출력값. 직전 보고서(70.2 / 83.8) 대비 변화 없음. 가장 큰 감점 요인: 현금 여력(16.0), 목표 정렬(49.5), 상위 2종목 집중.

## 1. 분석한 글 / 아이디어
- 232192 (T3chfeed, 11-20 미국 시황): relevance MEDIUM. 앤트로픽 상장 첫날 자금 이동으로 AI 인프라 약세, 연준 AI 과열 경고, NVDA 법무총괄 매도 예정 공지. FACT 4건 모두 WebSearch로 확인 시도했으나 UNVERIFIED(앤트로픽 가격 $83/$111.50/$97.17, Teter Form 144 30,000주 모두 검색에서 확인되지 않음. 공모가 범위 $70~78과 $80 초과 전망만 확인).
- 232205 (나스다큐, 11-20 시황): relevance MEDIUM. 3대 지수 2%↓, S&P 6일 연속 하락. 공모 조달액 $813억은 직전 글(232159)의 $107.3B와 불일치하고 확인된 최대 범위(약 $644억)와도 달라 UNVERIFIED.
- 232218 (공지·라이브 안내): relevance NONE.
- 투자 아이디어 수신함 대기 없음.

## 2. 판단 변경 여부
변경 없음. `decision_universe.json`, `portfolio.json`은 수정하지 않았다(지문 64ba3c306f2d4e4c, GitHub main과 일치).
- 두 시황 글은 가격·수급 서술이고 공식 근거가 없다. 센티먼트 악화는 신규 Starter·Tactical 크기와 매수 타이밍에 반영할 신호이며 Core 자동 축소 사유가 아니다.
- AI CAPEX 상관집중(NVDA·AVGO·VRT·AMZN)과 현금 여력 부족(투자가능 현금 $201.50)을 계속 점검한다. trader-decision-journal 추가 사유 없음.

## 3. 지금 실행할 액션 상위 3개
`reports/decision-latest.md` 그대로(제안일 뿐): TSLA 축소(목표 24%) → PLTR 추가매수(33%) → VRT 추가매수(7%). 증액은 TSLA 축소 재원이 전제다. 시장 약세(RISK_OFF 성격)에서는 VRT 신규 증액을 분할로 늦추는 것이 합리적이다.

## 4. 데이터 상태
- 공식 근거 기준일 2026-11-06(14일 경과). Fanding 수집 OK.
- 미반영 공시: NVDA 8-K(11-17 실적), AXON 8-K(11-18), CRWV 10-Q. sec.gov 원문 직접 열람 불가라 `official_research.json`은 갱신하지 않았다.
- 실행 환경: `python`(3.11)에 pydantic이 없어 `python3.13`을 사용했다.
