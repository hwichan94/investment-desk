# 애널리스트 루틴 보고서 (2026-11-20 10:20 KST)

**포트폴리오 점수 70.2 / 100 (목표 실행 시 83.8)** — `desk recommend` 출력값. 직전 보고서(70.2 / 83.8) 대비 변화 없음. 가장 큰 감점 요인: 현금 여력, 목표 정렬, 상위 2종목 집중.

## 1. 분석한 글 / 아이디어
- 새 글 없음(대기 0건), 투자 아이디어 수신함 대기 없음.
- 기존 분석 232159의 NVDA 관련 FACT 주장을 보강했다.
  - 젠슨황 CEO 사임·콜레트 크레스 임시 CEO 선임: **PARTIAL**. NVDA 8-K(공시일 11-12, 이벤트일 11-11)가 사임, 크레스 임시 CEO, 하비 존스 초대 이사회 의장을 보고한다. 근거 [8-K 원문](https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000082/nvidiaannouncesceotransiti.htm)은 샌드박스에서 직접 열지 못하고 WebSearch 요약으로만 확인했다. 직원 25% 청원은 여전히 미확인이고, 사임 사유는 회사 공시에 없다.
  - 무디스 전망 하향: 여전히 UNVERIFIED.

## 2. 판단 변경 여부
변경 없음. `decision_universe.json`과 `portfolio.json`은 수정하지 않았다(지문 64ba3c306f2d4e4c, GitHub main과 일치).
- NVDA 3분기 FY27 실적(11-17)은 WebSearch로 확인했다([NVDA IR](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Third-Quarter-Fiscal-2027/default.aspx), 공시 [8-K](https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000088/q3fy27pr.htm)). 다만 수치는 IR·2차 보도의 검색 요약이고 원문은 직접 읽지 못했다.
  - 매출 $115.8B(+103% YoY), 데이터센터 $107.6B(+110%), GAAP 총마진 74.8%.
  - 4분기 가이던스: 매출 $130B ±3%(1주 추가 포함), 총마진 71~72%, 중국 데이터센터 컴퓨트 제외.
  - 펀더멘털은 강하지만 총마진 가이던스가 하락하고, CEO 공백이라는 키맨 리스크가 새로 생겼다.
- 단일 이벤트와 원문 미열람 상태라 점수·목표 비중(NVDA 5%)은 thesis inertia에 따라 바꾸지 않는다. 다만 NVDA 신규·추가 집행은 후임 CEO 선임 경과와 4분기 총마진을 보며 판단하는 것이 합리적이다.
- `official_research.json`은 원문 미열람이라 갱신하지 않았다(as_of 2026-11-06 유지). trader-decision-journal 추가 사유 없음.

## 3. 지금 실행할 액션 상위 3개
`reports/decision-latest.md` 그대로(제안일 뿐): TSLA 축소(목표 24%) → PLTR 추가매수(33%) → VRT 추가매수(7%). 증액은 TSLA 축소 재원이 전제다. 투자 가능 현금 0.8%로 5% 최소선에 못 미친다.

## 4. 데이터 상태
- 공식 근거 기준일 2026-11-06(14일 경과). Fanding 수집 OK.
- 환경: `sec.gov`, `investor.nvidia.com`에 직접 접속할 수 없다(네트워크 허용 목록 밖). 허용되면 NVDA 11-17 실적 원문을 읽어 `official_research.json`을 갱신할 수 있다.
- 미확인으로 남은 공시: NVDA 8-K(11-17 실적), AXON 8-K(11-18), CRWV 10-Q. 모두 `data/market/docs/`에 원문이 아직 없다.
- 실행 메모: `python`이 3.11이라 `pip install -e .`의 패키지(3.13)를 못 찾는다. 이번 실행은 `python3.13`을 썼다.
