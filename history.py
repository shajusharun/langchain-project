import re
from datetime import datetime

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Column order for the sheet. A row's lifecycle:
#  1. start_entry()    -> writes Started At, Video ID, Title, Channel, Link,
#                          Edited="No", Downloaded="No"
#  2. finish_entry()    -> fills in Ended At and Blocks once generation ends
#  3. mark_edited()     -> flips Edited to "Yes" if the user opens the editor
#  4. mark_downloaded() -> flips Downloaded to "Yes" if the user downloads
HEADERS = [
    "Started At",
    "Ended At",
    "Video ID",
    "Title",
    "Channel",
    "Link",
    "Blocks",
    "Edited",
    "Downloaded",
]


def _log(message):
    # Plain prints show up in the terminal running `streamlit run frontend.py`.
    # Streamlit reruns can wipe on-page warnings before you get to read them,
    # so this is the reliable place to actually see what happened.
    print(f"[history] {message}", flush=True)


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _col_index(name):
    return HEADERS.index(name) + 1


@st.cache_resource(show_spinner=False)
def _authorize_client():
    _log("Authorizing Google Sheets client (cached for the app's lifetime)...")

    if "gcp_service_account" not in st.secrets:
        raise RuntimeError(
            "Missing [gcp_service_account] block in secrets.toml / app secrets."
        )
    if "GSHEET_ID" not in st.secrets:
        raise RuntimeError("Missing GSHEET_ID in secrets.toml / app secrets.")

    creds_info = st.secrets["gcp_service_account"]
    _log(f"Service account email: {creds_info.get('client_email')}")

    private_key = creds_info.get("private_key", "")
    _log(
        "private_key diagnostics: "
        f"length={len(private_key)}, "
        f"starts_with={private_key[:35]!r}, "
        f"ends_with={private_key[-35:]!r}, "
        f"newline_count={private_key.count(chr(10))}, "
        f"literal_backslash_n_count={private_key.count(chr(92) + 'n')}"
    )

    try:
        credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    except ValueError as e:
        raise ValueError(
            "Could not parse the service account private_key from secrets.toml. "
            "Check the 'private_key diagnostics' log line just above this error: "
            "newline_count should be > 0 and literal_backslash_n_count should be 0 "
            "(if not, private_key is probably single-quoted in secrets.toml instead "
            "of double-quoted). Also check ends_with only contains the PEM footer, "
            "with nothing extra copied in from the JSON file. "
            f"Original error: {e}"
        ) from e

    client = gspread.authorize(credentials)
    _log("Authorized with Google.")
    return client


def _get_worksheet():
    client = _authorize_client()
    spreadsheet = client.open_by_key(st.secrets["GSHEET_ID"])
    worksheet = spreadsheet.sheet1
    return worksheet


def _ensure_headers(worksheet):
    current = worksheet.row_values(1)
    if current != HEADERS:
        _log(f"Header row missing/mismatched (found {current!r}) — writing headers.")
        worksheet.update("A1", [HEADERS])
    else:
        _log("Header row already present, skipping.")


def _row_number_from_append_response(response):
    try:
        updated_range = response["updates"]["updatedRange"]
        match = re.search(r"![A-Za-z]+(\d+)", updated_range)
        return int(match.group(1)) if match else None
    except Exception as e:
        _log(f"Could not parse row number from append response {response!r}: {e!r}")
        return None


def start_entry(video_id, video_link, title, channel):
    """
    Append a new row right when generation starts. Returns the sheet row
    number so the row can be updated later (finish_entry, mark_edited,
    mark_downloaded) as the rest of the lifecycle happens.
    """
    _log(f"start_entry() called for video_id={video_id!r}, title={title!r}")

    worksheet = _get_worksheet()
    _ensure_headers(worksheet)

    row = [
        _now(),   # Started At
        "",       # Ended At (filled in by finish_entry)
        video_id,
        title,
        channel,
        video_link,
        "",       # Blocks (filled in by finish_entry)
        "No",     # Edited
        "No",     # Downloaded
    ]
    _log(f"Appending start row: {row}")

    response = worksheet.append_row(row, value_input_option="USER_ENTERED")
    row_number = _row_number_from_append_response(response)
    _log(f"Start row appended at row {row_number}.")
    return row_number


def finish_entry(row_number, total_blocks):
    """Fill in Ended At and Blocks once generation completes."""
    if row_number is None:
        _log("finish_entry() called with no row_number — skipping (no start row to update).")
        return

    _log(f"finish_entry() called for row {row_number}, total_blocks={total_blocks}")
    worksheet = _get_worksheet()
    worksheet.update_cell(row_number, _col_index("Ended At"), _now())
    worksheet.update_cell(row_number, _col_index("Blocks"), total_blocks)
    _log(f"Row {row_number}: Ended At + Blocks updated.")


def mark_edited(row_number):
    """Flip the Edited column to 'Yes' for this row."""
    if row_number is None:
        _log("mark_edited() called with no row_number — skipping.")
        return

    _log(f"mark_edited() called for row {row_number}")
    worksheet = _get_worksheet()
    worksheet.update_cell(row_number, _col_index("Edited"), "Yes")
    _log(f"Row {row_number}: Edited = Yes")


def mark_downloaded(row_number):
    """Flip the Downloaded column to 'Yes' for this row."""
    if row_number is None:
        _log("mark_downloaded() called with no row_number — skipping.")
        return

    _log(f"mark_downloaded() called for row {row_number}")
    worksheet = _get_worksheet()
    worksheet.update_cell(row_number, _col_index("Downloaded"), "Yes")
    _log(f"Row {row_number}: Downloaded = Yes")
