from youtube_transcript_api import YouTubeTranscriptApi
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import streamlit as st
from youtube_transcript_api.proxies import WebshareProxyConfig
import requests
import yt_dlp
from urllib.parse import urlparse, parse_qs
import difflib


load_dotenv()

llm = ChatOpenAI(model="gpt-4.1-mini")




import time

# ... existing imports stay as they are ...


def retry_on_failure(fn, *args, retries=5, base_delay=2, max_delay=20, **kwargs):
    """
    Call fn(*args, **kwargs), retrying on any exception up to `retries` times
    with exponential backoff (capped at max_delay), before finally re-raising
    the last exception.
    """
    last_exc = None

    for attempt in range(1, retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt == retries:
                break
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            print(
                f"[retry_on_failure] {fn.__name__} failed on attempt "
                f"{attempt}/{retries}: {e}. Retrying in {delay}s..."
            )
            time.sleep(delay)

    raise last_exc



def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)

    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


def get_video_details(url):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    return {
        "title": info.get("title"),
        "description": info.get("description"),
        "channel": info.get("channel"),
    }




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


def extract_video_id(url):
    if not url:
        return None

    # Allow URLs without a scheme (e.g. "youtube.com/watch?v=...")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed_url = urlparse(url)
    host = parsed_url.netloc.lower().replace("www.", "")

    if host == "youtu.be":
        # Path is like /EY9HBncyvZQ — video id is the first path segment.
        # Any query string (e.g. ?si=...) is ignored.
        video_id = parsed_url.path.lstrip("/").split("/")[0]
        return video_id or None

    if host in ("youtube.com", "m.youtube.com"):
        if parsed_url.path == "/watch":
            return parse_qs(parsed_url.query).get("v", [None])[0]
        if parsed_url.path.startswith(("/embed/", "/shorts/")):
            segments = parsed_url.path.split("/")
            return segments[2] if len(segments) > 2 else None

    return None


def generate_srt_stream(video_link, number_of_blocks=None ):



    video_id = extract_video_id(video_link)
    # response = requests.post(
    # "https://www.youtube-transcript.io/api/transcripts",
    # headers={
    # "Authorization": "Basic 6a141ab7020bd93fbc31f06e", 
    # "Content-Type": "application/json"},
    # json={"ids": ["eBSLhYnDXXM"]}
    # )


    # data = response.json()

    # # If API returns a list, take first item
    # if isinstance(data, list):
    #     data = data[0]

    # segments = data["tracks"][0]["transcript"]

    # transcript = [
    #     segment
    #     for segment in segments
    #     if segment.get("text", "").strip()
    # ]
   

    #print("\n\n\n-----------------------SHSHSHSHSHSHSHSHSHSHSHSH--------------------\n\n\n")
    #print(len(clean_segments))
    #print(clean_segments)
    
    proxy_un = st.secrets.get("PROXY_UN")
    proxy_pw = st.secrets.get("PROXY_PW")


    api = YouTubeTranscriptApi(
        proxy_config=WebshareProxyConfig(
            proxy_username=proxy_un,
            proxy_password=proxy_pw,
        )
    )
    #api = YouTubeTranscriptApi()


    videoDetails = retry_on_failure(get_video_details, video_link)
    print("\n\nVideo Details")
    print(videoDetails)

    video_id = extract_video_id(video_link)
    print(f"Video ID: {video_id}")

    transcript_list = retry_on_failure(api.list, video_id)

    print(transcript_list)

    transcript = transcript_list.find_generated_transcript(["hi"])
    print("\n\n\nHHHHHHHHHHHHHH\n\n\n")
    transcript = retry_on_failure(transcript.fetch)


    # videoDetails = get_video_details(video_link)
    # print("\n\nVideo Details")
    # print(videoDetails)
    
    # video_id = extract_video_id(video_link)
    # print(f"Video ID: {video_id}")
    # transcript_list = api.list(video_id)
    
    # print(transcript_list)

    # transcript = transcript_list.find_generated_transcript(["hi"])
    # print("\n\n\nHHHHHHHHHHHHHH\n\n\n")
    # transcript = transcript.fetch()

    #fetched = transcript.fetch()
    #transcript = api.fetch(video_id, languages=["hi"])
    print("\n\n\n-----------------------SHSHSHSHSHSHSHSHSHSHSHSH--------------------\n\n\n")

    print(transcript)
    print(len(transcript))
 
    total_blocks = len(transcript)

    
    print("\n\n\n-----------------------TRANSLATED--------------------\n\n\n")
    #print(translateTranscript(transcript, videoDetails))

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



def translateTranscript(transcript, videoDetails):

    SEP = "<<<CUT>>>"
    joined_text = f" {SEP} ".join(line.text for line in transcript)


    prompt = f"""
    Translate this Hindi YouTube transcript into Hinglish.
    Keep it phonetically similar and close to meaning to the original line. Any English words used should have correct spelling.    
    Do not add extra explanation.
    Keep this separator exactly unchanged wherever it appears: <<<CUT>>>

    Hindi:
    {joined_text}

    Hinglish:
    """

    print(f"PROMPT: {prompt}")
    response = llm.invoke(prompt)

    print("Inital Translation done, now enriching the result")
    output = response.content.strip()

    prompt_enrich = f"""
    Attached below is the transcript for a youtube video that was made from the video's audio. 
    Therefore, some words especially proper nouns including names of people, places etc. could be wrong in the original transcript. So correct them if and only if you find something relevant from the video details given below.
    
    Title: {videoDetails["title"]}
    Channel Name: {videoDetails["channel"]}
    Video Description: {videoDetails["description"]}

    Do not add extra explanation.
    Keep this separator exactly unchanged wherever it appears: <<<CUT>>>

    Transcript:
    {output}
    Fixed Transcript:
    """

    response = llm.invoke(prompt_enrich)

    output2 = response.content.strip()

    diff = difflib.ndiff(output.split(), output2.split())
    print("\nCHANGES IN ENRICHMENT\n")
    print("\n".join(diff))
    

    converted_lines = output2.split(SEP)
    print("\n\n Number of lines in original, firsttranslate and fixtranslate ")
    print(f"{len(transcript)}, {len(output.split(SEP))}  , {len(converted_lines)} ")

    for line, new_text in zip(transcript, converted_lines):
        line.text = new_text.strip()
        #line["text"] = new_text.strip()
    return transcript