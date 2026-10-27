# Trader Decision Journal

과거 판단이 합리적 대안보다 부진했을 때 결과를 기록하고 재발 방지 규칙을 남긴다. 단순한 단기 가격 변동은
오답으로 보지 않으며, 당시 이용 가능했던 정보와 12개월 목적함수를 기준으로 평가한다.

## 2026-10-27 — PLTR 승자 축소 회고

- **당시 판단:** 높은 밸류에이션과 포트폴리오 집중도를 이유로 보유량의 약 1/3 축소를 제안했다.
- **결과:** 이후 상승 구간의 일부에 참여하지 못해, 유지 대안보다 성과가 부진했다.
- **과대평가:** valuation, concentration risk.
- **과소평가:** 성장 가속, estimate revisions, relative momentum, 시장의 기대 재평가(Expectations Gap).
- **원인:** 불확실성을 포지션 구조보다 축소로 처리했고, 강한 승자에서 가격 부담을 펀더멘털·추정치·상대
  모멘텀보다 우선했다.
- **룰 변경:**
  1. Fundamentals + Estimate Revisions + Relative Momentum이 모두 개선 중이면 Winner Protection 적용.
  2. 밸류에이션·이벤트 위험 축소는 Tactical sleeve부터 하고 Core floor는 보존.
  3. Expectations Gap과 Regime/Narrative를 별도 렌즈로 점검.
  4. 보호된 승자 축소에는 구체적인 `winner_protection_override_reason` 필수.
- **향후 검증:** 다음 분기마다 성장·마진·계약 전환과 추정치 방향을 함께 확인한다. 데이터가 없으면
  `UNKNOWN`으로 두며 보호 조건을 임의로 충족시키지 않는다.
