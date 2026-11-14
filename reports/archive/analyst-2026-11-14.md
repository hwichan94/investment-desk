# 애널리스트 루틴 보고서 (2026-11-14 11:00 KST)

**포트폴리오 점수 70.9 / 100 (목표 실행 시 83.8)** — `desk recommend` 출력값. 직전 보고서(70.9 / 83.8) 대비 변화 없음. 주요 감점 요인: 현금 여력(5% 목표 미달), 목표 정렬, 상위 종목 집중.

## 1. 분석한 글 / 아이디어
- 230886 (T3chfeed 인사이더 테크리포트 Ep.48, relevance HIGH): NVDA 사임 이후 증권사 의견 정리. 작가는 GPU 수요 훼손이 없다고 보며 Wedbush(Buy)에 동의, 청문회(중국 수출 고의성)를 핵심 변수로 본다.
  - 검증: NVDA 실적 콜 11/17 14:00 PT(IR 공지) CONFIRMED. HIMS 3Q 해외 +321%·미국 약 +21%, 4Q 가이던스 CONFIRMED(웹 검색 요약, 미보유). TSLA 사이버캡은 10-Q로 PARTIAL(사이버트럭 축소·가격은 미확인). 증권사 노트·앤트로픽 상장 일정은 UNVERIFIED(공식 자료 없음).
  - 영향: NVDA·PLTR·TSLA NEUTRAL LOW, CRWV WEAKEN LOW.
- 신규 공시 VRT 8-K(11/13)는 sec.gov 접근 불가로 내용 UNKNOWN 유지(직전 보고서와 동일).
- 투자 아이디어 수신함 대기 없음.

## 2. 판단 변경 여부
변경 없음. 새 글은 단일 작가의 제3자 리포트 정리이며 새 공식 근거가 없다. `decision_universe.json`·`official_research.json` 미수정. trader-decision-journal 추가 사유 없음.

## 3. 지금 실행할 액션 상위 3개
`reports/decision-latest.md` 참조(제안일 뿐, 직전과 동일): TSLA 축소 → PLTR 추가매수 → VRT 추가매수. 재원·참고 수량은 해당 보고서.

## 4. 수집·데이터 상태 경고
- 공식 근거 기준일 2026-11-06(8일 전). VRT 11/13 8-K, CRWV 10-Q, NVDA 8-K 원문 미반영.
- **NVDA 실적 11/17 PT(11/18 KST 새벽)**: 결과 반영 후 NVDA 판단 재검토 필요.
- 투자 가능 현금 5% 미달.
- 샌드박스에서 pydantic·pytest가 기본 미설치라 수동 설치함(`pip install -e .`만으로는 부족).
