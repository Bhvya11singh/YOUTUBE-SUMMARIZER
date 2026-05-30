from youtube_transcript_api import YouTubeTranscriptApi

video_id = "jNQXAC9IVRw"

try:
    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    print("SUCCESS")
    print(transcript[:5])

except Exception as e:
    print("ERROR:")
    print(repr(e))