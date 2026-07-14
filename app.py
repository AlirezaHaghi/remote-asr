import mimetypes
import os
from functools import lru_cache
from hmac import compare_digest
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from pydantic_ai import Agent, BinaryContent

load_dotenv()

MODEL_NAME = "gemini-3.5-flash"
API_KEY = "7DJBK_iHnZpoNzdtHmuodHaF0bUhLddPuxX01qrbEdE"
MAX_AUDIO_SIZE = 10 * 1024 * 1024

app = FastAPI(title="Remote ASR")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class TranscriptionResult(BaseModel):
    transcription: str
    accent: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    accent_confidence: float | None = Field(default=None, ge=0, le=1)


def require_api_key(
    supplied_key: Annotated[str | None, Depends(api_key_header)],
) -> None:
    if supplied_key is None or not compare_digest(supplied_key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


def get_transcription(audio: UploadFile):
    agent = Agent(
        model="google:gemini-3.5-flash",
        output_type=TranscriptionResult,
        system_prompt="you are an ASR-ATC project",
    )

    result = agent.run_sync(
        [
            "you are given and ATC audio file. transcribe it. accuracy is very important."
            "don't seperate pilot and controller. include all of them in one result."
            "unforgivable thing is when you add something to the transcript that is not in the audio"
            "also return accent(don't say non native say nationality for example say Arabic) and confidence (a number from 0 to 1) of the transcript based on output model",
            BinaryContent(data=audio.file.read(), media_type="audio/wav"),
        ]
    )

    return result.output


@app.post(
    "/transcribe",
    response_model=TranscriptionResult,
    dependencies=[Depends(require_api_key)],
)
async def transcribe(
    audio: Annotated[UploadFile, File(description="Audio file to transcribe")],
) -> TranscriptionResult:
    return get_transcription(audio)
