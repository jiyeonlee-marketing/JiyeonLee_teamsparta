"""
모닝 브리핑 초기 설정 도우미.

실행:
    python setup.py

각 항목을 안내에 따라 입력하면 .env 파일이 생성되고
Slack 연결 테스트까지 자동으로 진행됩니다.
"""

import os
import sys
import json
import getpass

# ── 의존 패키지 확인 ────────────────────────────────────────────────────────────
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("[오류] 먼저 패키지를 설치해주세요: pip install -r requirements.txt")
    sys.exit(1)

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def _ask(prompt: str, secret: bool = False, default: str = "") -> str:
    display = f"{prompt}"
    if default:
        display += f" [{default}]"
    display += ": "
    if secret:
        value = getpass.getpass(display)
    else:
        value = input(display)
    return value.strip() or default


def _section(title: str) -> None:
    print(f"\n{'─' * 55}")
    print(f"  {title}")
    print(f"{'─' * 55}")


def _guide_slack() -> tuple[str, str]:
    _section("① Slack 설정")
    print("""
  1. https://api.slack.com/apps → [Create New App] → From scratch
  2. 앱 이름 입력 후 워크스페이스 선택
  3. [OAuth & Permissions] → Scopes → Bot Token Scopes 추가:
       chat:write   files:write
  4. [Install to Workspace] → Bot User OAuth Token 복사  (xoxb-...)
  5. 브리핑 받을 채널 우클릭 → [채널 ID 복사]  (C 로 시작하는 11자리)
  6. 해당 채널에 앱 초대:  /invite @앱이름
""")
    token = _ask("  Slack Bot Token (xoxb-...)", secret=True)
    channel = _ask("  채널 ID (예: C0ABC123DEF)")
    return token, channel


def _guide_sheets() -> tuple[str, str]:
    _section("② Google Sheets 설정")
    print("""
  1. https://console.cloud.google.com → 프로젝트 선택/생성
  2. [API 및 서비스] → [사용 설정된 API] → 아래 두 API 활성화:
       Google Sheets API  /  Google Drive API
  3. [사용자 인증 정보] → [서비스 계정 만들기]
  4. 서비스 계정 선택 → [키] 탭 → [키 추가] → JSON 다운로드
  5. 다운받은 JSON 파일을  credentials/google_service_account.json  으로 복사
  6. 사업지표 Google Sheets 열기 → URL에서 문서 ID 복사:
       https://docs.google.com/spreadsheets/d/[여기가 ID]/edit
  7. Sheets 공유 설정에 서비스 계정 이메일(JSON 내 client_email)을 뷰어로 추가
""")
    os.makedirs("credentials", exist_ok=True)
    json_path = _ask(
        "  서비스 계정 JSON 경로",
        default="./credentials/google_service_account.json",
    )
    doc_id = _ask("  사업지표 Sheets 문서 ID")
    return json_path, doc_id


def _guide_links() -> dict[str, str]:
    _section("③ 대시보드 링크 설정")
    print("  매일 아침 슬랙에 첨부할 링크를 입력해주세요.\n")
    return {
        "LINK_MISSION_BOARD":   _ask("  미션 현황판 URL"),
        "LINK_KDT_DASHBOARD":   _ask("  KDT 대시보드 URL"),
        "LINK_ANNUAL_SCHEDULE": _ask("  연간 일정 URL"),
        "LINK_NOTION":          _ask("  회의록 · 노션 URL"),
    }


def _write_env(values: dict[str, str]) -> None:
    lines = [f'{k}={v}' for k, v in values.items()]
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n  ✓ .env 파일 저장 완료: {ENV_PATH}")


def _test_slack(token: str, channel: str) -> bool:
    _section("④ Slack 연결 테스트")
    client = WebClient(token=token)
    try:
        resp = client.auth_test()
        print(f"  ✓ 봇 인증 성공: @{resp['user']}  (워크스페이스: {resp['team']})")
    except SlackApiError as e:
        print(f"  ✗ 봇 인증 실패: {e.response['error']}")
        print("    → Bot Token 값을 다시 확인해주세요.")
        return False

    try:
        client.chat_postMessage(
            channel=channel,
            text="✅ 모닝 브리핑 연결 테스트 완료! 설정이 정상적으로 완료되었습니다.",
        )
        print(f"  ✓ 테스트 메시지 발송 완료 (채널: {channel})")
    except SlackApiError as e:
        print(f"  ✗ 메시지 발송 실패: {e.response['error']}")
        print("    → 채널 ID 확인 및 /invite @앱이름 으로 앱이 채널에 초대됐는지 확인해주세요.")
        return False

    return True


def _show_cron() -> None:
    _section("⑤ 자동 실행 설정 (크론)")
    python = sys.executable
    script = os.path.abspath("main.py")
    print(f"""
  아래 크론을 등록하면 평일 오전 9시에 자동 발송됩니다.

  터미널에서:
    crontab -e

  아래 줄 추가:
    0 9 * * 1-5 {python} {script} >> /tmp/morning_briefing.log 2>&1

  실행 시간을 바꾸고 싶다면:
    50 8 * * 1-5  → 오전 8시 50분
    30 8 * * 1-5  → 오전 8시 30분
""")


def main() -> None:
    print("\n🌅  모닝 브리핑 초기 설정")
    print("   각 항목을 입력하면 .env가 생성되고 연결 테스트까지 진행됩니다.\n")

    if os.path.exists(ENV_PATH):
        overwrite = _ask(".env 파일이 이미 존재합니다. 덮어쓸까요? (y/N)", default="N")
        if overwrite.lower() != "y":
            print("설정을 취소했습니다.")
            sys.exit(0)

    # 각 섹션 입력
    slack_token, slack_channel = _guide_slack()
    sheets_json, sheets_doc_id = _guide_sheets()
    links = _guide_links()

    # .env 저장
    env_values = {
        "SLACK_BOT_TOKEN":             slack_token,
        "SLACK_CHANNEL_ID":            slack_channel,
        "GOOGLE_SERVICE_ACCOUNT_JSON": sheets_json,
        "SHEETS_DOCUMENT_ID":          sheets_doc_id,
        **links,
    }
    _write_env(env_values)

    # Slack 연결 테스트
    ok = _test_slack(slack_token, slack_channel)

    # 크론 안내
    _show_cron()

    if ok:
        print("=" * 55)
        print("  🎉 설정 완료! 이제 python main.py 로 바로 실행해보세요.")
        print("=" * 55)
    else:
        print("=" * 55)
        print("  ⚠️  Slack 연결에 문제가 있습니다. 위 오류를 확인 후")
        print("     python setup.py 를 다시 실행해주세요.")
        print("=" * 55)
        sys.exit(1)


if __name__ == "__main__":
    main()
