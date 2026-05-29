# VoiceForge AI Architecture

## Core Data Contract

Each record represents one candidate training sample:

```json
{
  "audio": "uploads/call_001.wav",
  "text": "Mujhe order cancel karna hai",
  "language": "Hindi-English",
  "quality_score": 92
}
```

The platform keeps both the raw transcript and the cleaned transcript so quality issues remain auditable.

## Pipeline Stages

1. Ingestion
   - Accepts raw audio files or transcript-only demo input.
   - Stores metadata and source information.

2. Transcription
   - Uses a `TranscriptionService` interface.
   - Local fallback is deterministic for demos.
   - Whisper can be enabled with `ENABLE_WHISPER=true` and `backend[ml]`.

3. Language Detection
   - Detects Hindi, English, and Hindi-English mixed text.
   - The current implementation is heuristic and can be replaced by FastText.

4. Cleaning
   - Normalizes casing, spacing, noisy symbols, and common Hinglish abbreviations.
   - Example: `muje mera order cancl krna h bro` -> `Mujhe mera order cancel karna hai`.

5. Deduplication
   - Uses exact hashing plus character n-gram cosine similarity.
   - This is intentionally swappable with Sentence Transformers for semantic duplicate detection.

6. Quality Scoring
   - Combines transcription confidence, length, language detection, noise, and duplicate risk.
   - Low-quality records are routed to the review queue.

7. Dataset Export
   - Exports processed records above a quality threshold as JSONL or CSV.
   - Output is ready to feed into model training or evaluation pipelines.

## Streaming Roadmap

The synchronous API is easy to demo. At scale, each stage should become an independent worker:

```text
audio.uploaded
  -> transcription.completed
  -> transcript.cleaned
  -> duplicate.checked
  -> quality.scored
  -> dataset.row.accepted
```

Kafka-compatible Redpanda is included in `docker-compose.yml` so the project can evolve into a streaming pipeline without changing the product model.

## Production Extensions

- Replace local files with S3 or MinIO.
- Add Alembic migrations.
- Add human review correction endpoints.
- Store embeddings for semantic search and duplicate detection.
- Add Kafka producers and consumers around each pipeline stage.
- Add authentication and dataset versioning.

