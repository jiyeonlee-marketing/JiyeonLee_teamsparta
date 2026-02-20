"""
모닝 브리핑 자동화 — 메인 실행 진입점.

실행 방법:
    python main.py

크론 등록 예시 (평일 오전 8시 50분):
    50 8 * * 1-5 /usr/bin/python3 /path/to/main.py >> /var/log/morning_briefing.log 2>&1
"""

import sys
from config import Config
from modules.sheets_capture import render_table_to_bytes
from modules.ideation import get_weekly_theme, format_ideation_block
from modules.slack_sender import send_morning_briefing


def main() -> None:
    cfg = Config()

    # 1. 사업지표 시트 스크린샷 (PNG bytes)
    print("[1/3] Google Sheets 데이터 읽는 중...")
    try:
        sheet_image = render_table_to_bytes(
            service_account_json=cfg.GOOGLE_SERVICE_ACCOUNT_JSON,
            document_id=cfg.SHEETS_DOCUMENT_ID,
            worksheet_name=cfg.SHEETS_SUMMARY_WORKSHEET,
            range_notation=cfg.SHEETS_SUMMARY_RANGE,
        )
        print("      → 이미지 생성 완료")
    except Exception as e:
        print(f"      [WARN] 시트 이미지 생성 실패 (스킵): {e}")
        sheet_image = None

    # 2. 이번 주 KDT 아이데이션 테마
    print("[2/3] 이번 주 아이데이션 테마 로드 중...")
    theme = get_weekly_theme()
    ideation_text = format_ideation_block(theme)
    print(f"      → 테마: {theme.theme}")

    # 3. Slack 발송
    print("[3/3] Slack 발송 중...")
    try:
        send_morning_briefing(
            token=cfg.SLACK_BOT_TOKEN,
            channel_id=cfg.SLACK_CHANNEL_ID,
            link_mission_board=cfg.LINK_MISSION_BOARD,
            link_kdt_dashboard=cfg.LINK_KDT_DASHBOARD,
            link_annual_schedule=cfg.LINK_ANNUAL_SCHEDULE,
            link_notion=cfg.LINK_NOTION,
            ideation_text=ideation_text,
            sheet_image_bytes=sheet_image,
        )
        print("      → 발송 완료!")
    except Exception as e:
        print(f"[ERROR] Slack 발송 실패: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
