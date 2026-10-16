"""Parse Fanding feed/post HTML observed in a normal logged-in browser session."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from desk import paths
from desk.errors import DomChanged, LockedPost
from desk.store import Post

BASE_URL = "https://fanding.kr"
POST_PATH = re.compile(r"^/@[^/]+/post/(\d+)/?$")
DEFAULT_SELECTORS: dict[str, str] = {
    "authenticated_signal": 'a[href="/messages/"]',
    "feed_container": "section.feed-post-list",
    "feed_card": ".post-feed-card.post",
    "post_link": 'a[href*="/post/"]',
    "post_root": "section.main-section.detail__section",
    "post_title": ".main-section__title",
    "post_author": ".desc__author .desc__text",
    "post_metadata": ".main-section__desc .desc__text",
    "post_body": ".main-section__main-text .tiptap",
    "locked_marker": "잠긴 콘텐츠 열어보기",
}


def load_selectors() -> dict[str, str]:
    selectors = DEFAULT_SELECTORS.copy()
    path = paths.CONFIG / "fanding_selectors.json"
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        selectors.update({k: v for k, v in raw.items() if k in selectors and v})
    return selectors


def clean_text(text: str) -> str:
    text = text.replace(" ", " ").replace("​", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def content_hash(body: str) -> str:
    return hashlib.sha256(clean_text(body).encode("utf-8")).hexdigest()


def parse_relative_datetime(raw: str | None, reference: datetime) -> datetime | None:
    """Fanding shows '5분 전', '3시간 전', '2일 전' or '10월 5일' in KST."""
    if not raw:
        return None
    value = raw.strip()
    for pattern, unit in ((r"(\d+)\s*분 전", "minutes"), (r"(\d+)\s*시간 전", "hours"),
                          (r"(\d+)\s*일 전", "days")):
        match = re.fullmatch(pattern, value)
        if match:
            return reference - timedelta(**{unit: int(match.group(1))})
    match = re.fullmatch(r"(?:(\d{4})년\s*)?(\d{1,2})월\s*(\d{1,2})일", value)
    if match:
        year = int(match.group(1)) if match.group(1) else reference.year
        candidate = reference.replace(year=year, month=int(match.group(2)), day=int(match.group(3)),
                                      hour=0, minute=0, second=0, microsecond=0)
        if not match.group(1) and candidate > reference + timedelta(days=1):
            candidate = candidate.replace(year=candidate.year - 1)
        return candidate
    return None


def parse_feed_urls(html: str, selectors: dict[str, str] | None = None) -> list[str]:
    rules = selectors or DEFAULT_SELECTORS
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(rules["feed_card"])
    anchors = ([a for card in cards for a in card.select(rules["post_link"])]
               if cards else soup.select(rules["post_link"]))
    urls: list[str] = []
    for anchor in anchors:
        href = anchor.get("href", "").split("?", 1)[0]
        if POST_PATH.match(href):
            absolute = urljoin(BASE_URL, href if href.endswith("/") else href + "/")
            if absolute not in urls:
                urls.append(absolute)
    return urls


def post_id_from_url(url: str) -> str:
    match = POST_PATH.match(urlparse(url).path)
    if not match:
        raise ValueError(f"Not a Fanding post URL: {url}")
    return match.group(1)


def parse_post_html(html: str, url: str, seen_at: datetime,
                    selectors: dict[str, str] | None = None) -> Post:
    rules = selectors or DEFAULT_SELECTORS
    soup = BeautifulSoup(html, "html.parser")
    body_node = soup.select_one(rules["post_body"])
    body_text = body_node.get_text("\n", strip=True) if body_node else ""
    if rules["locked_marker"] in soup.get_text(" ", strip=True) and not body_text:
        raise LockedPost(url)
    if body_node is None:
        body_node = soup.select_one(".main-section__main-text")
        body_text = body_node.get_text("\n", strip=True) if body_node else ""
    if body_node is None:
        raise DomChanged(f"post body not found: {url}")

    title_node = soup.select_one(rules["post_title"])
    author_node = soup.select_one(rules["post_author"]) or soup.select_one(".desc__author")
    title = clean_text(title_node.get_text(" ", strip=True)) if title_node else ""
    author = clean_text(author_node.get_text(" ", strip=True)) if author_node else ""
    body = clean_text(body_text)
    if not (title and author and body):
        raise DomChanged(f"required post fields missing: {url}")
    meta = [n.get_text(" ", strip=True) for n in soup.select(rules["post_metadata"])]
    published_raw = next((v for v in meta if v != author and not v.startswith("조회")), None)
    post_id = post_id_from_url(url)
    return Post(
        post_id=post_id,
        url=f"{BASE_URL}{urlparse(url).path}",
        title=title,
        author=author,
        published_raw=published_raw,
        published_at=parse_relative_datetime(published_raw, seen_at),
        body=body,
        content_hash=content_hash(body),
        first_seen_at=seen_at,
        updated_at=seen_at,
    )
