
import sys
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

DEFAULT_VIDEO_ID = "6fhFI8o3PPQ"

video_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VIDEO_ID

api = YouTubeTranscriptApi()
transcript = api.fetch(video_id, languages=["hi"])

llm = ChatOpenAI(model="gpt-4.1-mini")



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



def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)

    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"



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




numberOfLines = 0
previous_line_ended_with_full_stop = True

with open("hinglish_transcript.srt", "w", encoding="utf-8") as file:
    for index, line in enumerate(transcript, start=1):
        numberOfLines += 1
        hinglish_text = translate_to_hinglish(line.text)

        hinglish_text = fix_capitalization(
            hinglish_text,
            previous_line_ended_with_full_stop
        )

        start_time = format_srt_time(line.start)
        end_time = format_srt_time(line.start + line.duration)

        file.write(f"{index}\n")
        file.write(f"{start_time} --> {end_time}\n")
        file.write(f"{hinglish_text}\n\n")

        previous_line_ended_with_full_stop = hinglish_text.endswith(".")

        print(index)
        print(f"{start_time} --> {end_time}")
        print(hinglish_text)
        print("-" * 50)
        #if(numberOfLines == 20):
        #    break


# with open("hinglish_transcript.srt", "w", encoding="utf-8") as file:
#     for index, line in enumerate(transcript, start=1):
#         numberOfLines += 1
#         hinglish_text = translate_to_hinglish(line.text)

#         start_time = format_srt_time(line.start)
#         end_time = format_srt_time(line.start + line.duration)

#         file.write(f"{index}\n")
#         file.write(f"{start_time} --> {end_time}\n")
#         file.write(f"{hinglish_text}\n\n")

#         print(f"{index}")
#         print(f"{start_time} --> {end_time}")
#         print(hinglish_text)
#         print("-" * 50)
#         if(numberOfLines == 10):
#             break

print("SRT file saved as hinglish_transcript.srt")
