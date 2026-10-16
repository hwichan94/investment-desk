"""Fanding session state (cookies/localStorage) handling.

No ID or password is ever stored. The user logs in by hand in a real browser; only the
resulting session state is kept:
- plaintext in .secrets/ on the user's PC (git-ignored)
- AES-GCM encrypted in data/secure/ (committed) so GitHub Actions can use and refresh it
  with the FANDING_STATE_KEY repository secret.
"""
from __future__ import annotations

import base64
import json
import os
import secrets
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from desk import paths
from desk.errors import SessionUnavailable

KEY_ENV = "FANDING_STATE_KEY"
FANDING_DOMAIN = "fanding.kr"


def generate_key() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")


def _key_bytes(key: str) -> bytes:
    raw = base64.urlsafe_b64decode(key.strip().encode("ascii"))
    if len(raw) != 32:
        raise SessionUnavailable("FANDING_STATE_KEY must be a 32-byte urlsafe base64 key")
    return raw


def encrypt(state: dict[str, Any], key: str) -> bytes:
    nonce = secrets.token_bytes(12)
    data = json.dumps(state, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return base64.b64encode(nonce + AESGCM(_key_bytes(key)).encrypt(nonce, data, None))


def decrypt(blob: bytes, key: str) -> dict[str, Any]:
    raw = base64.b64decode(blob)
    try:
        data = AESGCM(_key_bytes(key)).decrypt(raw[:12], raw[12:], None)
    except Exception as exc:  # wrong key or tampered file
        raise SessionUnavailable("Could not decrypt the Fanding session state") from exc
    return json.loads(data)


def only_fanding(state: dict[str, Any]) -> dict[str, Any]:
    """Drop cookies/storage from unrelated sites before persisting anywhere."""
    return {
        "cookies": [c for c in state.get("cookies", []) if FANDING_DOMAIN in c.get("domain", "")],
        "origins": [o for o in state.get("origins", []) if FANDING_DOMAIN in o.get("origin", "")],
    }


def resolve_key() -> str | None:
    if os.environ.get(KEY_ENV):
        return os.environ[KEY_ENV]
    if paths.STATE_KEY_FILE.exists():
        return paths.STATE_KEY_FILE.read_text(encoding="ascii").strip()
    return None


def ensure_local_key() -> str:
    key = resolve_key()
    if key:
        return key
    paths.SECRETS.mkdir(parents=True, exist_ok=True)
    key = generate_key()
    paths.STATE_KEY_FILE.write_text(key, encoding="ascii")
    return key


def load_state() -> dict[str, Any]:
    """Prefer the local plaintext state; otherwise decrypt the committed one."""
    if paths.STATE_PLAIN.exists():
        return json.loads(paths.STATE_PLAIN.read_text(encoding="utf-8"))
    if not paths.STATE_ENCRYPTED.exists():
        raise SessionUnavailable("No Fanding session yet. Run `python -m desk login` on the PC.")
    key = resolve_key()
    if not key:
        raise SessionUnavailable(f"{KEY_ENV} is not set; cannot decrypt the Fanding session.")
    return decrypt(paths.STATE_ENCRYPTED.read_bytes(), key)


def save_state(state: dict[str, Any], key: str | None = None) -> bool:
    """Persist state. Returns True when the encrypted file actually changed."""
    state = only_fanding(state)
    if paths.STATE_PLAIN.exists() or paths.SECRETS.exists():
        paths.SECRETS.mkdir(parents=True, exist_ok=True)
        paths.STATE_PLAIN.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    key = key or resolve_key()
    if not key:
        return False
    if paths.STATE_ENCRYPTED.exists():
        try:
            if decrypt(paths.STATE_ENCRYPTED.read_bytes(), key) == state:
                return False  # avoid a new commit every run when nothing rotated
        except SessionUnavailable:
            pass
    _write_bytes(paths.STATE_ENCRYPTED, encrypt(state, key))
    return True


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data + b"\n")
