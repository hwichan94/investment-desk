# 개인 AI 투자 리서치 데스크 — Claude 인수인계

작성일: 2026-10-16 (Asia/Seoul)

작업 경로:

`C:\Users\USER\Documents\투자 포트폴리오 by fanding`

## 1. 프로젝트의 궁극적인 목적

이 프로젝트는 Fanding 투자 콘텐츠 요약기가 아니다.

최종 목적은 다음과 같다.

1. 사용자가 정상적으로 접근 가능한 Fanding 새 글을 감지한다.
2. 글의 주장, 의견, 예측을 구조화하고 데이터베이스에 축적한다.
3. 회사 IR, SEC, 정부 자료 등으로 독립 검증한다.
4. 기존 보유 종목과 신규 후보를 동일한 기준으로 비교한다.
5. 매번 `유지 / 추가매수 / 축소 / 매도 / 신규 편입`과 목표 비중을 제안한다.
6. 어떤 기존 종목에서 자금을 가져올지도 명시한다.
7. 실제 증권 주문은 절대 실행하지 않는다.

사용자는 단순히 보수적인 조언을 원하지 않는다. 펀더멘털이 유지·강화되고 12개월 안에 성과가 가시화될 가능성이 높으면 과감하게 초기 진입하고, 실적 확인 후 비중을 확대하는 방식을 선호한다.

핵심 문장:

> 증거가 나오기 전에 작게 진입하고, 증거가 나올 때 늘리며, 12개월 안에 증거가 없으면 기회비용을 고려해 회수한다.

## 2. 사용자 투자 성향

- 기본 의사결정 기간은 향후 12개월, 즉 4개 분기다.
- 보유기간 12개월이 끝났다고 기계적으로 매도하지 않는다.
- 펀더멘털과 기대수익이 유지되면 새로운 12개월 투자 논리를 작성한다.
- 단순 주가 하락은 매도 사유가 아니다.
- 신고가도 단독 매도 사유가 아니다.
- 펀더멘털 훼손, 촉매 지연, 더 나은 기회의 발견은 축소·매도 사유다.
- 기존 종목보다 매력적이지 않은 신규 종목은 편입하지 않는다.
- 신규 후보를 적극적으로 발굴하되 포트폴리오를 불필요하게 늘리지 않는다.
- AI가 판단을 회피하지 말고 구체적인 목표 비중과 자금 이동안을 제시해야 한다.
- 결론과 불확실성을 함께 보여줘야 한다.

세부 정책은 `config/investment_policy.md`에 있다.

## 3. 매우 중요한 안전 원칙

- 증권사 API와 주문 기능은 없다. 앞으로도 자동 주문을 연결하지 않는다.
- 모든 BUY/SELL/ADD/REDUCE는 추천일 뿐이다.
- 사용자의 Fanding 계정 ID나 비밀번호를 코드, 설정, 로그, 문서에 저장하지 않는다.
- 로그인은 사용자가 열린 브라우저에서 직접 수행한다.
- paywall, 로그인, 인증 우회 금지.
- 사용자가 접근 권한을 가진 게시물만 수집한다.
- 숫자를 임의 생성하지 않는다. 데이터가 없으면 `UNKNOWN` 또는 불충분 상태로 둔다.
- 사용자가 실제 매매를 실행했는지 확인하기 전에는 `config/portfolio.json`의 수량을 임의 변경하지 않는다.

## 4. 현재 구현 상태 요약

현재 구현된 것은 Phase 1~3의 일부다.

### 구현 완료

- Fanding persistent browser 로그인 프로필
- Fanding feed polling과 새 글·수정 글 감지
- 접근권한 밖 글 건너뛰기
- post ID와 content hash 기반 중복·수정 감지
- SQLite 저장
- FACT / OPINION / PREDICTION 휴리스틱 분류
- 티커와 산업·촉매·위험 기초 추출
- 공식 IR/SEC 근거 레지스트리
- Bull / Bear / invalidation signal 보고서
- 작성자 기초 통계
- Yahoo 공개 chart 가격 조회
- SEC ticker-CIK, 공시, 핵심 XBRL 지표 조회
- 데이터 신선도 경고
- 현재 비중 계산
- 보유·후보 종목 상대 점수
- 목표 비중 검증
- 유지·추가·축소·전량정리·신규편입 액션플랜
- 신규 편입 재원과 기회비용 설명
- Markdown 보고서
- watcher 새 글 발견 시 액션플랜 재생성 callback
- 테스트 29개

