import React from "react";
import ReactDOM from "react-dom/client";
import {
  CheckCircle2,
  Download,
  FileAudio,
  RefreshCw,
  Search,
  UploadCloud,
  XCircle
} from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api";

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function StatusBadge({ status }) {
  const className = `badge badge-${status}`;
  return <span className={className}>{status}</span>;
}

function App() {
  const [metrics, setMetrics] = React.useState(null);
  const [records, setRecords] = React.useState([]);
  const [reviewRecords, setReviewRecords] = React.useState([]);
  const [reviewDrafts, setReviewDrafts] = React.useState({});
  const [reviewMessage, setReviewMessage] = React.useState("");
  const [rawTranscript, setRawTranscript] = React.useState("muje mera order cancl krna h bro");
  const [confidence, setConfidence] = React.useState(0.76);
  const [status, setStatus] = React.useState("all");
  const [isLoading, setIsLoading] = React.useState(false);
  const [uploadState, setUploadState] = React.useState({
    phase: "idle",
    message: "Ready for audio upload.",
    record: null
  });

  const loadData = React.useCallback(async () => {
    setIsLoading(true);
    const statusQuery = status === "all" ? "" : `?status=${status}`;
    const [metricsResponse, recordsResponse, reviewResponse] = await Promise.all([
      fetch(`${API_BASE}/metrics`),
      fetch(`${API_BASE}/records${statusQuery}`),
      fetch(`${API_BASE}/records?status=review`)
    ]);
    const [metricsPayload, recordsPayload, reviewPayload] = await Promise.all([
      metricsResponse.json(),
      recordsResponse.json(),
      reviewResponse.json()
    ]);
    setMetrics(metricsPayload);
    setRecords(recordsPayload);
    setReviewRecords(reviewPayload);
    setReviewDrafts((currentDrafts) => {
      const nextDrafts = {};
      for (const record of reviewPayload) {
        nextDrafts[record.id] = currentDrafts[record.id] ?? record.clean_transcript;
      }
      return nextDrafts;
    });
    setIsLoading(false);
  }, [status]);

  React.useEffect(() => {
    loadData().catch(() => setIsLoading(false));
  }, [loadData]);

  async function submitTranscript(event) {
    event.preventDefault();
    setIsLoading(true);
    await fetch(`${API_BASE}/records/transcript`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: "dashboard-demo",
        raw_transcript: rawTranscript,
        confidence: Number(confidence)
      })
    });
    await loadData();
  }

  async function uploadAudio(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    const body = new FormData();
    body.append("file", file);
    setIsLoading(true);
    setUploadState({
      phase: "working",
      message: `Uploading and transcribing ${file.name}...`,
      record: null
    });

    try {
      const response = await fetch(`${API_BASE}/audio/upload`, {
        method: "POST",
        body
      });

      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(payload?.detail ?? "Audio upload failed.");
      }

      setUploadState({
        phase: "success",
        message: "Audio transcribed and processed.",
        record: payload
      });
      await loadData();
    } catch (error) {
      setUploadState({
        phase: "error",
        message: error instanceof Error ? error.message : "Audio upload failed.",
        record: null
      });
      setIsLoading(false);
    } finally {
      event.target.value = "";
    }
  }

  async function submitReview(record, action) {
    setIsLoading(true);
    setReviewMessage("");
    try {
      const response = await fetch(`${API_BASE}/records/${record.id}/review`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action,
          corrected_transcript: action === "approve" ? reviewDrafts[record.id] : undefined
        })
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(payload?.detail ?? "Review action failed.");
      }
      setReviewMessage(
        action === "approve"
          ? `Record ${record.id} approved for training export.`
          : `Record ${record.id} rejected from the training set.`
      );
      await loadData();
    } catch (error) {
      setReviewMessage(error instanceof Error ? error.message : "Review action failed.");
      setIsLoading(false);
    }
  }

  function exportDataset(format) {
    window.location.href = `${API_BASE}/datasets/export?format=${format}&min_quality=70`;
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">VoiceForge AI</p>
          <h1>Speech data operations</h1>
        </div>
        <nav>
          <a className="active" href="#pipeline">Pipeline</a>
          <a href="#review">Review</a>
          <a href="#records">Records</a>
          <a href="#exports">Exports</a>
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Hindi-English voice assistant dataset</p>
            <h2>Curate noisy speech into training-ready rows</h2>
          </div>
          <button className="icon-button" onClick={loadData} title="Refresh data">
            <RefreshCw size={18} />
          </button>
        </header>

        <section className="metrics-grid">
          <Metric label="Total" value={metrics?.total_records ?? 0} />
          <Metric label="Processed" value={metrics?.processed_records ?? 0} />
          <Metric label="Review" value={metrics?.review_records ?? 0} />
          <Metric label="Duplicates" value={metrics?.duplicate_records ?? 0} />
          <Metric label="Avg quality" value={metrics?.average_quality ?? 0} />
        </section>

        <section className="work-grid" id="pipeline">
          <form className="panel" onSubmit={submitTranscript}>
            <div className="panel-heading">
              <FileAudio size={18} />
              <h3>Transcript ingestion</h3>
            </div>
            <textarea
              value={rawTranscript}
              onChange={(event) => setRawTranscript(event.target.value)}
              rows={5}
            />
            <label className="field">
              <span>Confidence</span>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={confidence}
                onChange={(event) => setConfidence(event.target.value)}
              />
            </label>
            <button className="primary-button" disabled={isLoading}>
              <Search size={17} />
              Process transcript
            </button>
          </form>

          <div className="panel">
            <div className="panel-heading">
              <UploadCloud size={18} />
              <h3>Audio upload</h3>
            </div>
            <label className="dropzone">
              <UploadCloud size={32} />
              <span>Upload wav, mp3, or m4a</span>
              <input type="file" accept="audio/*" onChange={uploadAudio} />
            </label>
            <div className={`upload-result upload-${uploadState.phase}`}>
              <div className="upload-result-heading">
                {uploadState.phase === "error" ? <XCircle size={18} /> : <CheckCircle2 size={18} />}
                <strong>{uploadState.message}</strong>
              </div>
              {uploadState.record && (
                <div className="transcript-preview">
                  <span>Whisper transcript</span>
                  <p>{uploadState.record.raw_transcript}</p>
                  <span>Clean transcript</span>
                  <p>{uploadState.record.clean_transcript}</p>
                  <small>{uploadState.record.notes}</small>
                </div>
              )}
            </div>
            <div className="pipeline-list">
              <span>Upload</span>
              <span>Transcribe</span>
              <span>Clean</span>
              <span>Deduplicate</span>
              <span>Score</span>
            </div>
          </div>
        </section>

        <section className="review-section" id="review">
          <div className="section-heading">
            <div>
              <h3>Review queue</h3>
              <p>Correct low-quality samples before they enter the training dataset.</p>
            </div>
            <StatusBadge status="review" />
          </div>
          {reviewMessage && <div className="review-message">{reviewMessage}</div>}
          <div className="review-list">
            {reviewRecords.map((record) => (
              <article className="review-item" key={record.id}>
                <div className="review-meta">
                  <strong>Record {record.id}</strong>
                  <span>{record.language}</span>
                  <span>Quality {record.quality_score}</span>
                </div>
                <div className="review-copy">
                  <span>Raw transcript</span>
                  <p>{record.raw_transcript}</p>
                </div>
                <label className="field">
                  <span>Corrected training text</span>
                  <textarea
                    value={reviewDrafts[record.id] ?? record.clean_transcript}
                    onChange={(event) =>
                      setReviewDrafts((drafts) => ({
                        ...drafts,
                        [record.id]: event.target.value
                      }))
                    }
                    rows={3}
                  />
                </label>
                {record.notes && <small className="review-notes">{record.notes}</small>}
                <div className="review-actions">
                  <button
                    className="primary-button"
                    disabled={isLoading}
                    onClick={() => submitReview(record, "approve")}
                  >
                    <CheckCircle2 size={17} />
                    Approve
                  </button>
                  <button
                    className="danger-button"
                    disabled={isLoading}
                    onClick={() => submitReview(record, "reject")}
                  >
                    <XCircle size={17} />
                    Reject
                  </button>
                </div>
              </article>
            ))}
            {!reviewRecords.length && (
              <div className="empty-review">
                <CheckCircle2 size={20} />
                <span>No records waiting for review</span>
              </div>
            )}
          </div>
        </section>

        <section className="records-section" id="records">
          <div className="section-heading">
            <h3>Dataset records</h3>
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="all">All records</option>
              <option value="processed">Processed</option>
              <option value="review">Review</option>
              <option value="duplicate">Duplicate</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Clean transcript</th>
                  <th>Language</th>
                  <th>Quality</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.id}>
                    <td>{record.id}</td>
                    <td>
                      <strong>{record.clean_transcript}</strong>
                      <small>{record.raw_transcript}</small>
                    </td>
                    <td>{record.language}</td>
                    <td>{record.quality_score}</td>
                    <td><StatusBadge status={record.status} /></td>
                  </tr>
                ))}
                {!records.length && (
                  <tr>
                    <td colSpan="5" className="empty">No records yet</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="export-bar" id="exports">
          <div>
            <h3>Training dataset export</h3>
            <p>Only processed rows with quality score 70 or higher are exported.</p>
          </div>
          <div className="export-actions">
            <button onClick={() => exportDataset("jsonl")}>
              <Download size={17} />
              JSONL
            </button>
            <button onClick={() => exportDataset("csv")}>
              <Download size={17} />
              CSV
            </button>
          </div>
        </section>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
