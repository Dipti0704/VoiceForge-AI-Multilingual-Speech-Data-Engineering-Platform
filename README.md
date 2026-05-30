# VoiceForge AI

Multilingual Speech Data Engineering Platform for converting messy audio/transcript inputs into curated training datasets.

## What It Demonstrates

VoiceForge models the data layer behind a Hindi-English voice assistant:

```text
Raw Audio
-> Speech Recognition
-> Language Detection
-> Text Normalization
-> Deduplication
-> Quality Scoring
-> Review Queue
-> Dataset Export
```

The goal is not just to train a model. The goal is to build the machinery that turns noisy real-world speech data into high-quality training data.

## Architecture

```text
React Dashboard
      |
      v
FastAPI Backend
      |
      +-- Upload Service
      +-- Transcription Service
      +-- Language Detection
      +-- Cleaning Pipeline
      +-- Deduplication Engine
      +-- Quality Scoring Engine
      +-- Dataset Exporter
      |
      v
PostgreSQL
```

Kafka/Redpanda is included in Docker Compose as the next step for event-driven processing:

```text
audio.uploaded -> transcript.created -> transcript.cleaned -> quality.scored
```

## Tech Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL
- Frontend: React, Vite, Tailwind CSS
- Data layer: cleaning, normalization, deduplication, quality scoring, dataset export
- AI integration points: Whisper, FastText, Sentence Transformers
- Streaming-ready: Kafka-compatible Redpanda service
- Deployment: Docker Compose

## Project Structure

```text
backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
frontend/
  src/
docker-compose.yml
```

## Run Locally

### 1. Start infrastructure

```bash
docker compose up -d postgres redpanda
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Whisper transcription is enabled through `ENABLE_WHISPER=true` in the backend `.env`, and it expects the backend dependencies plus `ffmpeg` to be available.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Flow

Upload an audio file:

```bash
curl -F "file=@call_001.wav" http://localhost:8000/api/audio/upload
```

Create a transcript-only record for demos:

```bash
curl -X POST http://localhost:8000/api/records/transcript \
  -H "Content-Type: application/json" \
  -d "{\"source\":\"demo\",\"raw_transcript\":\"muje mera order cancl krna h bro\",\"confidence\":0.76}"
```

Export high-quality dataset rows:

```bash
curl "http://localhost:8000/api/datasets/export?format=jsonl&min_quality=70"
```

## Resume Description

Built an end-to-end speech data engineering platform that ingests raw audio, performs transcription, multilingual normalization, semantic deduplication, quality scoring, review queue routing, and training dataset generation using FastAPI, PostgreSQL, Kafka-compatible streaming architecture, Whisper-ready transcription interfaces, and React.

