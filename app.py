import mimetypes
import os
from functools import lru_cache
from hmac import compare_digest
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

MODEL_NAME = "gemini-3.5-flash"
API_KEY = "7DJBK_iHnZpoNzdtHmuodHaF0bUhLddPuxX01qrbEdE"
MAX_AUDIO_SIZE = 10 * 1024 * 1024

app = FastAPI(title="Remote ASR")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class TranscriptionResponse(BaseModel):
    transcription: str


def require_api_key(
    supplied_key: Annotated[str | None, Depends(api_key_header)],
) -> None:
    if supplied_key is None or not compare_digest(supplied_key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


@lru_cache
def get_agent() -> Agent:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    model = GoogleModel(
        MODEL_NAME,
        provider=GoogleProvider(api_key=gemini_api_key),
    )
    return Agent(model)


@app.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    dependencies=[Depends(require_api_key)],
)
async def transcribe(
    audio: Annotated[UploadFile, File(description="Audio file to transcribe")],
) -> TranscriptionResponse:
    media_type = audio.content_type or mimetypes.guess_type(audio.filename or "")[0]
    if media_type is None or not media_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The uploaded file must be audio",
        )

    data = await audio.read(MAX_AUDIO_SIZE + 1)
    await audio.close()

    if not data:
        raise HTTPException(status_code=400, detail="The uploaded audio file is empty")
    if len(data) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=413, detail="Audio file exceeds the 10 MiB limit")

    result = await get_agent().run(
        [
            (
                "Transcribe this audio verbatim. Preserve the spoken language and add "
                "punctuation where clear. Return only the transcription."
            ),
            BinaryContent(data=data, media_type=media_type),
        ]
    )
    return TranscriptionResponse(transcription=result.output.strip())
