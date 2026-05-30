from pathlib import Path

from app.core.config import get_settings


class TranscriptionService:
    """Whisper-ready transcription interface with a deterministic local fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._model = None

    def transcribe(self, audio_path: Path) -> tuple[str, float, str | None]:
        if self.settings.enable_whisper:
            return self._transcribe_with_whisper(audio_path)

        stem = audio_path.stem.replace("_", " ").replace("-", " ")
        fallback = f"transcript pending for {stem}"
        fallback_reason = "Whisper is disabled in backend settings; using fallback transcript."
        return fallback, 0.35, fallback_reason

    def _transcribe_with_whisper(self, audio_path: Path) -> tuple[str, float, str | None]:
        try:
            import whisper
        except ImportError as exc:
            raise RuntimeError("Install backend[ml] to enable Whisper transcription.") from exc

        if self._model is None:
            self._model = whisper.load_model("base")

        result = self._model.transcribe(str(audio_path))
        text = str(result.get("text", "")).strip()
        segments = result.get("segments", [])
        confidences = [1.0 - float(segment.get("no_speech_prob", 0.0)) for segment in segments]
        confidence = sum(confidences) / len(confidences) if confidences else 0.7
        return text, round(max(0.0, min(1.0, confidence)), 3), None

