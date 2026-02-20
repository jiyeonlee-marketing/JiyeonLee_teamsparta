"""
KDT 업계 현황 — 한국 IT/교육 뉴스 RSS를 수집해 슬랙에 전달.
Claude API 없이 동작. 자유 아이데이션은 슬랙 스레드에서 진행.
"""

import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import feedparser


# ── RSS 피드 목록 ──────────────────────────────────────────────────────────────
# 피드 URL은 실제 서비스 정책에 따라 변경될 수 있으니 주기적으로 확인 필요.
_FEEDS: list[dict] = [
    {"name": "전자신문",     "url": "https://www.etnews.com/rss/"},
    {"name": "ZDNet Korea", "url": "https://zdnet.co.kr/rss/rss.aspx"},
    {"name": "블로터",       "url": "https://www.bloter.net/feed"},
    {"name": "IT조선",       "url": "https://it.chosun.com/rss/data/it.xml"},
]

# ── 필터 키워드 (제목 또는 요약에 하나라도 포함되면 채택) ────────────────────────
_KEYWORDS: list[str] = [
    "KDT", "내일배움", "부트캠프", "디지털 교육", "AI 교육",
    "코딩 교육", "취업 연계", "훈련 기관", "HRD", "K-Digital",
    "기술 교육", "디지털 훈련", "직업훈련", "재직자 훈련",
]

_MAX_ARTICLES = 5       # 슬랙에 노출할 최대 기사 수
_FETCH_TIMEOUT = 8      # RSS 요청 타임아웃 (초)


@dataclass
class NewsArticle:
    title: str
    link: str
    source: str
    published: datetime.datetime = field(
        default_factory=lambda: datetime.datetime(1970, 1, 1)
    )


def _is_relevant(entry) -> bool:
    text = " ".join([
        getattr(entry, "title", ""),
        getattr(entry, "summary", ""),
    ]).lower()
    return any(kw.lower() in text for kw in _KEYWORDS)


def _parse_feed(feed_meta: dict) -> list[NewsArticle]:
    try:
        d = feedparser.parse(feed_meta["url"])
    except Exception:
        return []

    articles = []
    for entry in d.entries:
        if not _is_relevant(entry):
            continue

        # 날짜 파싱 (없으면 epoch으로 fallback)
        pub = datetime.datetime(1970, 1, 1)
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                pub = datetime.datetime(*entry.published_parsed[:6])
            except Exception:
                pass

        articles.append(
            NewsArticle(
                title=entry.get("title", "(제목 없음)").strip(),
                link=entry.get("link", ""),
                source=feed_meta["name"],
                published=pub,
            )
        )
    return articles


def fetch_industry_news() -> list[NewsArticle]:
    """
    등록된 RSS 피드를 병렬 수집 → 키워드 필터 → 최신순 정렬 → 상위 N개 반환.
    네트워크 장애 시 빈 리스트 반환 (호출부에서 fallback 처리).
    """
    all_articles: list[NewsArticle] = []

    with ThreadPoolExecutor(max_workers=len(_FEEDS)) as executor:
        futures = {executor.submit(_parse_feed, f): f for f in _FEEDS}
        for future in as_completed(futures, timeout=_FETCH_TIMEOUT):
            try:
                all_articles.extend(future.result())
            except Exception:
                pass

    # 중복 URL 제거 후 최신순 정렬
    seen: set[str] = set()
    unique = []
    for a in sorted(all_articles, key=lambda x: x.published, reverse=True):
        if a.link not in seen:
            seen.add(a.link)
            unique.append(a)

    return unique[:_MAX_ARTICLES]


def format_ideation_block(articles: list[NewsArticle]) -> str:
    """Slack mrkdwn 포맷으로 업계 현황 + 자유 아이데이션 섹션 반환."""
    today = datetime.date.today().strftime("%Y-%m-%d")

    if not articles:
        news_text = "_오늘은 관련 뉴스를 찾지 못했어요. 업계 동향을 직접 공유해주세요!_"
    else:
        lines = [
            f"• <{a.link}|{a.title}>  _{a.source}_"
            for a in articles
        ]
        news_text = "\n".join(lines)

    return (
        f"💡 *KDT 업계 현황 — {today} 기준*\n"
        f"{news_text}\n"
        f"_💬 위 내용 보고 자유롭게 아이디어 달아주세요!_"
    )
