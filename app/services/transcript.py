import re
from dataclasses import dataclass
from typing import Any

import tiktoken
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
)


def extract_video_id(url_or_id: str) -> str | None:
    value = url_or_id.strip()

    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value

    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)

    return None


@dataclass
class TranscriptSegment:
    text: str
    start: float
    duration: float


@dataclass
class TranscriptChunk:
    text: str
    start_time: float
    end_time: float


class TranscriptError(Exception):
    pass


def _snippet_value(snippet: Any, key: str) -> Any:
    if isinstance(snippet, dict):
        return snippet[key]

    return getattr(snippet, key)


def fetch_transcript(
    url_or_video_id: str,
    languages: list[str] | None = None,
) -> list[TranscriptSegment]:
    video_id = extract_video_id(url_or_video_id)

    if not video_id:
        raise TranscriptError("Invalid YouTube URL or video ID.")

    try:
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id, languages=languages or ["en"])

        segments: list[TranscriptSegment] = []

        for snippet in fetched_transcript:
            text = str(_snippet_value(snippet, "text")).strip()

            if text:
                segments.append(
                    TranscriptSegment(
                        text=text,
                        start=float(_snippet_value(snippet, "start")),
                        duration=float(_snippet_value(snippet, "duration")),
                    )
                )

        if not segments:
            raise TranscriptError("Transcript loaded, but it did not contain text.")

        return segments

    except TranscriptsDisabled as exc:
        raise TranscriptError("Transcripts are disabled for this video.") from exc
    except NoTranscriptFound as exc:
        raise TranscriptError(
            "No transcript was found for the requested language. Try another language code."
        ) from exc
    except VideoUnavailable as exc:
        raise TranscriptError("This video is unavailable or private.") from exc
    except RequestBlocked as exc:
        raise TranscriptError(
            "YouTube blocked the request. This often happens on cloud/server IPs or after too many requests."
        )