# 애널리스트 루틴 보고서 (2026-10-30 10:10 KST)

**포트폴리오 점수 72.1 / 100 (목표 실행 시 83.8)** — `desk recommend` 출력값. 직전 보고서(72.4 / 83.8) 대비 현재 −0.3, 목표 실행 시 변화 없음. 가장 큰 감점 요인은 목표 정렬(62.9)과 현금 여력(13.8, 투자 가능 현금 0.7%)이다. 점수 하락은 가격 변동과 보유 수량 확정 반영에 따른 것이며 이번 분석 결과가 목표 비중을 바꾼 것이 아니다.

## 1. 분석한 글 / 아이디어
- 새 글 4개 처리, 투자 아이디어 수신함은 비어 있음.
  - 227440 (세상학개론, FOMC·GOOG/MSFT 실적, MEDIUM): GOOG는 Cloud가 +103%로 호조였으나 서비스 부문이 기대에 못 미쳤다. 오라클 투자자의 날은 CAPEX 정점 이후 FCF 전환 일정을 제시했다.
  - 227172 (T3chfeed, AI 사이클 장기 수요, MEDIUM): BofA 전력 용량 추정과 코닝·버티브·블룸에너지의 "2028년" 발언을 근거로 2030년까지의 수요를 주장한다. 핵심 수치는 2차 인용이다.
  - 227218 (AI 인프라 가설 복기, LOW), 227447 (라이브 공지, NONE).
- 공식 근거 검증:
  - GOOG 3Q 10-Q 원문(https://www.sec.gov/Archives/edgar/data/1652044/000165204426000084/goog-20260930.htm): 매출 $127,577M, Cloud $30,709M(전년 $15,157M), Google Services $96,302M, 분기 CAPEX $51.4B 확인. 9개월 영업현금흐름 $127.1B와 CAPEX $132.0B로 9개월 FCF는 약 −$4.8B(본 보고서 산출).
  - 227440이 적은 GOOG EPS 컨센서스 $2.87은 10-Q상 전년 동기 EPS와 같아 오기로 판단했다. 실제 3Q 희석 EPS는 $2.12다.
  - ORCL 투자자의 날 8-K Ex.99.1(https://www.sec.gov/Archives/edgar/data/1341439/000119312526435853/d75538dex991.htm): FY26~30 연평균 35%+, 추가 조달 $20B 상한, FY29 FCF 최소 $30B 확인. CAPEX 정점은 글의 FY28이 아니라 FY27~28이다.
  - 227361의 GOOG FCF 주장은 UNVERIFIED에서 PARTIAL로 보강했다.
- 미확인(UNVERIFIED): MSFT 분기 CAPEX $45.2B와 총매출 컨센서스, 마벨의 루멘텀 인수설(WebSearch에서 공식 발표를 찾지 못함), 버티브 800V 2028년 문구(VRT 10-Q에서 못 찾음), BofA·앤트로픽·코닝 내부 목표, FOMC 12월 인상 확률 87.2%. 사유는 sec.gov 외 공식 원문 접근 불가와 비공개 리포트 인용이다.

## 2. 판단 변경
- **변경 없음** (`decision_universe.json`, `official_research.json`, `portfolio.json` 미수정). ORCL의 자금조달 완화 신호는 공식 확인됐으나 경영진 전망 1건이라 점수를 바꾸지 않았다(thesis inertia). GOOG는 universe 밖이다. GLW·BE·LITE는 분석 JSON의 후보 언급일 뿐이며 편입 기준 5개를 채우지 못했다.
- AI CAPEX 상관집중과 RISK_OFF 기조는 그대로다. 투자 가능 현금 0.7%로 최소 5%에 못 미친다.
- `trader-decision-journal.md`: 갱신 필요 없음.

## 3. 지금 실행할 액션 (제안, 주문 아님; `decision-latest.md` 기준)
1. **TSLA 축소**: 현재 31.79% → 목표 24.00%, 2회 분할, 약 −$2,284 (−5.64주). 첫 축소는 실적 전 절반만.
2. **VRT 추가매수**: 3.39% → 7.00%, 2회 분할, 약 +$1,058 (+4.26주), 재원 현금·TSLA. 급등일 추격 금지.
3. **PLTR 추가매수**: 29.83% → 33.00%, 약 +$928 (+4.77주), Core 30% 하한·Tactical 3% 구조 유지. 신고가 추격은 피하고 다음 실적에서 재확인.
- 보조: 현금 5% 복원 필요(+$1,264), INTC·AMZN은 소폭 조정 검토(각 −$419, −$296).

## 4. 데이터 상태 / 이번 실행에서 고친 것
- Fanding 수집 OK, 분석 대기 0개. 공식 근거 기준일 2026-10-29(GOOG·MSFT·AMZN 실적은 일부만 반영).
- 테스트 정리: 기준 커밋부터 실패하던 pytest 3건을 고쳤다. 코드 회귀가 아니라 테스트 데이터가 최신 확정 보유와 맞지 않은 것이 원인이었다.
  - `test_confirmed_portfolio_snapshot_is_synced`: 기대 보유를 확정값으로 갱신(AVGO 12, NVDA 8, AMZN 6, 현금 $201.50, 기준일 2026-10-29, NVDA·AMZN 평단 포함).
  - `test_report_renders`: 현금 기대값 $3,816.44를 $201.50으로 갱신.
  - `test_winner_protection_does_not_block_a_small_add`: 가격 픽스처에 보유 종목 AMZN이 빠져 PLTR 비중이 틀어졌고 변화가 1%p 미만 규칙으로 유지가 됐다. AMZN 가격을 추가했고 검증 조건(winner_protection_blocked False, amount > 0)은 그대로다.
- `pytest` 전체 통과, `python -m desk validate` OK.
