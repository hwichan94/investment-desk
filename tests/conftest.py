import shutil
from pathlib import Path

import pytest

from desk import paths

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture
def root(tmp_path, monkeypatch):
    """Isolated project root with a copy of the real config."""
    shutil.copytree(REPO / "config", tmp_path / "config")
    mapping = {
        "ROOT": tmp_path, "CONFIG": tmp_path / "config", "DATA": tmp_path / "data",
        "POSTS": tmp_path / "data/posts", "ANALYSES": tmp_path / "data/analyses",
        "STATUS": tmp_path / "data/status", "MARKET": tmp_path / "data/market",
        "SECURE": tmp_path / "data/secure", "REPORTS": tmp_path / "reports",
        "SECRETS": tmp_path / ".secrets",
        "STATE_PLAIN": tmp_path / ".secrets/fanding_state.json",
        "STATE_KEY_FILE": tmp_path / ".secrets/fanding_state.key",
        "STATE_ENCRYPTED": tmp_path / "data/secure/fanding_state.enc",
    }
    for name, value in mapping.items():
        monkeypatch.setattr(paths, name, value)
    for d in ("POSTS", "ANALYSES", "STATUS", "MARKET"):
        mapping[d].mkdir(parents=True)
    monkeypatch.delenv("FANDING_STATE_KEY", raising=False)
    return tmp_path
