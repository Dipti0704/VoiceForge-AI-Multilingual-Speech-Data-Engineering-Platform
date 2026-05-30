from app.services.cleaning import TextCleaningService
from app.services.language import LanguageDetectionService
from app.services.quality import QualityScoringService
from app.services.transcription import TranscriptionService


def test_hinglish_cleaning_normalizes_common_noise() -> None:
    cleaner = TextCleaningService()

    assert cleaner.normalize("muje mera order cancl krna h bro") == "Mujhe mera order cancel karna hai"


def test_language_detection_identifies_hinglish() -> None:
    detector = LanguageDetectionService()

    assert detector.detect("Mujhe order cancel karna hai") == "Hindi-English"


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

