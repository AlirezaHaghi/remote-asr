from pydantic import BaseModel
class TranscriptionResult(BaseModel):
    transcription: str
    accent: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    accent_confidence: float | None = Field(default=None, ge=0, le=1)
