from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models import AudioRecord
from app.services.cleaning import TextCleaningService
from app.services.language import LanguageDetectionService
from app.services.pipeline import SpeechDataPipeline
from app.services.quality import QualityScoringService
from app.services.transcription import TranscriptionService


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_hinglish_cleaning_normalizes_common_noise() -> None:
    cleaner = TextCleaningService()

    assert cleaner.normalize("muje mera order cancl krna h bro") == "Mujhe mera order cancel karna hai"


def test_cleaning_normalizes_structured_entities_and_code_mix() -> None:
    cleaner = TextCleaningService()

    cleaned = cleaner.normalize(
        "umm mera order 2 din se pending hai, plz mail test.user@gmail.com ya call 9876543210"
    )

    assert cleaned == (
        "Mera order two din se pending hai please mail email address ya call phone number"
    )


def test_cleaning_normalizes_currency_urls_and_repeated_noise() -> None:
    cleaner = TextCleaningService()

    cleaned = cleaner.normalize("refund ₹500 chahiye yaar, check www.example.com haiiii")

    assert cleaned == "Refund five hundred rupees chahiye check website link hai"


def test_language_detection_identifies_hinglish() -> None:
    detector = LanguageDetectionService()

    assert detector.detect("Mujhe order cancel karna hai") == "Hindi-English"


def test_language_detection_identifies_multiple_scripts_and_latin_languages() -> None:
    detector = LanguageDetectionService()

    assert detector.detect("मुझे मेरा ऑर्डर कैंसल करना है") == "Hindi"
    assert detector.detect("எனக்கு ஆர்டர் ரத்து செய்ய வேண்டும்") == "Tamil"
    assert detector.detect("Je veux annuler ma commande") == "French"
    assert detector.detect("Quiero cancelar mi pedido") == "Spanish"


def test_language_detection_uses_fasttext_when_available() -> None:
    class FakeFastTextModel:
        def predict(self, text: str, k: int = 1):
            return ["__label__fr"], [0.93]

    detector = LanguageDetectionService()
    detector._model = FakeFastTextModel()

    assert detector.detect("texte sans mots indices") == "French"


def test_quality_scoring_routes_low_confidence_for_review() -> None:
    scorer = QualityScoringService()

    score, issues = scorer.score(
        raw_text="cancl",
        clean_text="cancel",
        confidence=0.2,
        language="English",
        duplicate_risk=False,
    )

    assert score < 60
    assert "low transcription confidence" in issues


def test_transcription_fallback_reports_reason() -> None:
    service = TranscriptionService()
    service.settings.enable_whisper = False

    text, confidence, note = service.transcribe(Path("call_001.wav"))

    assert text == "transcript pending for call 001"
    assert confidence == 0.35
    assert note is not None
    assert "fallback transcript" in note


def test_review_approval_promotes_corrected_record(db_session) -> None:
    pipeline = SpeechDataPipeline()
    record = AudioRecord(
        source="test",
        raw_transcript="cancl",
        clean_transcript="cancl",
        language="English",
        confidence=0.2,
        quality_score=40,
        status="review",
        notes="low transcription confidence",
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    reviewed = pipeline.review_record(
        db=db_session,
        record_id=record.id,
        action="approve",
        corrected_transcript="mujhe order cancel karna hai",
    )

    assert reviewed is not None
    assert reviewed.status == "processed"
    assert reviewed.clean_transcript == "Mujhe order cancel karna hai"
    assert reviewed.language == "Hindi-English"
    assert reviewed.confidence == 0.95
    assert reviewed.notes is not None
    assert "human reviewed and approved" in reviewed.notes
