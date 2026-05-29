import re
import unicodedata


ABBREVIATIONS = {
    "muje": "mujhe",
    "mujy": "mujhe",
    "mera": "mera",
    "cancl": "cancel",
    "cncl": "cancel",
    "krna": "karna",
    "kr": "kar",
    "h": "hai",
    "haii": "hai",
    "plz": "please",
    "pls": "please",
    "ordr": "order",
    "bro": "",
}


class TextCleaningService:
    def normalize(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = text.lower().strip()
        text = re.sub(r"\[[^\]]+\]|\([^\)]+\)", " ", text)
        text = re.sub(r"[^a-zA-Z0-9\u0900-\u097F\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        tokens = [ABBREVIATIONS.get(token, token) for token in text.split()]
        cleaned = " ".join(token for token in tokens if token)
        return cleaned[:1].upper() + cleaned[1:] if cleaned else ""

