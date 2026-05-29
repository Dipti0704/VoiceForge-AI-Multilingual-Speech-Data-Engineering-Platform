import React from "react";
import ReactDOM from "react-dom/client";
import { Download, FileAudio, RefreshCw, Search, UploadCloud } from "lucide-react";
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
  const [rawTranscript, setRawTranscript] = React.useState("muje mera order cancl krna h bro");
  const [confidence, setConfidence] = React.useState(0.76);
  const [status, setStatus] = React.useState("all");
  const [isLoading, setIsLoading] = React.useState(false);

  const loadData = React.useCallback(async () => {
    setIsLoading(true);
    const statusQuery = status === "all" ? "" : `?status=${status}`;
    const [metricsResponse, recordsResponse] = await Promise.all([
      fetch(`${API_BASE}/metrics`),
      fetch(`${API_BASE}/records${statusQuery}`)
    ]);
    setMetrics(await metricsResponse.json());
    setRecords(await recordsResponse.json());
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
    await fetch(`${API_BASE}/audio/upload`, {
      method: "POST",
      body
    });
    await loadData();
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
            <div className="pipeline-list">
              <span>Upload</span>
              <span>Transcribe</span>
              <span>Clean</span>
              <span>Deduplicate</span>
              <span>Score</span>
            </div>
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

