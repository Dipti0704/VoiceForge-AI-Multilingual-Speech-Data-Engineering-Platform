from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import AudioRecord, RecordStatus
from app.schemas import AudioRecordRead, MetricsRead, TranscriptCreate
from app.services.exporter import DatasetExporter
from app.services.pipeline import SpeechDataPipeline

router = APIRouter()
pipeline = SpeechDataPipeline()
exporter = DatasetExporter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/audio/upload", response_model=AudioRecordRead)
async def upload_audio(file: UploadFile = File(...), db: Session = Depends(get_db)) -> AudioRecord:
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required.")

    settings = get_settings()
    suffix = Path(file.filename).suffix or ".wav"
    target = settings.upload_dir / f"{uuid4().hex}{suffix}"

    content = await file.read()
    target.write_bytes(content)
    return pipeline.process_audio(db, target, source=file.filename)


@router.post("/records/transcript", response_model=AudioRecordRead)
def create_transcript(payload: TranscriptCreate, db: Session = Depends(get_db)) -> AudioRecord:
    return pipeline.process_transcript(
        db=db,
        raw_transcript=payload.raw_transcript,
        confidence=payload.confidence,
        source=payload.source,
    )


@router.get("/records", response_model=list[AudioRecordRead])
def list_records(
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=250),
    db: Session = Depends(get_db),
) -> list[AudioRecord]:
    query = db.query(AudioRecord).order_by(AudioRecord.created_at.desc())
    if status:
        query = query.filter(AudioRecord.status == status)
    return query.limit(limit).all()


@router.get("/metrics", response_model=MetricsRead)
def metrics(db: Session = Depends(get_db)) -> MetricsRead:
    total = db.query(func.count(AudioRecord.id)).scalar() or 0
    processed = db.query(func.count(AudioRecord.id)).filter(AudioRecord.status == RecordStatus.processed.value).scalar() or 0
    review = db.query(func.count(AudioRecord.id)).filter(AudioRecord.status == RecordStatus.review.value).scalar() or 0
    duplicate = db.query(func.count(AudioRecord.id)).filter(AudioRecord.status == RecordStatus.duplicate.value).scalar() or 0
    average = db.query(func.avg(AudioRecord.quality_score)).scalar() or 0
    return MetricsRead(
        total_records=total,
        processed_records=processed,
        review_records=review,
        duplicate_records=duplicate,
        average_quality=round(float(average), 2),
    )


@router.get("/datasets/export")
def export_dataset(
    format: str = Query(default="jsonl", pattern="^(jsonl|csv)$"),
    min_quality: int = Query(default=70, ge=0, le=100),
    db: Session = Depends(get_db),
) -> Response:
    media_type, content = exporter.export(db, file_format=format, min_quality=min_quality)
    extension = "csv" if format == "csv" else "jsonl"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=voiceforge_train.{extension}"},
    )

