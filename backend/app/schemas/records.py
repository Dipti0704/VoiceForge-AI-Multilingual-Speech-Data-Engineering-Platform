from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TranscriptCreate(BaseModel):
    source: str = "manual"
    raw_transcript: str = Field(min_length=1)
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)


class ReviewUpdate(BaseModel):
    action: Literal["approve", "reject"] = "approve"
    corrected_transcript: str | None = Field(default=None, min_length=1)
    review_note: str | None = None


class AudioRecordRead(BaseModel):
    id: int
    source: str
    audio_path: str | None
    raw_transcript: str
    clean_transcript: str
    language: str
    confidence: float
    quality_score: int
    duplicate_of_id: int | None
    status: str
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricsRead(BaseModel):
    total_records: int
    processed_records: int
    review_records: int
    duplicate_records: int
    average_quality: float
