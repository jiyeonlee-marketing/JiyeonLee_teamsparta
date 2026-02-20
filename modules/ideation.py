"""
KDT 업계 현황 — 한국 IT/교육 뉴스 RSS를 수집해 슬랙에 전달.
Claude API 없이 동작. 자유 아이데이션은 슬랙 스레드에서 진행.
"""

import datetime
import email.utils
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import requests


# ── RSS 피드 목록 ──────────────────────────────────────────────────────────────
_FEEDS: list[dict] = [
    {"name": "전자신문",     "url": "https://www.etnews.com/rss/"},
    {"name": "ZDNet Korea", "url": "https://zdnet.co.kr/rss/rss.aspx"},
    {"name": "블로터",       "url": "https://www.bloter.net/feed"},
    {"name": "IT조선",       "url": "https://it.chosun.com/rss/data/it.xml"},
]

# ── 필터 키워드 ────────────────────────────────────────────────────────────────
_KEYWORDS: list[str] = [
    "KDT", "내일배움", "부트캠프", "디지털 교육", "AI 교육",
    "코딩 교육", "취업 연계", "훈련 기관", "HRD", "K-Digital",
    "기술 교육", "디지털 훈련", "직업훈련", "재직자 훈련",
]

_MAX_ARTICLES = 5
_FETCH_TIMEOUT = 8


@dataclass
class NewsArticle:
    title: str
    link: str
    source: str
    published: datetime.datetime = field(
        default_factory=lambda: datetime.datetime(1970, 1, 1)
    )


def _is_relevant(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    return any(kw.lower() in text for kw in _KEYWORDS)


def _parse_date(date_str: str) -> datetime.datetime:
    try:
        return datetime.datetime(*email.utils.parsedate(date_str)[:6])
    except Exception:
        return datetime.datetime(1970, 1, 1)


def _parse_feed(feed_meta: dict) -> list[NewsArticle]:
    try:
        resp = requests.get(feed_meta["url"], timeout=_FETCH_TIMEOUT,
                            headers={"User-Agent": "MorningBriefingBot/1.0"})
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception:
        return []

    articles = []
    # RSS 2.0: <channel><item>...</item></channel>
    for item in root.iter("item"):
        title   = (item.findtext("title")   or "").strip()
        link    = (item.findtext("link")    or "").strip()
        summary = (item.findtext("description") or "").strip()
        pub_raw = item.findtext("pubDate") or ""

        if not _is_relevant(title, summary):
            continue

        articles.append(NewsArticle(
            title=title or "(제목 없음)",
            link=link,
            source=feed_meta["name"],
            published=_parse_date(pub_raw),
        ))

    return articles


def fetch_industry_news() -> list[NewsArticle]:
    """RSS 피드 병렬 수집 → 키워드 필터 → 최신순 정렬 → 상위 N개 반환."""
    all_articles: list[NewsArticle] = []

    with ThreadPoolExecutor(max_workers=len(_FEEDS)) as executor:
        futures = {executor.submit(_parse_feed, f): f for f in _FEEDS}
        for future in as_completed(futures, timeout=_FETCH_TIMEOUT + 2):
            try:
                all_articles.extend(future.result())
            except Exception:
                pass

    seen: set[str] = set()
    unique = []
    for a in sorted(all_articles, key=lambda x: x.published, reverse=True):
        if a.link not in seen:
            seen.add(a.link)
            unique.append(a)

    return unique[:_MAX_ARTICLES]


def format_ideation_block(articles: list[NewsArticle]) -> str:
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
