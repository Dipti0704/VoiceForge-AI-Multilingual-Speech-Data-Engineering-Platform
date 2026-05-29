import re


DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
ENGLISH_RE = re.compile(r"[a-zA-Z]")
HINGLISH_HINTS = {
    "mujhe",
    "mera",
    "karna",
    "hai",
    "nahi",
    "kya",
    "order",
    "cancel",
    "please",
}


class LanguageDetectionService:
    def detect(self, text: str) -> str:
        has_devanagari = bool(DEVANAGARI_RE.search(text))
        has_english = bool(ENGLISH_RE.search(text))
        tokens = {token.lower() for token in text.split()}
        has_hinglish = bool(tokens & HINGLISH_HINTS)

        if has_devanagari and has_english:
            return "Hindi-English"
        if has_hinglish:
            return "Hindi-English"
        if has_devanagari:
            return "Hindi"
        if has_english:
            return "English"
        return "unknown"

