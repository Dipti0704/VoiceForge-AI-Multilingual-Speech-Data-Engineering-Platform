import re


class QualityScoringService:
    def score(
        self,
        raw_text: str,
        clean_text: str,
        confidence: float,
        language: str,
        duplicate_risk: bool,
    ) -> tuple[int, list[str]]:
        issues: list[str] = []
        score = 100

        if confidence < 0.5:
            score -= 30
            issues.append("low transcription confidence")
        elif confidence < 0.75:
            score -= 12
            issues.append("medium transcription confidence")

        token_count = len(clean_text.split())
        if token_count < 3:
            score -= 18
            issues.append("too short for training")
        if token_count > 60:
            score -= 10
            issues.append("long utterance may need segmentation")

        if duplicate_risk:
            score -= 40
            issues.append("duplicate or near-duplicate sample")

        if language == "unknown":
            score -= 15
            issues.append("language detection failed")

        noisy_chars = len(re.findall(r"[^a-zA-Z0-9\u0900-\u097F\s]", raw_text))
        if noisy_chars:
            score -= min(15, noisy_chars * 2)
            issues.append("raw transcript contains noisy symbols")

        return max(0, min(100, score)), issues

