from datetime import datetime

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS = ["Processed At", "Video ID", "Title", "Channel", "Link", "Blocks"]


def _log(message):
    # Plain prints show up in the terminal running `streamlit run frontend.py`.
    # Streamlit reruns can wipe on-page warnings before you get to read them,
    # so this is the reliable place to actually see what happened.
    print(f"[history] {message}", flush=True)


def _get_worksheet():
    _log("Starting Google Sheets auth...")

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
    # A valid key: starts_with should read like "-----BEGIN PRIVATE KEY-----\n"
    # (with an ACTUAL newline, i.e. newline_count > 0), and
    # literal_backslash_n_count should be 0. If newline_count is 0 and
    # literal_backslash_n_count is high, the value was likely wrapped in
    # single quotes in secrets.toml, which doesn't convert \n into real
    # newlines. If ends_with shows characters other than
    # "-----END PRIVATE KEY-----\n" (e.g. a stray '","client_email":'),
    # the copy-paste grabbed extra JSON beyond the key value.

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
    _log("Authorized with Google. Opening spreadsheet by ID...")

    spreadsheet = client.open_by_key(st.secrets["GSHEET_ID"])
    _log(f"Opened spreadsheet: '{spreadsheet.title}'")

    worksheet = spreadsheet.sheet1
    _log(f"Using worksheet (tab): '{worksheet.title}'")
    return worksheet


def _ensure_headers(worksheet):
    current = worksheet.row_values(1)
    if current != HEADERS:
        _log(f"Header row missing/mismatched (found {current!r}) — writing headers.")
        worksheet.update("A1", [HEADERS])
    else:
        _log("Header row already present, skipping.")


def add_to_history(video_id, video_link, title, channel, total_blocks):
    """Append one processed-video record as a new row in the sheet."""
    _log(f"add_to_history() called for video_id={video_id!r}, title={title!r}")

    worksheet = _get_worksheet()
    _ensure_headers(worksheet)

    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        video_id,
        title,
        channel,
        video_link,
        total_blocks,
    ]
    _log(f"Appending row: {row}")

    worksheet.append_row(row, value_input_option="USER_ENTERED")
    _log("Row appended successfully.")