### 아직 미완성 또는 수동

- LLM 기반 본문 의미 분석은 없다. 현재 `thesis_extractor.py`는 휴리스틱이다.
- `config/decision_universe.json`의 정성 점수와 목표 비중은 Codex가 외부 근거를 검토해 수동 갱신했다.
- 새 Fanding 글이 들어와도 점수가 자동으로 바뀌지는 않는다.
- watcher callback은 최신 가격으로 액션플랜을 재생성하지만, 신규 주장을 해석해 점수와 목표를 자동 수정하지 않는다.
- 완전한 valuation engine, DCF, forward estimate 수집은 없다.
- 공식자료 레지스트리는 자동 갱신되지 않는다.
- 알림, 대시보드, 예측 적중률, 세금·실거래비용 계산은 없다.
- Windows 백그라운드 watcher의 지속 실행이 안정적이지 않다.

## 5. 현재 실제 상태

### 데이터

- SQLite: `data/investment_ai.db`
- 저장된 Fanding 글: 21개
- 최신 전체 리서치: 21개 글, 705개 문장 검토
- 최신 테스트: `29 passed`
- Git 저장소가 아니다. `git status`는 실패한다.

### watcher 상태

2026-10-16 확인 시 `python main.py watch` 프로세스는 실행 중이 아니었다.

10월 15일에는 watcher를 백그라운드로 실행했으나 이후 종료됐다. 로그에는 한 차례 `AuthenticationRequiredError`가 있었고 이후 세션이 다시 동작해 신규 글 1개를 추가 저장한 기록도 있다. 일부 게시물에서는 반복적으로 `BrowserSessionError`가 발생했다.

최신 로그:

`logs/investment_ai.log`

watcher를 재개하려면 먼저 다음 순서로 확인한다.

```powershell
python main.py login
python main.py check
python main.py watch
```

`login`은 브라우저에서 사용자가 직접 로그인해야 한다. 비밀번호를 요청하거나 저장하지 말 것.

장기적으로는 숨김 콘솔 프로세스보다 Windows 작업 스케줄러, 서비스 또는 Codex automation처럼 복구 가능한 실행 방식을 검토할 것. 단, 사용자의 승인 없이 시스템 시작 작업이나 외부 알림을 설치하지 말 것.

## 6. 최신 포트폴리오 원본

Source of truth는 `config/portfolio.json`이다. 마지막으로 사용자가 제공한 수량을 기반으로 하며, 추천 이후 사용자가 실제 거래했는지는 아직 확인되지 않았다.

| 종목 | 수량 | 평균단가(USD) |
|---|---:|---:|
| TSLA | 23 | 419.799565 |
| PLTR | 45 | 160.890222 |
| AVGO | 9 | 391.185556 |
| CCJ | 21 | 96.7914 |
| INTC | 11 | 137.33 |
| VRT | 4 | 290.98 |
| FLNC | 120 | 15.30 |
| 현금 | - | 119.756243 |

주의:

- 사용자가 실제 거래를 했다면 먼저 새로운 스크린샷이나 수량을 받아 `portfolio.json`을 갱신한다.
- 추천 내용을 실제 보유 수량으로 착각하지 않는다.

## 7. 최신 액션플랜

최신 생성 시각: 2026-10-16 19:57 KST

최신 가격 기준 평가액: 약 `$25,004.85`

