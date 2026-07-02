from email.policy import default
import streamlit as st
import streamlit.components.v1 as components
from subtitle_generator import generate_srt_stream, extract_video_id
from urllib.parse import urlparse, parse_qs



if "srt_blocks" not in st.session_state:
    st.session_state["srt_blocks"] = []

if "is_generating" not in st.session_state:
    st.session_state["is_generating"] = False

if "show_edit" not in st.session_state:
    st.session_state["show_edit"] = False

st.title("YouTube Hinglish Subtitle Generator")

video_link = st.text_input("Enter YouTube Video Link", value="youtube.com/watch?v=TlppYYh-Gwc")


if st.button("Generate SRT"):
    st.session_state["srt_blocks"] = []
    st.session_state["is_generating"] = True
    st.session_state["show_edit"] = False

    progress_box = st.empty()
    output_container = st.container()

    with st.spinner("Generating Hinglish subtitles..."):
        for srt_block, index, total_blocks in generate_srt_stream(video_link, number_of_blocks=3000):
            st.session_state["srt_blocks"].append(srt_block)

            with output_container:
                st.code(srt_block)

            progress_box.write(f"Generated {index}/{total_blocks} subtitle blocks...")

    st.session_state["is_generating"] = False
    st.success("Generation complete. You can now edit subtitles below.")


if st.session_state["srt_blocks"] and not st.session_state["is_generating"]:
    video_id = extract_video_id(video_link)
    raw_srt_content = "".join(
        block.strip() + "\n\n" for block in st.session_state["srt_blocks"]
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Edit Subtitles before downloading"):
            st.session_state["show_edit"] = True

    with col2:
        st.download_button(
            label="Download SRT file",
            data=raw_srt_content,
            file_name=f"{video_id}_hinglish.srt",
            mime="text/plain"
        )

    if st.session_state["show_edit"]:
        st.markdown("<div id='edit-section'></div>", unsafe_allow_html=True)
        st.subheader("Edit Subtitles")

        final_srt_content = ""

        for index, block in enumerate(st.session_state["srt_blocks"], start=1):
            edited_block = st.text_area(
                label=f"Edit Block {index}",
                value=block,
                key=f"edit_block_{index}",
                height=120
            )

            final_srt_content += edited_block.strip() + "\n\n"

        st.download_button(
            label="Download Edited SRT",
            data=final_srt_content,
            file_name=f"{video_id}_hinglish_edited.srt",
            mime="text/plain",
            key="download_edited_srt"
        )

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




# import streamlit as st
# from subtitle_generator import generate_srt_stream
# from urllib.parse import urlparse, parse_qs

# def extract_video_id(url):
#     parsed_url = urlparse(url)
#     return parse_qs(parsed_url.query).get("v", [None])[0]



# st.title("YouTube Hinglish SRT Generator")
# #video_id = st.text_input("Enter YouTube Video ID", value="6fhFI8o3PPQ")
# video_link = st.text_input("Enter YouTube Video Link")
# video_id = extract_video_id(video_link)


# if st.button("Generate SRT"):
#     srt_content = ""

#     progress_box = st.empty()
#     output_container = st.container()

#     with st.spinner("Generating Hinglish subtitles..."):
#         for index, srt_block in enumerate(generate_srt_stream(video_id), start=1):
#             srt_content += srt_block

#             with output_container:
#                 st.code(srt_block)

#             progress_box.write(f"Generated {index} subtitle blocks...")

#     st.success("SRT generated successfully!")

#     st.download_button(
#         label="Download SRT File",
#         data=srt_content,
#         file_name=f"{video_id}_hinglish.srt",
#         mime="text/plain"
#     )



