<<<<<<< HEAD
import { useState } from 'react';
import './App.css';
=======
import { useState } from "react";
import "./App.css";

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

function normalizeResults(rawResults) {
  const list = Array.isArray(rawResults)
    ? rawResults
    : rawResults?.results || [];

  return list.slice(0, 5).map((item, index) => ({
    id: item.id ?? `result-${index + 1}`,
    hybrid: item.hybrid ?? null,
    semantic: item.semantic ?? null,
    bm25: item.bm25 ?? null,
    text:
      item.text ||
      item.content ||
      item.review_text ||
      "No content available.",
  }));
}

function formatScore(score) {
  if (score === null || score === undefined || Number.isNaN(score)) {
    return "–";
  }
  return Number(score).toFixed(4);
}
>>>>>>> dev_c

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

function normalizeResults(rawResults) {
  const list = Array.isArray(rawResults) ? rawResults : rawResults?.results || [];

  return list.slice(0, 5).map((item, index) => {
    const profileName =
      item.profile_name ||
      item.profileName ||
      item.profile ||
      item.author ||
      'Unknown reviewer';

    const summary =
      item.summary || item.title || item.heading || item.review_summary || 'Untitled review';

    const text =
      item.text ||
      item.content ||
      item.document ||
      item.body ||
      item.review_text ||
      'No content available.';

    return {
      id: item.id ?? item.doc_id ?? item.document_id ?? `result-${index + 1}`,
      hybrid: item.hybrid ?? item.score ?? null,
      semantic: item.semantic ?? item.semantic_score ?? null,
      bm25: item.bm25 ?? item.bm25_score ?? null,
      profileName,
      summary,
      text,
    };
  });
}

function formatScore(score) {
  if (score === null || score === undefined || Number.isNaN(score)) {
    return '–';
  }
  return Number(score).toFixed(4);
}

function App() {
<<<<<<< HEAD
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (event) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setError('Enter a query to search.');
=======
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e) => {
    e.preventDefault();
    const trimmed = query.trim();

    if (!trimmed) {
      setError("Enter a query to search.");
>>>>>>> dev_c
      return;
    }

    setLoading(true);
<<<<<<< HEAD
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/search/hybrid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
=======
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/search/hybrid`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
>>>>>>> dev_c
        body: JSON.stringify({ query: trimmed, k: 5 }),
      });

      if (!response.ok) {
<<<<<<< HEAD
        throw new Error(`Search request failed with status ${response.status}`);
=======
        throw new Error(`Request failed (${response.status})`);
>>>>>>> dev_c
      }

      const data = await response.json();
      setResults(normalizeResults(data));
    } catch (err) {
<<<<<<< HEAD
      setError(err.message || 'Unable to complete search.');
=======
      setError(err.message || "Search failed.");
>>>>>>> dev_c
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="hero">
<<<<<<< HEAD
        <p className="eyebrow">Hybrid Search Engine</p>
        <h1>Find the best matches with BM25 + semantic scores</h1>
        <p className="lede">
          Run a hybrid query and review the top 5 results with both lexical and semantic relevance metrics.
=======
        <p className="eyebrow">Hybrid Search Engine by Ricci J.</p>
        <h1>Semantic + BM25 Hybrid Search</h1>
        <p className="lede">
          Combining lexical relevance and vector similarity for better ranking.
>>>>>>> dev_c
        </p>
      </header>

      <main className="content">
        <section className="search-panel">
          <form className="search-form" onSubmit={handleSearch}>
<<<<<<< HEAD
            <label className="visually-hidden" htmlFor="query-input">
              Search query
            </label>
            <input
              id="query-input"
              type="text"
              placeholder="Search for reviews, products, or topics..."
=======
            <input
              type="text"
              placeholder="Search…"
>>>>>>> dev_c
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
            />
            <button type="submit" disabled={loading}>
<<<<<<< HEAD
              {loading ? 'Searching…' : 'Search'}
=======
              {loading ? "Searching…" : "Search"}
>>>>>>> dev_c
            </button>
          </form>
          {error && <p className="error">{error}</p>}
        </section>

        <section className="results-panel">
<<<<<<< HEAD
          <div className="results-header">
            <div>
              <p className="eyebrow">Top results</p>
              <h2>Hybrid ranking (Top 5)</h2>
            </div>
            <div className="score-key">
              <span className="tag">Hybrid</span>
              <span className="tag">Semantic</span>
              <span className="tag">BM25</span>
            </div>
          </div>

          {results.length === 0 && !loading && !error && (
            <div className="empty-state">
              <p>Submit a search to see ranked results.</p>
            </div>
          )}

          <ol className="results-list">
            {results.map((result, index) => (
              <li key={result.id} className="result-card">
                <div className="result-meta">
                  <div className="rank-name">
                    <span className="rank">#{index + 1}</span>
                    <div className="identity">
                      <p className="summary">{result.summary}</p>
                      <p className="byline">by {result.profileName}</p>
                    </div>
                  </div>
                  <div className="scores">
                    <div>
                      <p className="score-label">Hybrid</p>
                      <p className="score-value">{formatScore(result.hybrid)}</p>
                    </div>
                    <div>
                      <p className="score-label">Semantic</p>
                      <p className="score-value">{formatScore(result.semantic)}</p>
                    </div>
                    <div>
                      <p className="score-label">BM25</p>
                      <p className="score-value">{formatScore(result.bm25)}</p>
                    </div>
                  </div>
                </div>
                <p className="result-text">{result.text}</p>
=======
          {results.length === 0 && !loading && !error && (
            <p className="empty-state">
              Submit a query to see ranked results.
            </p>
          )}

          <ol className="results-list">
            {results.map((r, i) => (
              <li key={r.id} className="result-card">
                <div className="result-meta">
                  <span className="rank">#{i + 1}</span>
                  <div className="scores">
                    <div>
                      <p className="score-label">Hybrid</p>
                      <p className="score-value">
                        {formatScore(r.hybrid)}
                      </p>
                    </div>
                    <div>
                      <p className="score-label">Semantic</p>
                      <p className="score-value">
                        {formatScore(r.semantic)}
                      </p>
                    </div>
                    <div>
                      <p className="score-label">BM25</p>
                      <p className="score-value">
                        {formatScore(r.bm25)}
                      </p>
                    </div>
                  </div>
                </div>

                <p className="result-text">{r.text}</p>
>>>>>>> dev_c
              </li>
            ))}
          </ol>
        </section>
      </main>
    </div>
  );
}

export default App;
