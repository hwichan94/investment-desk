# 개인 AI 투자 리서치 데스크

Fanding 새 글을 3시간마다 수집하고, Claude가 공식 자료로 검증해 보유·후보 종목의 목표 비중과
자금 이동을 제안한다. **주문 기능은 없다.** 프로젝트 규칙은 [CLAUDE.md](CLAUDE.md).

## PC 설치 (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m playwright install chromium
python -m pytest
```

## 최초 연결 (한 번만)

1. `python -m desk login` → 열린 브라우저에서 직접 로그인.
   - `.secrets/fanding_state.key` (키, git 제외)와 `data/secure/fanding_state.enc` (암호화 세션)가 생긴다.
2. GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret
   - `FANDING_STATE_KEY`: `.secrets/fanding_state.key` 파일 내용
   - `SEC_USER_AGENT`: `PersonalInvestmentDesk/1.0 본인이메일` (SEC 요구사항)
3. `git push` 후 Actions 탭에서 `collect`를 한 번 수동 실행(Run workflow)해 확인.

## 로그인이 만료됐을 때

GitHub에서 `collect` 실패 메일이 오고 보고서 상단에 `AUTH_REQUIRED`가 뜬다. PC에서:

```powershell
git pull
python -m desk login
git add data/secure/fanding_state.enc
git commit -m "session: refresh Fanding login"
git push
```

## 결과 보기

- `reports/decision-latest.md`: 최신 가격 기준 현재→목표 액션플랜 (3시간마다)
- `reports/analyst-latest.md`: Claude 분석 루틴의 해석과 판단 변경
- `docs/decision-log.md`: 목표 비중 변경 이력
