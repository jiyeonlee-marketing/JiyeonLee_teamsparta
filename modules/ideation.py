"""
KDT 방향성 아이데이션 — 주차(week number)에 따라 테마 순환.
Claude API 없이 동작. 추후 AI 연동 시 use_ai=True 옵션 활성화 가능.
"""

import datetime
from dataclasses import dataclass


@dataclass
class IdeationTheme:
    theme: str           # 이번 주 테마명
    question: str        # 핵심 질문
    sub_points: list[str]  # 생각해볼 포인트 3개


# 순환 테마 풀 — 비즈니스 방향성 관련 프레임워크
_THEMES: list[IdeationTheme] = [
    IdeationTheme(
        theme="수강생 경험 설계",
        question="수강생이 캠프를 끝낸 뒤 가장 크게 달라지는 것은 무엇인가?",
        sub_points=[
            "온보딩 → 중반 → 수료 각 단계에서 이탈 원인은?",
            "수강생 Net Promoter Score(NPS)를 높이는 핵심 접점은?",
            "재수강·추천 전환율을 높이는 경험 포인트는?",
        ],
    ),
    IdeationTheme(
        theme="B2G 사업 확장",
        question="정부·공공기관 파트너십을 통해 어떤 새 트랙을 만들 수 있는가?",
        sub_points=[
            "현재 KDT 인증 과정 외 확장 가능한 바우처·훈련 유형은?",
            "지자체/공기업 연계 취업 연결 구조를 만들 수 있는가?",
            "공공 RFP 수주를 위한 내부 역량 중 부족한 부분은?",
        ],
    ),
    IdeationTheme(
        theme="커리큘럼 차별화",
        question="타 부트캠프 대비 콘텐츠·커리큘럼의 실질적 차별점은 무엇인가?",
        sub_points=[
            "업계 채용 트렌드 변화가 커리큘럼에 얼마나 빠르게 반영되는가?",
            "프로젝트 기반 학습(PBL) 비중을 높이면 어떤 효과가 생기는가?",
            "현직 멘토/강사 네트워크 확장 방안은?",
        ],
    ),
    IdeationTheme(
        theme="수료 후 취업 연계",
        question="수료생 취업률을 높이기 위해 구조적으로 바꿀 수 있는 것은?",
        sub_points=[
            "기업 파트너와의 채용 연계 파이프라인 현황과 병목은?",
            "수료생 포트폴리오 품질 관리 프로세스 개선점은?",
            "취업 후 1년 이내 이직률을 낮추는 사후 지원 방안은?",
        ],
    ),
    IdeationTheme(
        theme="운영 효율화",
        question="반복 업무를 자동화하면 어디서 가장 큰 시간·비용 절감이 생기는가?",
        sub_points=[
            "수강 관리·출석·과제 채점 중 자동화 가능한 부분은?",
            "강사/PM 온보딩 프로세스 표준화 현황은?",
            "내부 데이터 분산으로 인해 의사결정이 늦어지는 병목은?",
        ],
    ),
    IdeationTheme(
        theme="브랜드 & 마케팅",
        question="내일배움캠프의 브랜드 인지도를 어떤 채널에서 집중 키울 것인가?",
        sub_points=[
            "현재 수강 신청 전환율이 가장 높은 획득 채널은?",
            "수강생 후기·성공 스토리를 콘텐츠 자산화하는 전략은?",
            "경쟁사 대비 포지셔닝 메시지를 어떻게 명확히 할 것인가?",
        ],
    ),
    IdeationTheme(
        theme="데이터 기반 의사결정",
        question="어떤 지표를 매일/매주 보면 사업 방향이 더 빨리 보이는가?",
        sub_points=[
            "현재 중요하지만 추적하지 못하는 지표는 무엇인가?",
            "코호트 분석으로 발견할 수 있는 수강생 패턴은?",
            "A/B 테스트를 적용할 수 있는 운영·마케팅 영역은?",
        ],
    ),
    IdeationTheme(
        theme="신규 트랙 발굴",
        question="향후 6~12개월 내 가장 수요가 늘 교육 영역은 어디인가?",
        sub_points=[
            "AI·LLM 관련 실무 교육 수요를 어떻게 선점할 것인가?",
            "비개발 직군(PM, 데이터 분석, UX) 트랙 확장 타당성은?",
            "기업 B2B 인하우스 트레이닝 시장 진입 가능성은?",
        ],
    ),
]


def get_weekly_theme(date: datetime.date | None = None) -> IdeationTheme:
    """이번 주 연도+주차 기반으로 테마를 고정 순환 반환."""
    if date is None:
        date = datetime.date.today()
    year, week_num, _ = date.isocalendar()
    idx = (year * 100 + week_num) % len(_THEMES)
    return _THEMES[idx]


def format_ideation_block(theme: IdeationTheme) -> str:
    """Slack mrkdwn 포맷으로 아이데이션 섹션 반환."""
    bullets = "\n".join(f">  • {p}" for p in theme.sub_points)
    return (
        f"💡 *KDT 방향성 아이데이션 — 이번 주 테마: {theme.theme}*\n"
        f"*{theme.question}*\n"
        f"{bullets}\n"
        f"_💬 이 스레드에 아이디어 달아주세요!_"
    )
