import re
import unicodedata


EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+|\b[a-z0-9-]+\.(?:com|in|org|net|ai|io)\S*\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
CURRENCY_RE = re.compile(
    r"(?:(?P<prefix>rs\.?|inr|\u20b9|\$)\s*(?P<prefix_amount>\d[\d,]*(?:\.\d+)?)|"
    r"(?P<suffix_amount>\d[\d,]*(?:\.\d+)?)\s*(?P<suffix>rs\.?|inr|rupees?|dollars?))",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"\b\d+\b")
REPEATED_ALPHA_RE = re.compile(r"([a-zA-Z])\1{2,}")


ABBREVIATIONS = {
    "muje": "mujhe",
    "mujy": "mujhe",
    "mje": "mujhe",
    "mjhe": "mujhe",
    "mera": "mera",
    "mra": "mera",
    "cancl": "cancel",
    "cncl": "cancel",
    "cancle": "cancel",
    "krna": "karna",
    "kr": "kar",
    "kro": "karo",
    "kardo": "kar do",
    "h": "hai",
    "haii": "hai",
    "nhi": "nahi",
    "nai": "nahi",
    "plz": "please",
    "pls": "please",
    "ordr": "order",
    "odr": "order",
    "bro": "",
    "yaar": "",
    "yr": "",
    "btw": "",
    "ok": "okay",
    "thx": "thanks",
    "tnx": "thanks",
}

FILLER_WORDS = {
    "ah",
    "aah",
    "basically",
    "erm",
    "hmm",
    "like",
    "umm",
    "um",
    "uh",
    "uhh",
}

ONES = {
    0: "zero",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    14: "fourteen",
    15: "fifteen",
    16: "sixteen",
    17: "seventeen",
    18: "eighteen",
    19: "nineteen",
}

TENS = {
    20: "twenty",
    30: "thirty",
    40: "forty",
    50: "fifty",
    60: "sixty",
    70: "seventy",
    80: "eighty",
    90: "ninety",
}


class TextCleaningService:
    def normalize(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = text.lower().strip()
        text = EMAIL_RE.sub(" email address ", text)
        text = URL_RE.sub(" website link ", text)
        text = PHONE_RE.sub(" phone number ", text)
        text = CURRENCY_RE.sub(self._normalize_currency, text)
        text = NUMBER_RE.sub(lambda match: self._number_to_words(int(match.group(0))), text)
        text = REPEATED_ALPHA_RE.sub(r"\1\1", text)
        text = re.sub(r"\[[^\]]+\]|\([^\)]+\)", " ", text)
        text = re.sub(r"[^a-zA-Z0-9\u0900-\u097F\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        tokens = []
        for token in text.split():
            if token in FILLER_WORDS:
                continue
            replacement = ABBREVIATIONS.get(token, token)
            tokens.extend(replacement.split())

        cleaned = " ".join(token for token in tokens if token)
        return cleaned[:1].upper() + cleaned[1:] if cleaned else ""

    def _normalize_currency(self, match: re.Match[str]) -> str:
        amount = match.group("prefix_amount") or match.group("suffix_amount") or "0"
        marker = match.group("prefix") or match.group("suffix") or "rupees"
        whole_amount = int(float(amount.replace(",", "")))
        currency = "dollars" if marker == "$" or "dollar" in marker.lower() else "rupees"
        return f" {self._number_to_words(whole_amount)} {currency} "

    def _number_to_words(self, number: int) -> str:
        if number < 20:
            return ONES[number]
        if number < 100:
            tens, remainder = divmod(number, 10)
            words = TENS[tens * 10]
            return f"{words} {ONES[remainder]}" if remainder else words
        if number < 1000:
            hundreds, remainder = divmod(number, 100)
            words = f"{ONES[hundreds]} hundred"
            return f"{words} {self._number_to_words(remainder)}" if remainder else words
        if number < 100000:
            thousands, remainder = divmod(number, 1000)
            words = f"{self._number_to_words(thousands)} thousand"
            return f"{words} {self._number_to_words(remainder)}" if remainder else words
        if number < 10000000:
            lakhs, remainder = divmod(number, 100000)
            words = f"{self._number_to_words(lakhs)} lakh"
            return f"{words} {self._number_to_words(remainder)}" if remainder else words
        return str(number)
