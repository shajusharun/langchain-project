import streamlit as st
import streamlit.components.v1 as components
from subtitle_generator import generate_srt_stream, extract_video_id, get_video_details
from history import start_entry, finish_entry, mark_edited, mark_downloaded


if "srt_blocks" not in st.session_state:
    st.session_state["srt_blocks"] = []

if "is_generating" not in st.session_state:
    st.session_state["is_generating"] = False

if "show_edit" not in st.session_state:
    st.session_state["show_edit"] = False

if "history_row" not in st.session_state:
    st.session_state["history_row"] = None

st.title("YouTube Hinglish Subtitle Generator")

video_link = st.text_input("Enter YouTube Video Link", value="youtube.com/watch?v=TlppYYh-Gwc")

generate_clicked = st.button("Generate SRT", disabled=st.session_state["is_generating"])

# Reserve slots for the top section (success message + action buttons)
# and the output section (streamed blocks + edit UI), in that order.
# Position on the page is fixed here, at creation time — content can be
# added to either container later, regardless of when that happens.
top_section = st.container()
output_container = st.container()

# Step 1: on click, just flip the flag and rerun. This lets the button
# re-render as disabled *before* the (blocking) generation loop starts —
# Streamlit only pushes widget attribute changes like `disabled` between
# script runs, not mid-loop, so the generation itself can't happen in
# this same run if we want the disabled state to actually show up.
if generate_clicked and not st.session_state["is_generating"]:
    st.session_state["srt_blocks"] = []
    st.session_state["is_generating"] = True
    st.session_state["show_edit"] = False
    st.session_state["history_status"] = None
    st.session_state["history_row"] = None
    st.rerun()

# Step 2: this run starts with is_generating already True (and the button
# already rendered disabled above), so it's safe to do the actual work.
if st.session_state["is_generating"]:
    blocks_generated = 0
    video_id = extract_video_id(video_link)

    with top_section:
        progress_box = st.empty()

        with st.spinner("Generating Hinglish subtitles..."):
            # Add the history row up front, before any subtitle blocks are
            # generated, so the "Started At" timestamp reflects the true
            # start time. Wrapped in try/except so a logging hiccup here
            # doesn't block generation itself. The result is stashed in
            # session_state (not shown via st.warning here) because the
            # st.rerun() below would wipe an on-screen message before
            # you'd ever see it — check history.py's print() logs in the
            # terminal for full detail regardless.
            try:
                details = get_video_details(video_link)
            except Exception as e:
                print(f"[frontend] Could not fetch video details before generation: {e!r}", flush=True)
                details = {}

            try:
                st.session_state["history_row"] = start_entry(
                    video_id=video_id,
                    video_link=video_link,
                    title=details.get("title"),
                    channel=details.get("channel"),
                )
            except Exception as e:
                print(f"[frontend] Failed to create history row: {e!r}", flush=True)
                st.session_state["history_row"] = None
                st.session_state["history_status"] = ("error", f"Couldn't create history row: {e}")

            for srt_block, index, total_blocks in generate_srt_stream(video_link, number_of_blocks=20000):
                st.session_state["srt_blocks"].append(srt_block)
                blocks_generated = index

                with output_container:
                    st.code(srt_block)

                progress_box.write(f"Generated {index}/{total_blocks} subtitle blocks...")

    if blocks_generated > 0 and st.session_state.get("history_row"):
        try:
            finish_entry(st.session_state["history_row"], total_blocks=blocks_generated)
            st.session_state["history_status"] = None
        except Exception as e:
            print(f"[frontend] Failed to finish history row: {e!r}", flush=True)
            st.session_state["history_status"] = ("error", f"Couldn't finish history row: {e}")

    st.session_state["is_generating"] = False
    # Rerun once more so the button re-renders as enabled immediately,
    # instead of staying visually disabled until the next interaction.
    st.rerun()


if st.session_state["srt_blocks"] and not st.session_state["is_generating"]:
    video_id = extract_video_id(video_link)
    raw_srt_content = "".join(
        block.strip() + "\n\n" for block in st.session_state["srt_blocks"]
    )

    # If edit mode is on and the text areas have already been rendered at
    # least once (so their edited values exist in session_state under their
    # keys), build the download data from those edited values instead of
    # the raw, freshly-generated blocks.
    num_blocks = len(st.session_state["srt_blocks"])
    edits_available = st.session_state["show_edit"] and all(
        f"edit_block_{i}" in st.session_state for i in range(1, num_blocks + 1)
    )

    if edits_available:
        download_content = "".join(
            st.session_state[f"edit_block_{i}"].strip() + "\n\n"
            for i in range(1, num_blocks + 1)
        )
        download_filename = f"{video_id}_hinglish_edited.srt"
    else:
        download_content = raw_srt_content
        download_filename = f"{video_id}_hinglish.srt"

    with top_section:
        st.success("Generation complete. You can download the SRT file now, and edit/fix it in YT studio OR you can edit/fix subtitles here and then download SRT.")

        history_status = st.session_state.get("history_status")
        if history_status and history_status[0] == "error":
            st.error(f"History sheet: {history_status[1]}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Edit Subtitles before downloading"):
                st.session_state["show_edit"] = True
                try:
                    mark_edited(st.session_state.get("history_row"))
                except Exception as e:
                    print(f"[frontend] Failed to mark Edited in history: {e!r}", flush=True)

        with col2:
            if st.download_button(
                label="Download SRT file",
                data=download_content,
                file_name=download_filename,
                mime="text/plain"
            ):
                try:
                    mark_downloaded(st.session_state.get("history_row"))
                except Exception as e:
                    print(f"[frontend] Failed to mark Downloaded in history: {e!r}", flush=True)

    if st.session_state["show_edit"]:
        with output_container:
            st.markdown("<div id='edit-section'></div>", unsafe_allow_html=True)
            st.subheader("Edit Subtitles")

            for index, block in enumerate(st.session_state["srt_blocks"], start=1):
                st.text_area(
                    label=f"Edit Block {index}",
                    value=block,
                    key=f"edit_block_{index}",
                    height=120
                )

            if st.download_button(
                label="Download SRT file",
                data=download_content,
                file_name=download_filename,
                mime="text/plain",
                key="download_bottom"
            ):
                try:
                    mark_downloaded(st.session_state.get("history_row"))
                except Exception as e:
                    print(f"[frontend] Failed to mark Downloaded in history: {e!r}", flush=True)

        # Scroll the page down to the edit section once it's rendered
        components.html(
            """
            <script>
                var el = window.parent.document.getElementById('edit-section');
                if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }
            </script>
            """,
            height=0,
        )
    else:
        # Not in edit mode: keep showing the generated blocks read-only.
        # These were only written to output_container during the live
        # generation loop, so on every later rerun (e.g. after clicking
        # Download) they need to be re-drawn from session_state, or they'd
        # appear to "disappear" once generation finishes.
        with output_container:
            for block in st.session_state["srt_blocks"]:
                st.code(block.strip())