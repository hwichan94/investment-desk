from desk.errors import AuthRequired, PageTimeout


def feed_html(post_ids, author="T3chfeed"):
    cards = "".join(
        f'<div class="post-feed-card post"><a href="/@{author}/post/{pid}/">글</a></div>'
        for pid in post_ids
    )
    return f'<html><a href="/messages/">msg</a><section class="feed-post-list">{cards}</section></html>'


def post_html(title="제목", author="T3chfeed_테크피드", when="3시간 전", body="본문 내용입니다.",
              locked=False):
    body_html = "" if locked else f"<p>{body}</p>"
    marker = "<button>잠긴 콘텐츠 열어보기</button>" if locked else ""
    return f"""
    <section class="main-section detail__section">
      <h1 class="main-section__title">{title}</h1>
      <div class="main-section__desc">
        <span class="desc__author"><span class="desc__text">{author}</span></span>
        <span class="desc__text">{when}</span><span class="desc__text">조회 10</span>
      </div>
      <div class="main-section__main-text"><div class="tiptap">{body_html}</div></div>
      {marker}
    </section>"""


class FakeSession:
    def __init__(self, feed, posts, auth=True, timeouts=None):
        self.feed, self.posts, self.auth = feed, posts, auth
        self.timeouts = dict(timeouts or {})
        self.calls = []

    def feed_html(self, url):
        if not self.auth:
            raise AuthRequired("expired")
        return self.feed

    def post_html(self, url):
        self.calls.append(url)
        pid = url.rstrip("/").rsplit("/", 1)[-1]
        if self.timeouts.get(pid, 0) > 0:
            self.timeouts[pid] -= 1
            raise PageTimeout(url)
        return self.posts[pid]
