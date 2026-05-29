from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RecordStatus(str, Enum):
    processed = "processed"
    review = "review"
    duplicate = "duplicate"
    failed = "failed"


class AudioRecord(Base):
    __tablename__ = "audio_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(255), default="manual")
    audio_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_transcript: Mapped[str] = mapped_column(Text)
    clean_transcript: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(80), default="unknown")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_of_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default=RecordStatus.processed.value)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