| 종목 | 현재 비중 | 목표 비중 | 현재 판단 |
|---|---:|---:|---|
| PLTR | 36.08% | 33% | 핵심 보유 밴드 30~35%, 현재는 일부 축소 |
| TSLA | 33.34% | 24% | 2회 분할 축소 |
| AVGO | 12.39% | 14% | 조정 시 보충 |
| CCJ | 6.99% | 6% | 유지 |
| INTC | 4.20% | 2% | 관찰 포지션만 유지 |
| VRT | 3.44% | 7% | 분할 추가매수 |
| FLNC | 3.09% | 0% | 전량 정리 |
| NVDA | 0% | 5% | 신규 편입 |
| AMZN | 0% | 4% | 신규 편입 |
| 현금 | 0.48% | 5% | 대기자금 확보 |

최신 참고 수량:

- TSLA 최종 약 6.44주 축소
- PLTR 최종 약 3.84주 축소. 단, 우선 1~2주만 줄여 35% 이내로 복귀하는 방식도 가능
- FLNC 120주 전량 정리
- NVDA 약 5.76주 신규 편입, 절반 우선
- AMZN 약 3.93주 신규 편입, 절반 우선
- VRT 약 4.15주 추가, 절반 우선

이 수량은 가격 변동에 따라 바뀌는 참고치다. 실제 주문이 아니다.

최신 보고서:

- `data/reports/research-phase2-2026-10-16-195726.md`
- `data/reports/portfolio-decision-2026-10-16-195739.md`

## 8. 현재 후보 종목 판단

`config/decision_universe.json`에 보유 종목과 후보가 함께 있다.

추가 자본 매력도 상위권:

1. NVDA
2. AVGO
3. AMZN
4. VRT

관찰:

- ETN: 전력 인프라 사업은 좋지만 VRT와 역할 중복 및 가격 부담
- ORCL: OCI/RPO 성장은 강하지만 CAPEX, 음의 FCF, 자금조달 부담
- AXON: 매출 35%, ARR 39%, NRR 126%로 사업의 질은 강함. 그러나 높은 밸류에이션 때문에 현재 목표 0%

제외에 가까운 관찰:

- CRWV: AI 수요보다 대규모 부채와 자금조달 위험이 우선
- FLNC: 수주잔고에도 생산 차질, 가이던스 재하향, 낮은 총마진 때문에 목표 0%

후보를 추가할 때 반드시 다음을 문서화한다.

1. 기존 어느 보유 종목보다 나은가?
2. 12개월 안에 확인할 KPI와 촉매는 무엇인가?
3. 생각을 바꿀 조건은 무엇인가?
4. 편입 재원은 어느 종목에서 가져오는가?
5. 현재 가격에서 기대수익이 충분한가?

## 9. 최신 Fanding 내용에서 나온 새 신호

최근 추가된 주요 글:

- `224130`: 코어위브 신용·부채 위험
- `224055`: AI 버블 논쟁과 NVDA 비교
- `223927`: 실적은 좋지만 시장 기대와 반도체 경쟁 우려
- `223860`: AI 투자 자본 병목과 AVGO 관련 논쟁
- `223348`: AXON의 공공안전 설치 기반과 AI·소프트웨어 확장
- `223701`: 유가 상승, 시장 breadth 악화, 빅테크 실적 의존
- `223387`: 9월 투자전공반 회고

현재 해석:

- AI 최종 수요가 붕괴했다는 근거는 아직 없다.
- 다만 AI 투자의 제약이 반도체·전력뿐 아니라 자본조달과 신용으로 이동하고 있다.
- 레버리지가 높은 네오클라우드는 피한다.
- NVDA, AVGO, VRT도 고객의 자금조달과 hyperscaler CAPEX를 위험 변수로 추가했다.
- 현금 5% 목표는 유지한다.
- AXON은 좋은 신규 아이디어지만 가격 때문에 편입하지 않았다.

## 10. 주요 파일 지도

### 진입점

- `main.py`: CLI, research/recommend/watch orchestration

### Fanding

- `app/watcher/browser_session.py`: Playwright persistent browser 세션
- `app/watcher/fanding_watcher.py`: polling, retry, 신규·수정 감지, callback
- `app/ingestion/parser.py`: 실제 DOM 파싱
- `app/ingestion/cleaner.py`: 본문 정리
- `config/fanding_selectors.json`: Fanding DOM 선택자

### 연구

