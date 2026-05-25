import streamlit as st
from subtitle_generator import generate_srt_stream
from urllib.parse import urlparse, parse_qs


def extract_video_id(url):
    parsed_url = urlparse(url)
    return parse_qs(parsed_url.query).get("v", [None])[0]

if "srt_blocks" not in st.session_state:
    st.session_state["srt_blocks"] = []

if "is_generating" not in st.session_state:
    st.session_state["is_generating"] = False

st.title("YouTube Hinglish SRT Generator")

video_link = st.text_input("Enter YouTube Video Link")
video_id = extract_video_id(video_link)

if st.button("Generate SRT"):
    st.session_state["srt_blocks"] = []
    st.session_state["is_generating"] = True

    progress_box = st.empty()
    output_container = st.container()

    with st.spinner("Generating Hinglish subtitles..."):
        for srt_block, index, total_blocks in generate_srt_stream(video_id, number_of_blocks=1000):
            st.session_state["srt_blocks"].append(srt_block)

            with output_container:
                st.code(srt_block)

            progress_box.write(f"Generated {index}/{total_blocks} subtitle blocks...")

    st.session_state["is_generating"] = False
    st.success("Generation complete. You can now edit subtitles below.")


if st.session_state["srt_blocks"] and not st.session_state["is_generating"]:
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
        mime="text/plain"
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



