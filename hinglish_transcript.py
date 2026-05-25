from youtube_transcript_api import YouTubeTranscriptApi
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

video_id = "6fhFI8o3PPQ"

api = YouTubeTranscriptApi()
transcript = api.fetch(video_id, languages=["hi"])

llm = ChatOpenAI(model="gpt-4.1-mini")

def translate_to_hinglish(text):
    prompt = f"""
Translate this Hindi YouTube transcript line into Hinglish.
Keep it phonetically similar. Use punctuations according to the original line. 
Start the line with capital letter only if it is the the start of the sentence or after a full stop.
Do not add extra explanation.

Hindi:
{text}

Hinglish:
"""
    response = llm.invoke(prompt)
    return response.content.strip()

i=0
with open("hinglish_transcript.txt", "w", encoding="utf-8") as file:
    
    for line in transcript:
        i= i+1
        hinglish_text = translate_to_hinglish(line.text)

        file.write(f"[{line.start:.2f}s - {line.start + line.duration:.2f}s]\n")
        file.write(f"Hindi: {line.text}\n")
        file.write(f"Hinglish: {hinglish_text}\n\n")

        print(f"Hindi: {line.text}")
        print(f"Hinglish: {hinglish_text}")

        print(f"Done: {line.start:.2f}s")
        if(i==10):
            break

print("Hinglish transcript saved to hinglish_transcript.txt")
