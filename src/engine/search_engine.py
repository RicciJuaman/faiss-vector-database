"""CLI wrapper around the hybrid search engine."""
from __future__ import annotations

from typing import Iterable

from psycopg2.extensions import connection

from engine.config import create_pg_connection, ensure_env_loaded, resolve_index_path
from engine.embedder import Embedder
from engine.hybrid_search import HybridSearch
from engine.indexer import FaissIndex


def display_hybrid_results(results: Iterable[dict]) -> None:
    print("\n==================== HYBRID RESULTS ====================\n")

    for i, r in enumerate(results, start=1):
        print(f"Result {i}")
        print(f"Document ID:    {r['id']}")
        print(f"Hybrid Score:   {r['hybrid']:.4f}")
        print(f"Semantic Score: {r['semantic']:.4f}")
        print(f"BM25 Score:     {r['bm25']:.4f}")
        if r.get("summary"):
            print(f"Summary:        {r['summary']}")
        if r.get("profile_name"):
            print(f"Reviewer:       {r['profile_name']}")
        if r.get("text"):
            text_preview = r['text'][:240] + ("…" if len(r['text']) > 240 else "")
            print(f"Text:           {text_preview}")
        print("--------------------------------------------------")

    print("\n=========================================================\n")


def initialize_components() -> tuple[HybridSearch, connection]:
    ensure_env_loaded()
    index_path = resolve_index_path()
    faiss_index = FaissIndex.load(index_path)
    embedder = Embedder()

    conn = create_pg_connection()
    return HybridSearch(faiss_index, conn, embedder), conn


if __name__ == "__main__":
    hybrid, conn = initialize_components()

    try:
        print("\nHybrid Search Engine Ready! (v0.2.0)")
        print("Type your query or 'exit' to quit.\n")

        while True:
            query = input("\n🔍 Enter search query: ").strip()
            if query.lower() == "exit":
                print("\nGoodbye!")
                break

            results = hybrid.search(query, k=5)
            display_hybrid_results(results)
    finally:
        conn.close()
        print("[✔] PostgreSQL connection closed")