- `app/research/thesis_extractor.py`: 현재 휴리스틱 분석
- `app/research/phase2_engine.py`: 공식 근거, Bull/Bear, Thesis, 작성자 통계
- `app/research/models.py`: Phase 2 모델
- `config/official_research.json`: 보유 7종목 공식 자료 스냅샷
- `config/sources.json`: 출처 신뢰도 설정

### 시장 데이터

- `app/market_data/providers.py`: Yahoo chart, SEC EDGAR
- `app/market_data/updater.py`: 가격·공시·XBRL 갱신과 freshness
- `app/market_data/models.py`: 시장 데이터 모델

### 포트폴리오

- `app/portfolio/portfolio_engine.py`: 현재 비중과 제약 검증
- `app/portfolio/rebalance_engine.py`: current→target 차이와 액션
- `app/portfolio/decision_engine.py`: 보유·후보 점수, 최신 가격 비중, 기회비용
- `config/portfolio.json`: 실제 보유 수량 source of truth
- `config/portfolio_constraints.json`: 현금·단일종목·변화 임계값
- `config/decision_universe.json`: 현재 점수·목표 비중·이유·위험·공식 링크
- `config/watchlist.json`: 후보 universe

### 저장·보고서

- `app/database/repository.py`: SQLite 저장소
- `app/reports/report_generator.py`: Markdown 보고서 생성
- `data/investment_ai.db`: 실제 데이터베이스
- `data/reports/`: 생성된 보고서
- `logs/investment_ai.log`: watcher와 오류 로그

### 테스트

- `tests/test_watcher.py`
- `tests/test_parser.py`
- `tests/test_analysis.py`
- `tests/test_phase2_research.py`
- `tests/test_market_data.py`
- `tests/test_decision_engine.py`
- 나머지 repository/portfolio/rebalance 테스트

## 11. 실행 명령

프로젝트 루트에서 실행한다.

```powershell
python -m pytest
python main.py setup
python main.py login
python main.py check
python main.py watch
python main.py portfolio
python main.py report
python main.py update-data
python main.py research
python main.py recommend
python main.py analyze <FANDING_URL>
```

명령 의미:

- `login`: 직접 로그인 후 persistent profile 저장
- `check`: Fanding 1회 확인. 새 글이 있으면 기본 분석 및 액션플랜 생성
- `watch`: 기본 5분 polling. 새 글이 있으면 액션플랜 재생성 callback 실행
- `research`: 저장된 전체 글을 Phase 2 방식으로 분석하고 액션플랜도 생성
- `recommend`: 최신 가격으로 보유·후보 비교와 액션플랜만 생성
- `update-data`: 보유 종목 가격·SEC 자료 보고서

## 12. 데이터와 판단의 중요한 차이

다음 두 종류를 혼동하지 말 것.

### 동적으로 갱신되는 것

- Fanding 저장 글
- 최신 시장가격
- SEC 공시 목록과 일부 XBRL 지표
- 현재 비중
- current→target 차이와 참고 수량

### 현재 수동 검토가 필요한 것

- 회사별 투자 점수
- 목표 비중
- 신규 후보 편입 여부
- 정성적 thesis 상태
- 신규 Fanding 주장이 포트폴리오 점수에 주는 영향
- `official_research.json`의 최신 공식 근거

따라서 보고서가 자동 생성됐다는 이유만으로 최신 Fanding 내용이 목표 비중에 완전히 반영됐다고 말하면 안 된다.

## 13. 알려진 기술적 문제

### P0 — watcher 지속성

- 백그라운드 Python 프로세스가 장기간 유지되지 않았다.
- 로그인 만료와 `AuthenticationRequiredError`를 정상 상태로 감지하고 알림해야 한다.
- 반복적인 `BrowserSessionError`가 있다.
- 브라우저 프로필 lock, page timeout, DOM 변경, 로그인 만료를 구분해야 한다.

### P0 — 실제 포트폴리오 동기화

- 사용자가 추천을 실제로 실행했는지 모른다.
- 다음 판단 전에 현재 수량과 현금을 다시 받아야 한다.
- broker 계좌 자동 연결은 하지 않는다.

