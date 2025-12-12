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
    profileName: item.profile_name || item.profileName || "Unknown reviewer",
    summary: item.summary || item.Summary || "No summary provided.",
    reviewText:
      item.review_text ||
      item.reviewText ||
      item.text ||
      item.content ||
      "No content available.",
  }));
}

function formatScore(score) {
  if (score === null || score === undefined || Number.isNaN(score)) {
    return "–";
  }
  return Number(score).toFixed(4);
}

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e) => {
    e.preventDefault();
    const trimmed = query.trim();

    if (!trimmed) {
      setError("Enter a query to search.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/search/hybrid`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed, k: 5 }),
      });

      if (!response.ok) {
        throw new Error(`Request failed (${response.status})`);
      }

      const data = await response.json();
      setResults(normalizeResults(data));
    } catch (err) {
      setError(err.message || "Search failed.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="hero">
        <p className="eyebrow">Hybrid Search Engine by Ricci J.</p>
        <h1>Semantic + BM25 Hybrid Search</h1>
        <p className="lede">
          Combining lexical relevance and vector similarity for better ranking.
        </p>
      </header>

      <main className="content">
        <section className="search-panel">
          <form className="search-form" onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Search…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
            />
            <button type="submit" disabled={loading}>
              {loading ? "Searching…" : "Search"}
            </button>
          </form>
          {error && <p className="error">{error}</p>}
        </section>

        <section className="results-panel">
          {results.length === 0 && !loading && !error && (
            <p className="empty-state">
              Submit a query to see ranked results.
            </p>
          )}

          <ol className="results-list">
            {results.map((r, i) => (
              <li key={r.id} className="result-card">
                <div className="result-meta">
                  <div className="identity">
                    <span className="rank">#{i + 1}</span>
                    <div className="identity-text">
                      <p className="meta-label">ID</p>
                      <p className="meta-value">{r.id}</p>
                      <p className="meta-label">Profile</p>
                      <p className="meta-value">{r.profileName}</p>
                    </div>
                  </div>
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
                <p className="result-summary">{r.summary}</p>
                <p className="result-text">{r.reviewText}</p>
              </li>
            ))}
          </ol>
        </section>
      </main>
    </div>
  );
}

export default App;
