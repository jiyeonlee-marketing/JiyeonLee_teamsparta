import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Slack
    SLACK_BOT_TOKEN: str = os.environ["SLACK_BOT_TOKEN"]
    SLACK_CHANNEL_ID: str = os.environ["SLACK_CHANNEL_ID"]

    # Google Sheets
    GOOGLE_SERVICE_ACCOUNT_JSON: str = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    SHEETS_DOCUMENT_ID: str = os.environ["SHEETS_DOCUMENT_ID"]
    SHEETS_SUMMARY_WORKSHEET: str = "Summary"
    SHEETS_SUMMARY_RANGE: str = "B2:X17"

    # 대시보드 링크
    LINK_MISSION_BOARD: str = os.environ["LINK_MISSION_BOARD"]
    LINK_KDT_DASHBOARD: str = os.environ["LINK_KDT_DASHBOARD"]
    LINK_ANNUAL_SCHEDULE: str = os.environ["LINK_ANNUAL_SCHEDULE"]
    LINK_NOTION: str = os.environ["LINK_NOTION"]
