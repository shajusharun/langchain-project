from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from youtube_transcript_api import YouTubeTranscriptApi

video_id = "6fhFI8o3PPQ"

api = YouTubeTranscriptApi()

transcript = api.fetch(video_id, languages=["hi"])

for line in transcript:
    print(line.start)
    print(line.duration)
    print(line.text)

# load_dotenv()

# llm = ChatOpenAI(model="gpt-4.1-mini", max_completion_tokens=20)

# response = llm.invoke("What is lang chain?", )

# print(response.content)