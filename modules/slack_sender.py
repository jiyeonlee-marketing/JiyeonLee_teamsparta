"""
Slack 메시지 발송 — 텍스트 블록 + 시트 이미지 업로드.
slack-sdk의 WebClient 사용 (bot token 필요).
"""

import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


_DAY_KO = ["월", "화", "수", "목", "금", "토", "일"]


def _build_message_blocks(
    date: datetime.date,
    link_mission_board: str,
    link_kdt_dashboard: str,
    link_annual_schedule: str,
    link_notion: str,
    ideation_text: str,
) -> list[dict]:
    day = _DAY_KO[date.weekday()]
    date_str = date.strftime(f"%Y-%m-%d ({day})")

    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🌅  모닝 브리핑  |  {date_str}",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "📊 *사업지표 Summary*\n아래 이미지를 확인해주세요.",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "📋 *오늘의 대시보드*\n"
                    f"• <{link_mission_board}|미션 현황판>\n"
                    f"• <{link_kdt_dashboard}|KDT 대시보드>\n"
                    f"• <{link_annual_schedule}|연간 일정>\n"
                    f"• <{link_notion}|회의록 · 노션>"
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": ideation_text},
        },
    ]


def send_morning_briefing(
    token: str,
    channel_id: str,
    link_mission_board: str,
    link_kdt_dashboard: str,
    link_annual_schedule: str,
    link_notion: str,
    ideation_text: str,
    sheet_image_bytes: bytes | None = None,
    date: datetime.date | None = None,
) -> None:
    """
    1. 텍스트 블록 메시지 발송
    2. sheet_image_bytes 가 있으면 PNG 파일을 같은 채널에 업로드
    """
    if date is None:
        date = datetime.date.today()

    client = WebClient(token=token)

    blocks = _build_message_blocks(
        date=date,
        link_mission_board=link_mission_board,
        link_kdt_dashboard=link_kdt_dashboard,
        link_annual_schedule=link_annual_schedule,
        link_notion=link_notion,
        ideation_text=ideation_text,
    )

    # 텍스트 메시지 발송
    result = client.chat_postMessage(
        channel=channel_id,
        blocks=blocks,
        text=f"모닝 브리핑 | {date}",  # 알림 fallback 텍스트
    )
    thread_ts = result["ts"]

    # 사업지표 이미지 업로드 (thread에 첨부)
    if sheet_image_bytes:
        try:
            client.files_upload_v2(
                channel=channel_id,
                filename=f"summary_{date}.png",
                file=sheet_image_bytes,
                title=f"사업지표 Summary {date}",
                thread_ts=thread_ts,
                initial_comment="📊 Summary!B2:X17",
            )
        except SlackApiError as e:
            print(f"[WARN] 이미지 업로드 실패: {e.response['error']}")
