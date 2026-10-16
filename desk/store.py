"""Git-friendly JSON storage: one file per post / analysis, plus small status files."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from desk import paths


class Post(BaseModel):
    post_id: str
    url: str
    title: str
    author: str
    published_raw: str | None = None
    published_at: datetime | None = None
    body: str
    content_hash: str
    first_seen_at: datetime
    updated_at: datetime
    revision: int = 1


UpsertResult = Literal["CREATED", "UPDATED", "UNCHANGED"]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


class PostStore:
    def __init__(self, posts_dir: Path | None = None, analyses_dir: Path | None = None):
        self.posts_dir = posts_dir or paths.POSTS
        self.analyses_dir = analyses_dir or paths.ANALYSES

    def _post_path(self, post_id: str) -> Path:
        return self.posts_dir / f"{post_id}.json"

    def get(self, post_id: str) -> Post | None:
        raw = read_json(self._post_path(post_id))
        return Post.model_validate(raw) if raw else None

    def known_ids(self) -> set[str]:
        return {p.stem for p in self.posts_dir.glob("*.json")}

    def upsert(self, post: Post) -> UpsertResult:
        existing = self.get(post.post_id)
        if existing is None:
            write_json(self._post_path(post.post_id), post.model_dump(mode="json"))
            return "CREATED"
        if existing.content_hash == post.content_hash:
            return "UNCHANGED"
        updated = post.model_copy(
            update={
                "first_seen_at": existing.first_seen_at,
                "published_at": existing.published_at or post.published_at,
                "revision": existing.revision + 1,
            }
        )
        write_json(self._post_path(post.post_id), updated.model_dump(mode="json"))
        return "UPDATED"

    def all(self) -> list[Post]:
        return sorted(
            (Post.model_validate(read_json(p)) for p in self.posts_dir.glob("*.json")),
            key=lambda post: post.post_id,
        )

    def pending_analysis(self) -> list[Post]:
        """Posts with no analysis yet, or whose content changed after it was analyzed."""
        pending = []
        for post in self.all():
            analysis = read_json(self.analyses_dir / f"{post.post_id}.json")
            if analysis is None or analysis.get("content_hash") != post.content_hash:
                pending.append(post)
        return pending
