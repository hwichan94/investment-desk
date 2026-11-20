# 애널리스트 루틴 보고서 (2026-11-20 22:20 KST)

**포트폴리오 점수 70.2 / 100 (목표 실행 시 83.8)** — `desk recommend` 출력값. 직전 보고서(70.2 / 83.8) 대비 변화 없음. 가장 큰 감점 요인: 현금 여력, 목표 정렬, 상위 2종목 집중.

## 1. 분석한 글 / 아이디어
- 232464 (세상학개론, IREN 종합점검 AI 정리본): relevance LOW. IREN(미보유·미추적) 가설 재확인. FACT: 무디스 NVDA 전망 긍정→안정(Aa1 유지) CONFIRMED(복수 매체, Moody's 원문 미확인), 앤트로픽 $1.5T PARTIAL, IREN ATM $6B UNVERIFIED.
- 232467 (T3chfeed, 앤트로픽 점검): LOW. 첫날 시가 $111.50/종가 $92.60 UNVERIFIED(상장 후 체결 보도 못 찾음), 조달 $81.3B PARTIAL(공모가 $83 기준 최소 $68B 보도).
- 232483 (세상학개론, 2018년 평행이론): LOW. 앤트로픽 종가 $97은 232467의 $92.60과 불일치 → CONFLICT 표기. 헌터브룩 AMD 숏리포트 UNVERIFIED.
- 232505 (세상학개론, IREN 3개월 정리): LOW. CDS·금리·JPM 상향 모두 UNVERIFIED(공개 근거 없음).
- 투자 아이디어 수신함 대기 없음.

## 2. 판단 변경 여부
변경 없음. `decision_universe.json`, `portfolio.json` 미수정(지문 64ba3c306f2d4e4c, GitHub main과 일치). 4건 모두 IREN·앤트로픽·시황 서술로 보유 종목 thesis에 공식 근거가 없고, IREN은 CRWV와 AI CAPEX 테마가 겹쳐 target 0% 유지. 시장 약세는 신규 Starter·Tactical 크기 축소 신호일 뿐 Core 자동 축소 사유가 아님. trader-decision-journal 추가 사유 없음.

## 3. 지금 실행할 액션 상위 3개
`reports/decision-latest.md` 그대로(제안일 뿐): TSLA 축소(목표 24%) → PLTR 추가매수(33%) → VRT 추가매수(7%). 증액은 TSLA 축소 재원이 전제이며 RISK_OFF 국면에서는 VRT 증액을 분할로 늦추는 편이 합리적.

## 4. 데이터 상태
- 공식 근거 기준일 2026-11-06(14일 경과). Fanding 수집 OK.
- 미반영 공시: NVDA 8-K(11-17), AXON 8-K(11-18), CRWV 10-Q. sec.gov 원문 직접 열람 불가라 `official_research.json` 미갱신.
- 실행 환경: `python`(3.11)에 pydantic이 없어 `python3.13` 사용.
