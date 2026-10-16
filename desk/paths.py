from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(os.environ.get("DESK_ROOT", Path(__file__).resolve().parent.parent))
CONFIG = ROOT / "config"
DATA = ROOT / "data"
POSTS = DATA / "posts"
ANALYSES = DATA / "analyses"
STATUS = DATA / "status"
MARKET = DATA / "market"
SECURE = DATA / "secure"
REPORTS = ROOT / "reports"
SECRETS = ROOT / ".secrets"

# Plaintext session + key stay on the user's PC only (.gitignore'd).
STATE_PLAIN = SECRETS / "fanding_state.json"
STATE_KEY_FILE = SECRETS / "fanding_state.key"
# Encrypted session is committed so GitHub Actions can use and refresh it.
STATE_ENCRYPTED = SECURE / "fanding_state.enc"

FEED_URL = os.environ.get("FANDING_FEED_URL", "https://fanding.kr/feeds")
KST = ZoneInfo("Asia/Seoul")


def now_kst() -> datetime:
    return datetime.now(KST)
