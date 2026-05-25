import sys
import requests

url = sys.argv[1]


response = requests.post(
  "https://www.youtube-transcript.io/api/transcripts",
  headers={
  "Authorization": "Basic 6a141ab7020bd93fbc31f06e", 
  "Content-Type": "application/json"},
  json={"ids": ["eBSLhYnDXXM"]}
)


print("Status:", response.status_code)
print("Response:", response.text)