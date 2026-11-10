# 애널리스트 루틴 보고서 (2026-11-10 13:20 KST)

**포트폴리오 점수 71.6 / 100 (목표 실행 시 83.8)** — `desk recommend` 출력값. 직전 보고서(71.4 / 83.8) 대비 현재 +0.2(가격 변동), 목표 실행 시 동일. 주요 감점 요인: 목표 정렬, 현금 여력(투자 가능 현금 $201.50, 5% 목표 미달), 보유 종목 질.

## 1. 분석한 글 / 아이디어
- **229854 (T3chfeed, HIMS 3Q 실적)** relevance LOW: 매출 $890M(+49%)과 연간 조정 EBITDA 가이던스 하향($275~325M → $257~277M)은 [SEC 8-K](https://www.sec.gov/Archives/edgar/data/0001773751/000177375126000242/hims-20260930x8xkearningsr.htm)로 CONFIRMED. 구독자 YoY +13%·매출총이익률 약 57%는 PARTIAL. 컨센서스 대비 미스 수치와 분기 EBITDA는 UNVERIFIED(2차 매체 수치 상충). HIMS는 보유·후보 종목이 아니라 thesis 영향 없음.
- 아이디어 수신함 '대기' 없음.

## 2. 판단 변경
- 변경 없음. `decision_universe.json`, `portfolio.json`(지문 64ba3c306f2d4e4c) 미수정. 새 글은 비보유 종목이고, 마지막 분석 이후 새 SEC 공시도 없다. 저널 갱신 불필요.

## 3. 지금 실행할 액션 상위 3개 (제안, 주문 아님)
decision-latest 기준: TSLA 축소(목표 24%, -6.23주), PLTR 추가매수(33%, +3.26주), VRT 추가매수(7%, +5.22주). 재원·상세는 `reports/decision-latest.md` 참조.

## 4. 데이터 상태 경고
- Fanding 수집 OK(2026-11-10 12:37 KST). 공식 근거 기준일 2026-11-06(4일 전).
- 투자 가능 현금 5% 목표 미달.
- 환경: `python`은 3.11인데 pip는 3.13에 설치되어 `python3.13 -m desk`로 실행. validate OK, pytest 통과.
