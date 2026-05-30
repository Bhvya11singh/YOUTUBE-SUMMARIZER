import json
import asyncio
from typing import AsyncIterator
from openai import AsyncOpenAI

from .transcript import TranscriptChunk, TranscriptSegment, segments_to_text


# ── prompts ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are summarizing a YouTube video transcript.
The input may be raw ASR output with no punctuation — handle it gracefully.

Return ONLY valid JSON. No markdown fences. No preamble. No explanation.

{
  "title": "concise inferred video topic (max 10 words)",
  "summary": "2-3 sentence overview, no filler phrases like 'In this video...'",
  "key_points": [
    {
      "point": "specific, actionable insight",
      "timestamp": 142
    }
  ],
  "chapters": [
    {
      "title": "chapter name (max 5 words)",
      "start": 0,
      "end": 320
    }
  ]
}

Rules:
- key_points: exactly 5-8 items
- timestamps: integers (seconds from video start)
- chapters: 3-6 items covering the full video
- summary: start with what the video actually covers, not meta-commentary
"""

CHUNK_SYSTEM_PROMPT = """Summarize this transcript section in 5 bullet points.
This is raw ASR output — no punctuation, run-on sentences are normal.
Start timestamp for this section: {start_time:.0f}s

Return ONLY valid JSON:
{{
  "bullets": ["point 1", "point 2", ...],
  "start_time": {start_time:.0f}
}}
No markdown. No preamble."""

REDUCE_SYSTEM_PROMPT = """You are given summaries of sequential sections of a YouTube video.
Combine them into a final structured summary.

Return ONLY valid JSON. No markdown fences. No preamble.

{
  "title": "concise video topic (max 10 words)",
  "summary": "2-3 sentence overview",
  "key_points": [
    {"point": "insight", "timestamp": 142}
  ],
  "chapters": [
    {"title": "chapter name", "start": 0, "end": 320}
  ]
}

Rules:
- key_points: 5-8 items, spread across the full video
- timestamps: use the section start_times to estimate accurate timestamps
- chapters: 3-6 items
"""


# ── timestamp deep-link ───────────────────────────────────────────────────────

def build_timestamp_url(video_id: str, seconds: int) -> str:
    return f"https://youtu.be/{video_id}?t={seconds}"

def enrich_with_links(result: dict, video_id: str) -> dict:
    """Add YouTube deep-links to every key_point and chapter."""
    for kp in result.get("key_points", []):
        kp["url"] = build_timestamp_url(video_id, int(kp.get("timestamp", 0)))
    for ch in result.get("chapters", []):
        ch["url"] = build_timestamp_url(video_id, int(ch.get("start", 0)))
    return result


# ── single-call path (short videos) ──────────────────────────────────────────

async def summarize_direct(
    segments: list[TranscriptSegment],
    video_id: str,
    client: AsyncOpenAI,
) -> AsyncIterator[str]:
    """
    Stream the summary for a short video directly.
    Yields raw SSE data chunks; caller wraps in event format.
    """
    transcript_text = segments_to_text(segments)

    stream = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1500,
        stream=True,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Transcript:\n{transcript_text}",
            },
        ],
    )

    buffer = ""
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            buffer += delta
            yield delta  # stream tokens as they arrive

    # After stream ends, parse + enrich and yield the enriched version
    # (client can either render streamed tokens or wait for [ENRICHED] event)
    try:
        parsed = json.loads(buffer)
        enriched = enrich_with_links(parsed, video_id)
        yield f"\n[ENRICHED]{json.dumps(enriched)}[/ENRICHED]"
    except json.JSONDecodeError:
        pass  # partial JSON — client should handle gracefully


# ── map-reduce path (long videos) ────────────────────────────────────────────

async def summarize_chunk(
    chunk: TranscriptChunk,
    client: AsyncOpenAI,
) -> dict:
    """Summarize one chunk (non-streaming, called in parallel)."""
    prompt = CHUNK_SYSTEM_PROMPT.format(start_time=chunk.start_time)

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",  # cheaper for map step
        max_tokens=400,
        stream=False,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": chunk.text},
        ],
    )

    raw = resp.choices[0].message.content.strip()
    # strip accidental markdown fences
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # fallback: return raw text so reduce step still has something
        return {"bullets": [raw], "start_time": chunk.start_time}


async def summarize_map_reduce(
    chunks: list[TranscriptChunk],
    video_id: str,
    client: AsyncOpenAI,
) -> AsyncIterator[str]:
    """
    Map: summarize all chunks in parallel.
    Reduce: merge summaries into final JSON, then stream it.
    """
    # Map step — all chunks run concurrently
    yield "[STATUS]Summarizing sections in parallel...[/STATUS]"

    chunk_summaries = await asyncio.gather(
        *[summarize_chunk(c, client) for c in chunks]
    )

    yield f"[STATUS]Combining {len(chunks)} sections...[/STATUS]"

    # Reduce step — stream the final merge
    reduce_input = json.dumps(chunk_summaries, indent=2)

    stream = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1500,
        stream=True,
        messages=[
            {"role": "system", "content": REDUCE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Section summaries:\n{reduce_input}",
            },
        ],
    )

    buffer = ""
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            buffer += delta
            yield delta

    try:
        parsed = json.loads(buffer)
        enriched = enrich_with_links(parsed, video_id)
        yield f"\n[ENRICHED]{json.dumps(enriched)}[/ENRICHED]"
    except json.JSONDecodeError:
        pass