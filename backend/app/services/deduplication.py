import hashlib
import math
from collections import Counter

from sqlalchemy.orm import Session

from app.models import AudioRecord


class DeduplicationService:
    def fingerprint(self, text: str) -> str:
        normalized = " ".join(text.lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def find_duplicate(self, db: Session, clean_text: str, threshold: float = 0.92) -> AudioRecord | None:
        candidates = db.query(AudioRecord).filter(AudioRecord.clean_transcript != "").all()
        for candidate in candidates:
            if self.fingerprint(candidate.clean_transcript) == self.fingerprint(clean_text):
                return candidate
            if self._cosine_similarity(candidate.clean_transcript, clean_text) >= threshold:
                return candidate
        return None

    def _cosine_similarity(self, left: str, right: str) -> float:
        left_vec = self._char_ngrams(left)
        right_vec = self._char_ngrams(right)
        if not left_vec or not right_vec:
            return 0.0
        overlap = set(left_vec) & set(right_vec)
        numerator = sum(left_vec[key] * right_vec[key] for key in overlap)
        left_norm = math.sqrt(sum(value * value for value in left_vec.values()))
        right_norm = math.sqrt(sum(value * value for value in right_vec.values()))
        return numerator / (left_norm * right_norm)

    def _char_ngrams(self, text: str, n: int = 3) -> Counter[str]:
        compact = f"  {' '.join(text.lower().split())}  "
        return Counter(compact[index : index + n] for index in range(max(0, len(compact) - n + 1)))

