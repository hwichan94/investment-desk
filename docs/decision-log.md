# 판단 변경 이력

목표 비중·점수·편입 여부가 바뀔 때마다 위에 새 항목을 추가한다.

## 2026-10-27 — 시장행동·Regime 자동 레이어 추가

- 종목별 목표 비중과 Fundamental 점수는 변경하지 않음.
- Yahoo 일봉에서 가격 추세·QQQ/섹터 상대강도·거래량을 계산해 기존 `UNKNOWN` Relative Momentum을
  런타임에 보완하도록 추가. 원본 decision universe를 자동으로 덮어쓰지 않음.
- Estimate Revisions가 `UNKNOWN`이어도 Fundamentals 강화 + Relative Momentum STRONG + 50/200일선 상단 +
  QQQ 상대강도 상승이면 Winner Protection을 켜도록 확장. RSI 과매수는 약세·매도 조건에서 제외.
- Regime은 Starter/Tactical/타이밍만 조절하며 Core 자동매도에는 사용하지 않음.

## 2026-10-27 — Trader Engine 규칙 반영

- 종목별 목표 비중과 점수는 변경하지 않음.
- 기존 PLTR 실행 원칙의 30~35% 핵심 보유 밴드를 구조화해 목표 33%를 Core floor 30% + Tactical 3%로 구분.
- Estimate Revisions·Expectations Gap·Relative Momentum·Regime·Asymmetry는 확인된 신규 근거가 없어
  기존 종목 모두 기본값 `UNKNOWN` 유지. Winner Protection을 임의로 활성화하지 않음.
- 현금 $119.756243의 성격과 금액은 바꾸지 않고 `cash_available_for_investing`으로 키만 이관했으며,
  `cash_reserved_for_debt`는 확인된 예약액이 없어 0으로 시작.

## 2026-10-16 — 초기 이관

- Codex 환경(`투자 포트폴리오 by fanding`)의 `decision_universe.json`(as_of 2026-10-15)을 그대로 이관.
- 목표: PLTR 33, TSLA 24, AVGO 14, VRT 7, CCJ 6, NVDA 5, AMZN 4, INTC 2, FLNC 0, 현금 5 (%).
- 사용자 확인: 2026-10-16 기준 추천 이후 실제 매매 없음 → `portfolio.json` 수량 유지.
- 아직 Claude가 재검토하지 않음. 첫 분석 루틴에서 21개 글 재분석 후 검토 예정.
