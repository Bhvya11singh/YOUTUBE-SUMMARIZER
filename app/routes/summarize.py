import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import AsyncOpenAI

from ..dependencies import get_openai
from ..services.transcript import (
    extract_video_id,
    fetch_transcript,
    chunk_transcript,
    needs_chunking,
    TranscriptError,
)
from ..services.summarizer import (
    summarize_direct,
    summarize_map_reduce,
)

router = APIRouter()


class SummarizeRequest(BaseModel):
    url: str


async def event_stream(
    video_id: str,
    openai_client: AsyncOpenAI,
):
    """
    Core streaming generator.
    """

    try:
        # Fetch transcript
        yield "data: [STATUS]Fetching transcript...[/STATUS]\n\n"

        segments = fetch_transcript(video_id)

        # Decide summarization strategy
        if needs_chunking(segments):
            yield "data: [STATUS]Long video detected — using map-reduce...[/STATUS]\n\n"

            chunks = chunk_transcript(segments)

            generator = summarize_map_reduce(
                chunks,
                video_id,
                openai_client,
            )

        else:
            yield "data: [STATUS]Summarizing...[/STATUS]\n\n"

            generator = summarize_direct(
                segments,
                video_id,
                openai_client,
            )

        # Stream tokens
        async for token in generator:

            if token.startswith("[STATUS]"):
                yield f"data: {token}\n\n"

            elif token.startswith("[ENRICHED]") or token.startswith("\n[ENRICHED]"):
                yield f"data: {token}\n\n"

            elif token.startswith("[ERROR]"):
                yield f"data: {token}\n\n"

            else:
                yield f"data: {token}\n\n"

        yield "data: [DONE]\n\n"

    except TranscriptError as e:
        yield f"data: [ERROR]{str(e)}[/ERROR]\n\n"

    except Exception as e:
        yield f"data: [ERROR]Unexpected error: {str(e)}[/ERROR]\n\n"


@router.post("/summarize")
async def summarize(
    req: SummarizeRequest,
    openai_client: AsyncOpenAI = Depends(get_openai),
):
    video_id = extract_video_id(req.url)

    if not video_id:
        raise HTTPException(
            status_code=422,
            detail="Could not extract a valid YouTube video ID from this URL.",
        )

    return StreamingResponse(
        event_stream(video_id, openai_client),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )