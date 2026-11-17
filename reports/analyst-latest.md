# 애널리스트 루틴 보고서 (2026-11-17 14:00 KST)

**포트폴리오 점수 70.6 / 100 (목표 실행 시 83.8)** — `desk recommend` 출력값. 직전 보고서(70.7 / 83.8) 대비 -0.1(가격 변동). 가장 큰 감점 요인: 현금 여력(투자 가능 현금 $201.50), 목표 정렬, 상위 2종목 집중.

## 1. 분석한 글 / 아이디어
- 231385 (T3chfeed 11/17 시황, MEDIUM): 미 상무부 GPU 원격이용 통제 최종규정, 워시 발언, PLTR NHS 연장, TSLA 베를린 사이버캡 등. WebSearch로 확인 시도: PLTR NHS는 2년 연장 옵션(~2029-03)과 연장 준비 보도까지만 확인(PARTIAL). BIS 11월 최종규정과 TSLA €3B·2029는 확인하지 못해 UNVERIFIED(2026-01 BIS 규정·$250M 4680 증설만 확인).
- 231419 (세상학개론 11/17, LOW): 유동성 이탈·저가매수 의견, 워시 연설 공유. 종목 근거 없음. 앤트로픽 20배 청약은 2차 전언이라 UNVERIFIED.
- 230741: 연회원권 공지(NONE).
- 기존 231127 보강: 10년물·12월 인상 주장 PARTIAL(10년물 4.85~4.93%, 12월 인상 확률 약 77% 보도; 5.15%는 미확인).
- 투자 아이디어 수신함 대기 없음.

## 2. 판단 변경 여부
변경 없음. 모두 단일 작가 의견이고 새 공식 근거가 없다. `decision_universe.json`, `official_research.json`, `portfolio.json`은 수정하지 않았다. trader-decision-journal 추가 사유 없음. NVDA 실적(11/18 07:00 KST)과 앤트로픽 가격결정 전이라 신규 Starter·Tactical 확대는 보류한다. Core 자동 축소는 하지 않는다.

## 3. 지금 실행할 액션 상위 3개
`reports/decision-latest.md` 그대로(제안일 뿐): TSLA 축소(목표 24%) → PLTR 추가매수(33%) → VRT 추가매수(7%). 현금이 $201.50이라 증액은 TSLA 축소 재원이 전제이며 NVDA 실적 반응 확인 후 재검토를 권한다.

## 4. 수집·데이터 상태 경고
- 공식 근거 기준일 2026-11-06(11일 전). NVDA·VRT·CRWV·AXON·CCJ·GOOG 신규 공시는 NVDA 실적 후 일괄 반영 필요.
- Fanding 수집 OK(11/17 12:54 KST). portfolio 지문 64ba3c306f2d4e4c, GitHub와 일치.
- 샌드박스 `python`(3.11)에 의존성이 없어 `python -m pip install`로 설치 후 실행했다.
