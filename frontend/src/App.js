import { useState } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

function normalizeResults(rawResults) {
  const list = Array.isArray(rawResults) ? rawResults : rawResults?.results || [];

  return list.slice(0, 5).map((item, index) => {
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
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (event) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setError('Enter a query to search.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/search/hybrid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed, k: 5 }),
      });

      if (!response.ok) {
        throw new Error(`Search request failed with status ${response.status}`);
      }

      const data = await response.json();
      setResults(normalizeResults(data));
    } catch (err) {
      setError(err.message || 'Unable to complete search.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="hero">
        <p className="eyebrow">Hybrid Search Engine</p>
        <h1>Find the best matches with BM25 + semantic scores</h1>
        <p className="lede">
          Run a hybrid query and review the top 5 results with both lexical and semantic relevance metrics.
        </p>
      </header>

      <main className="content">
        <section className="search-panel">
          <form className="search-form" onSubmit={handleSearch}>
            <label className="visually-hidden" htmlFor="query-input">
              Search query
            </label>
            <input
              id="query-input"
              type="text"
              placeholder="Search for reviews, products, or topics..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Searching…' : 'Search'}
            </button>
          </form>
          {error && <p className="error">{error}</p>}
        </section>

        <section className="results-panel">
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
                  <span className="rank">#{index + 1}</span>
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
              </li>
            ))}
          </ol>
        </section>
      </main>
    </div>
  );
}

export default App;
