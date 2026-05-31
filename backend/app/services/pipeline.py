from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import AudioRecord, RecordStatus
from app.services.cleaning import TextCleaningService
from app.services.deduplication import DeduplicationService
from app.services.language import LanguageDetectionService
from app.services.quality import QualityScoringService
from app.services.transcription import TranscriptionService


class SpeechDataPipeline:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.transcription = TranscriptionService()
        self.cleaning = TextCleaningService()
        self.language = LanguageDetectionService()
        self.deduplication = DeduplicationService()
        self.quality = QualityScoringService()

    def process_audio(self, db: Session, audio_path: Path, source: str = "upload") -> AudioRecord:
        raw_text, confidence, transcription_note = self.transcription.transcribe(audio_path)
        return self.process_transcript(
            db=db,
            raw_transcript=raw_text,
            confidence=confidence,
            source=source,
            audio_path=str(audio_path),
            transcription_note=transcription_note,
        )

    def process_transcript(
        self,
        db: Session,
        raw_transcript: str,
        confidence: float,
        source: str = "manual",
        audio_path: str | None = None,
        transcription_note: str | None = None,
    ) -> AudioRecord:
        clean_text = self.cleaning.normalize(raw_transcript)
        language = self.language.detect(clean_text)
        duplicate = self.deduplication.find_duplicate(db, clean_text)
        quality_score, issues = self.quality.score(
            raw_text=raw_transcript,
            clean_text=clean_text,
            confidence=confidence,
            language=language,
            duplicate_risk=duplicate is not None,
        )

        if duplicate:
            status = RecordStatus.duplicate.value
        elif quality_score < self.settings.review_quality_threshold:
            status = RecordStatus.review.value
        else:
            status = RecordStatus.processed.value

        notes = list(issues)
        if transcription_note:
            notes.insert(0, transcription_note)

        record = AudioRecord(
            source=source,
            audio_path=audio_path,
            raw_transcript=raw_transcript,
            clean_transcript=clean_text,
            language=language,
            confidence=confidence,
            quality_score=quality_score,
            duplicate_of_id=duplicate.id if duplicate else None,
            status=status,
            notes=", ".join(notes) if notes else None,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def review_record(
        self,
        db: Session,
        record_id: int,
        action: str,
        corrected_transcript: str | None = None,
        review_note: str | None = None,
    ) -> AudioRecord | None:
        record = db.get(AudioRecord, record_id)
        if record is None:
            return None

        notes: list[str] = []
        if record.notes:
            notes.append(record.notes)

        if action == "reject":
            record.status = RecordStatus.failed.value
            if review_note:
                notes.append(f"review rejected: {review_note}")
            else:
                notes.append("review rejected by human reviewer")
            record.notes = ", ".join(notes)
            db.commit()
            db.refresh(record)
            return record

        reviewed_text = corrected_transcript or record.clean_transcript
        clean_text = self.cleaning.normalize(reviewed_text)
        language = self.language.detect(clean_text)
        duplicate = self.deduplication.find_duplicate(db, clean_text, exclude_id=record.id)
        review_confidence = max(record.confidence, 0.95)
        quality_score, issues = self.quality.score(
            raw_text=record.raw_transcript,
            clean_text=clean_text,
            confidence=review_confidence,
            language=language,
            duplicate_risk=duplicate is not None,
        )

        record.clean_transcript = clean_text
        record.language = language
        record.confidence = review_confidence
        record.quality_score = quality_score
        record.duplicate_of_id = duplicate.id if duplicate else None
        record.status = RecordStatus.duplicate.value if duplicate else RecordStatus.processed.value

        notes.append("human reviewed and approved")
        if review_note:
            notes.append(f"review note: {review_note}")
        notes.extend(issues)
        record.notes = ", ".join(notes)

        db.commit()
        db.refresh(record)
        return record
