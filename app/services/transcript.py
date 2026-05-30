import ssl
import re

ssl._create_default_https_context = ssl._create_unverified_context
from dataclasses import dataclass

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

import tiktoken


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
    ]

    for pat in patterns:
        match = re.search(pat, url)

        if match:
            return match.group(1)

    return None


# ─────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────

class TranscriptError(Exception):
    pass


# ─────────────────────────────────────────────
# Fetch transcript
# ─────────────────────────────────────────────

def fetch_transcript(video_id: str) -> list[TranscriptSegment]:

    try:
        print(f"Fetching transcript for: {video_id}")

        fetched_transcript = YouTubeTranscriptApi.get_transcript(video_id)

        segments = []

        for seg in fetched_transcript:

            text = seg["text"]

            if text:
                segments.append(
                    TranscriptSegment(
                        text=text,
                        start=seg["start"],
                        duration=seg["duration"],
                    )
                )

        print(f"Loaded {len(segments)} transcript segments")

        return segments

    except Exception as e:

        print("FULL ERROR:", repr(e))

        error_text = str(e)

        if "429" in error_text:
            raise TranscriptError("YouTube rate-limited requests. Wait a few minutes.")

        if "SSL" in error_text:
            raise TranscriptError("SSL connection issue while contacting YouTube.")

        raise TranscriptError(f"Failed to fetch transcript: {error_text}")


# ─────────────────────────────────────────────
# Token helpers
# ─────────────────────────────────────────────

CHUNK_TOKEN_LIMIT = 3000
CONTEXT_TOKEN_LIMIT = 14000


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def segments_to_text(
    segments: list[TranscriptSegment]
) -> str:

    return " ".join(s.text for s in segments)


# ─────────────────────────────────────────────
# Chunking
# ─────────────────────────────────────────────

def chunk_transcript(
    segments: list[TranscriptSegment],
    max_tokens: int = CHUNK_TOKEN_LIMIT,
) -> list[TranscriptChunk]:

    enc = tiktoken.encoding_for_model("gpt-4o-mini")

    chunks = []

    current = []

    current_tokens = 0

    for seg in segments:

        seg_tokens = len(enc.encode(seg.text))

        if current_tokens + seg_tokens > max_tokens and current:

            chunks.append(
                TranscriptChunk(
                    text=segments_to_text(current),
                    start_time=current[0].start,
                    end_time=current[-1].start + current[-1].duration,
                )
            )

            current = current[-2:]

            current_tokens = sum(
                len(enc.encode(s.text))
                for s in current
            )

        current.append(seg)

        current_tokens += seg_tokens

    if current:
        chunks.append(
            TranscriptChunk(
                text=segments_to_text(current),
                start_time=current[0].start,
                end_time=current[-1].start + current[-1].duration,
            )
        )

    return chunks


def needs_chunking(
    segments: list[TranscriptSegment],
) -> bool:

    total_text = segments_to_text(segments)

    return count_tokens(total_text) > CONTEXT_TOKEN_LIMIT