### P1 — 의사결정 자동화의 연결 고리

- Fanding 분석 결과가 `decision_universe.json` 점수로 자동 연결되지 않는다.
- 새 정보가 thesis 강화/약화, catalyst, invalidation에 미친 영향을 구조화해야 한다.
- 자동 변경은 급격하지 않도록 thesis inertia와 근거 신뢰도를 적용해야 한다.

### P1 — 공식 근거 최신화

- 최신 Phase 2 보고서의 공식자료 기준일은 여전히 2026-10-06이다.
- 보고서 생성일과 공식자료 기준일을 구분해야 한다.
- 신규 실적이 나오면 회사별 공식 IR과 SEC 근거를 갱신해야 한다.

### P1 — valuation

- 현재 valuation 점수는 수동이다.
- trailing P/E만으로 판단하지 말고 회사 유형별 forward 지표와 시나리오를 구현해야 한다.
- SaaS: 성장, FCF, EV/Sales
- 반도체: forward EPS, cycle, FCF
- 인프라: EBITDA, FCF, backlog
- 원자재: 정상화 가격과 생산비

### P2 — 제품화

- 일일 보고서
- 사용자 알림
- dashboard
- 예측 적중률
- 작성자 장기 track record
- 세금·거래비용

## 14. Claude가 먼저 해야 할 일

권장 순서:

1. 이 문서와 `README.md`, `config/investment_policy.md`를 읽는다.
2. `python -m pytest`로 29개 테스트가 통과하는지 확인한다.
3. 사용자에게 추천 이후 실제로 거래한 종목·수량이 있는지 확인한다.
4. 실제 수량을 받기 전에는 `portfolio.json`을 수정하지 않는다.
5. Fanding 로그인을 사용자가 직접 다시 하게 한 뒤 `python main.py check`를 실행한다.
6. watcher가 왜 종료됐는지 진단하고 재시작·복구 정책을 만든다.
7. `official_research.json`의 기준일과 최신 실적을 확인한다.
8. 신규 Fanding 주장과 공식 근거를 비교해 `decision_universe.json` 점수를 검토한다.
9. 새 목표 비중과 자금 이동안을 보고서로 제시한다.
10. 모든 변경 후 테스트와 실제 CLI smoke test를 수행한다.

## 15. Claude에게 그대로 전달할 첫 요청

```text
첨부된 CLAUDE_HANDOFF.md를 먼저 끝까지 읽고 이 프로젝트를 인수인계 받아라.

프로젝트 목적은 Fanding 글 요약이 아니라, 새로운 투자 정보를 공식 외부 데이터로 검증하고 현재 포트폴리오 및 신규 후보와 비교해 매번 유지·추가매수·축소·매도·신규 편입과 목표 비중을 제안하는 것이다.

먼저 코드를 변경하지 말고 다음을 수행해라.
1. 현재 테스트와 watcher 상태 확인
2. 최신 DB 글 수와 최신 보고서 확인
3. 실제 보유 수량이 추천 이후 변경됐는지 사용자에게 확인할 항목 정리
4. 알려진 문제와 우선순위 재검토

그 다음 P0인 watcher 지속성, 로그인 만료 처리, 실제 포트폴리오 동기화부터 작업해라.

계정 비밀번호를 소스나 문서에 저장하지 말고, 실제 증권 주문 기능을 만들지 마라.
```

## 16. 완료 기준

다음 담당자가 잘 인수했다면 최소한 다음을 만족해야 한다.

- 현재 보유 수량과 추천 목표를 구분한다.
- Fanding watcher의 실행·실패 상태를 근거로 말한다.
- 새 글이 실제로 DB에 저장됐는지 확인한다.
- 공식 근거 기준일을 확인한다.
- 신규 종목을 기존 종목과 비교한다.
- 매수 재원을 명시한다.
- 12개월 KPI와 invalidation 조건을 제시한다.
- 사용자가 실행하기 전에는 주문이나 보유 수량을 바꾸지 않는다.
- 모든 코드 변경 후 테스트를 통과시킨다.

