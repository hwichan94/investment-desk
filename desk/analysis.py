"""Schema for post analyses written by the Claude analyst routine (data/analyses/<id>.json)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from desk import paths
from desk.store import PostStore, read_json


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["FACT", "OPINION", "PREDICTION"]
    text: str = Field(description="Short paraphrase of the claim, not a long quote")
    tickers: list[str] = Field(default_factory=list)
    verification: Literal["CONFIRMED", "PARTIAL", "UNVERIFIED", "CONFLICT", "NOT_APPLICABLE"]
    evidence_url: str | None = None
    evidence_note: str | None = None
    due: date | None = Field(default=None, description="For predictions: when it can be graded")


class ThesisImpact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticker: str
    direction: Literal["STRENGTHEN", "WEAKEN", "NEUTRAL"]
    magnitude: Literal["LOW", "MEDIUM", "HIGH"]
    rationale: str


class PostAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    post_id: str
    content_hash: str
    analyzed_at: datetime
    title: str
    author: str
    summary: str
    relevance: Literal["HIGH", "MEDIUM", "LOW", "NONE"]
    claims: list[Claim] = Field(default_factory=list)
    thesis_impacts: list[ThesisImpact] = Field(default_factory=list)
    new_candidates: list[str] = Field(default_factory=list)
    portfolio_implication: str


def validate_all() -> list[str]:
    errors = []
    store = PostStore()
    for path in sorted(paths.ANALYSES.glob("*.json")):
        try:
            analysis = PostAnalysis.model_validate(read_json(path))
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        if analysis.post_id != path.stem:
            errors.append(f"{path.name}: post_id mismatch")
        if store.get(analysis.post_id) is None:
            errors.append(f"{path.name}: no matching post")
    return errors
