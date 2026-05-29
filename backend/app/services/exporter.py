import csv
import json
from io import StringIO

from sqlalchemy.orm import Session

from app.models import AudioRecord, RecordStatus


class DatasetExporter:
    def export(self, db: Session, file_format: str = "jsonl", min_quality: int = 70) -> tuple[str, str]:
        records = (
            db.query(AudioRecord)
            .filter(AudioRecord.status == RecordStatus.processed.value)
            .filter(AudioRecord.quality_score >= min_quality)
            .order_by(AudioRecord.id.asc())
            .all()
        )

        if file_format == "csv":
            return "text/csv", self._to_csv(records)
        return "application/x-ndjson", self._to_jsonl(records)

    def _to_jsonl(self, records: list[AudioRecord]) -> str:
        rows = []
        for record in records:
            rows.append(
                json.dumps(
                    {
                        "audio": record.audio_path,
                        "text": record.clean_transcript,
                        "language": record.language,
                        "quality_score": record.quality_score,
                    },
                    ensure_ascii=False,
                )
            )
        return "\n".join(rows) + ("\n" if rows else "")

    def _to_csv(self, records: list[AudioRecord]) -> str:
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["audio", "text", "language", "quality_score"])
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "audio": record.audio_path,
                    "text": record.clean_transcript,
                    "language": record.language,
                    "quality_score": record.quality_score,
                }
            )
        return output.getvalue()

