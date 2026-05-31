from pathlib import Path

from app.core.config import get_settings


class TranscriptionService:
    """OpenAI transcription interface with a deterministic local fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def transcribe(self, audio_path: Path) -> tuple[str, float, str | None]:
        if self.settings.enable_whisper:
            return self._transcribe_with_openai(audio_path)

        stem = audio_path.stem.replace("_", " ").replace("-", " ")
        fallback = f"transcript pending for {stem}"
        fallback_reason = "OpenAI transcription is disabled in backend settings; using fallback transcript."
        return fallback, 0.35, fallback_reason

    def _transcribe_with_openai(self, audio_path: Path) -> tuple[str, float, str | None]:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when ENABLE_WHISPER=true.")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the openai package to enable API transcription.") from exc

        client = OpenAI(api_key=self.settings.openai_api_key)
        with audio_path.open("rb") as audio_file:
            result = client.audio.transcriptions.create(
                model=self.settings.transcription_model,
                file=audio_file,
            )

        text = str(getattr(result, "text", "")).strip()
        if not text:
            raise RuntimeError("OpenAI transcription returned an empty transcript.")

        note = f"Transcribed with OpenAI model {self.settings.transcription_model}."
        return text, 0.85, note
