import re
from collections import Counter

from app.core.config import get_settings


SCRIPT_PATTERNS = {
    "Hindi": re.compile(r"[\u0900-\u097F]"),
    "Bengali": re.compile(r"[\u0980-\u09FF]"),
    "Punjabi": re.compile(r"[\u0A00-\u0A7F]"),
    "Gujarati": re.compile(r"[\u0A80-\u0AFF]"),
    "Tamil": re.compile(r"[\u0B80-\u0BFF]"),
    "Telugu": re.compile(r"[\u0C00-\u0C7F]"),
    "Kannada": re.compile(r"[\u0C80-\u0CFF]"),
    "Malayalam": re.compile(r"[\u0D00-\u0D7F]"),
    "Arabic": re.compile(r"[\u0600-\u06FF]"),
    "Chinese": re.compile(r"[\u4E00-\u9FFF]"),
    "Japanese": re.compile(r"[\u3040-\u30FF]"),
    "Korean": re.compile(r"[\uAC00-\uD7AF]"),
    "Russian": re.compile(r"[\u0400-\u04FF]"),
}

LATIN_RE = re.compile(r"[a-zA-Z]")
TOKEN_RE = re.compile(r"[a-zA-Z]+")

HINGLISH_HINTS = {
    "aap",
    "cancel",
    "chahiye",
    "din",
    "haan",
    "hai",
    "kar",
    "karna",
    "kya",
    "mera",
    "mujhe",
    "nahi",
    "order",
    "please",
    "se",
}

LATIN_LANGUAGE_HINTS = {
    "English": {
        "a",
        "and",
        "are",
        "cancel",
        "for",
        "hello",
        "i",
        "is",
        "my",
        "order",
        "please",
        "refund",
        "the",
        "to",
        "want",
    },
    "Spanish": {"cancelar", "de", "el", "hola", "la", "mi", "pedido", "por", "quiero"},
    "French": {"annuler", "bonjour", "commande", "de", "je", "ma", "mon", "veux"},
    "German": {"bestellung", "die", "ich", "meine", "mochte", "stornieren", "und"},
    "Italian": {"annullare", "ciao", "il", "mio", "ordine", "voglio"},
    "Portuguese": {"cancelar", "meu", "ola", "pedido", "quero"},
}

FASTTEXT_LABELS = {
    "ar": "Arabic",
    "bn": "Bengali",
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "gu": "Gujarati",
    "hi": "Hindi",
    "it": "Italian",
    "ja": "Japanese",
    "kn": "Kannada",
    "ko": "Korean",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "pt": "Portuguese",
    "ru": "Russian",
    "ta": "Tamil",
    "te": "Telugu",
    "ur": "Urdu",
    "zh": "Chinese",
}


class LanguageDetectionService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._model = None
        self._model_load_failed = False

    def detect(self, text: str) -> str:
        normalized = text.lower()
        tokens = set(TOKEN_RE.findall(normalized))
        script_hits = self._detect_scripts(text)
        has_latin = bool(LATIN_RE.search(text))
        has_hinglish = bool(tokens & HINGLISH_HINTS)

        if "Hindi" in script_hits and has_latin:
            return "Hindi-English"
        if has_hinglish:
            return "Hindi-English"

        fasttext_language = self._detect_with_fasttext(text)
        if fasttext_language:
            return fasttext_language

        if len(script_hits) > 1:
            return "Multilingual"
        if script_hits:
            return script_hits[0]
        if has_latin:
            return self._detect_latin_language(tokens)
        return "unknown"

    def _detect_scripts(self, text: str) -> list[str]:
        scores = Counter(
            language
            for language, pattern in SCRIPT_PATTERNS.items()
            for _ in pattern.finditer(text)
        )
        return [language for language, _ in scores.most_common()]

    def _detect_latin_language(self, tokens: set[str]) -> str:
        scores = {language: len(tokens & hints) for language, hints in LATIN_LANGUAGE_HINTS.items()}
        language, score = max(scores.items(), key=lambda item: item[1])
        return language if score else "English"

    def _detect_with_fasttext(self, text: str, min_confidence: float = 0.45) -> str | None:
        model = self._load_fasttext_model()
        if model is None or not text.strip():
            return None

        labels, scores = model.predict(text.replace("\n", " "), k=1)
        if not labels or not scores or float(scores[0]) < min_confidence:
            return None

        code = labels[0].replace("__label__", "")
        return FASTTEXT_LABELS.get(code, code)

    def _load_fasttext_model(self):
        if not self.settings.enable_fasttext_language or self._model_load_failed:
            return self._model
        if self._model is not None:
            return self._model
        if not self.settings.fasttext_language_model_path.exists():
            self._model_load_failed = True
            return None

        try:
            import fasttext
        except ImportError:
            self._model_load_failed = True
            return None

        self._model = fasttext.load_model(str(self.settings.fasttext_language_model_path))
        return self._model
