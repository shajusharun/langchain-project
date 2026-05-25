from youtube_transcript_api import YouTubeTranscriptApi
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import streamlit as st
from youtube_transcript_api.proxies import GenericProxyConfig


load_dotenv()

llm = ChatOpenAI(model="gpt-4.1-mini")


def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)

    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"




def translate_to_hinglish(text):
    prompt = f"""
Translate this Hindi YouTube transcript line into Hinglish.
Keep it phonetically similar and close to meaning to the original line. Any English words used should have correct spelling.
Do not add extra explanation.

Hindi:
{text}

Hinglish:
"""
    response = llm.invoke(prompt)
    return response.content.strip()


def fix_capitalization(text, should_capitalize_start):
    text = text.strip()

    if not text:
        return text

    # Fix first character based on previous line
    if should_capitalize_start:
        text = text[0].upper() + text[1:]
    else:
        text = text[0].lower() + text[1:]

    # Capitalize first character after every full stop
    result = ""
    capitalize_next = False

    for char in text:
        if capitalize_next and char.isalpha():
            result += char.upper()
            capitalize_next = False
        else:
            result += char

        if char == ".":
            capitalize_next = True

    return result


def generate_srt_stream(video_id, number_of_blocks=None ):

    proxy_url = st.secrets.get("PROXY_URL")

    api = YouTubeTranscriptApi(
        proxy_config=GenericProxyConfig(
            http_url=proxy_url,
            https_url=proxy_url,
        )
    )
    #api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id, languages=["hi"])
    total_blocks = len(transcript)

    previous_line_ended_with_full_stop = True
    for index, line in enumerate(transcript, start=1):
        if number_of_blocks and index > number_of_blocks:
            break
        hinglish_text = translate_to_hinglish(line.text)
        hinglish_text = fix_capitalization(
            hinglish_text,
            previous_line_ended_with_full_stop
        )

        start_time = format_srt_time(line.start)
        end_time = format_srt_time(line.start + line.duration)
        previous_line_ended_with_full_stop = hinglish_text.endswith(".")

        srt_block = (
            f"{index}\n"
            f"{start_time} --> {end_time}\n"
            f"{hinglish_text}\n\n"
        )

        yield srt_block, index, total_blocks