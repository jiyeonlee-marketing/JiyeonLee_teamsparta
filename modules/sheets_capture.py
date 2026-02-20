"""
Google Sheets의 Summary!B2:X17 범위를 PNG 이미지로 변환.
gspread로 데이터를 읽고 matplotlib으로 테이블 이미지 생성.
"""

import io
import gspread
from google.oauth2.service_account import Credentials
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd


_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def _get_sheet_data(
    service_account_json: str,
    document_id: str,
    worksheet_name: str,
    range_notation: str,
) -> list[list]:
    creds = Credentials.from_service_account_file(service_account_json, scopes=_SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(document_id).worksheet(worksheet_name)
    rows = sheet.get(range_notation, value_render_option="FORMATTED_VALUE")
    return rows


def _rows_to_df(rows: list[list]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    max_cols = max(len(r) for r in rows)
    padded = [r + [""] * (max_cols - len(r)) for r in rows]
    df = pd.DataFrame(padded[1:], columns=padded[0])
    return df


def render_table_to_bytes(
    service_account_json: str,
    document_id: str,
    worksheet_name: str = "Summary",
    range_notation: str = "B2:X17",
) -> bytes:
    """
    지정 범위를 스타일된 테이블 이미지(PNG)로 반환.
    반환값: PNG bytes (Slack 업로드용)
    """
    rows = _get_sheet_data(service_account_json, document_id, worksheet_name, range_notation)
    df = _rows_to_df(rows)

    n_rows, n_cols = df.shape
    fig_width = max(16, n_cols * 1.1)
    fig_height = max(4, n_rows * 0.45 + 1.2)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")

    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc="center",
        loc="center",
        bbox=[0, 0, 1, 1],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)

    # 헤더 스타일
    header_color = "#1B4F72"
    row_even_color = "#EBF5FB"
    row_odd_color = "#FFFFFF"

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#BDC3C7")
        cell.set_linewidth(0.5)
        if row == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor(row_even_color)
        else:
            cell.set_facecolor(row_odd_color)

    fig.patch.set_facecolor("#FFFFFF")
    plt.tight_layout(pad=0.3)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
