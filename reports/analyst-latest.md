# 애널리스트 루틴 보고서 (2026-11-18 22:15 KST)

**포트폴리오 점수 70.4 / 100 (목표 실행 시 83.8)** — `desk recommend` 출력값. 직전 보고서(70.4 / 83.8)와 변화 없음. 가장 큰 감점 요인: 현금 여력(투자 가능 현금 $201.50), 목표 정렬, 상위 종목 집중.

## 1. 분석한 글 / 아이디어
- 231698 (T3chfeed, 젠슨 황 없는 엔비디아 실적, MEDIUM): FY28 성장률 70→75% 상향, Edge Computing $82억(+42% YoY) 해석, CEO 교체 리스크. NVDA STRENGTHEN/LOW. 영업이익·매출은 8-K 웹검색 대조, Edge 수치·멀티플은 UNVERIFIED.
- 231841 (세상학개론, NVDA 지급보증 정리, HIGH): 직접투자 $82.5B + 보증 $170B 집계(OpenAI 비중 큼), 실질 보증 약 $60B. 영업이익 $77.5B만 CONFIRMED(8-K), 보증 집계는 작가 자체 집계로 UNVERIFIED(Q3 10-Q 주석 대조 필요). NVDA/CRWV NEUTRAL/LOW — 순환금융 리스크 점검 항목으로만 추가.
- 231822 (나스다큐, 로켓랩 Neutron 엔진 시험, LOW): RKLB는 보유·후보 밖. 650회 시험 공지는 웹검색에서 미확인. 변경 없음.
- 투자 아이디어 수신함 대기 없음.

## 2. 판단 변경 여부
변경 없음. 새 공식 근거로 점수를 움직일 내용이 없고, 단일 작가 의견·미검증 집계로 비중을 바꾸지 않는다. `decision_universe.json`, `official_research.json`, `portfolio.json` 미수정. trader-decision-journal 추가 사유 없음.

## 3. 지금 실행할 액션 상위 3개
`reports/decision-latest.md` 그대로(제안일 뿐): TSLA 축소(목표 24%) → PLTR 추가매수(33%) → VRT 추가매수(7%). 현금 $201.50이라 증액은 TSLA 축소 재원이 전제다.

## 4. 수집·데이터 상태 경고
- NVDA FQ3 8-K(11/17)는 data/market/docs에 아직 없음(path null). 다음 collect 후 보증·구매의무와 세그먼트 수치 대조 필요. sec.gov 직접 열람은 샌드박스에서 불가.
- 공식 근거 기준일 2026-11-06(12일 경과).
- 샌드박스 초기 `pip install -e .`가 시스템 pip로 가서 pydantic 누락 → `python -m pip` 사용(실행에 영향 없음).
