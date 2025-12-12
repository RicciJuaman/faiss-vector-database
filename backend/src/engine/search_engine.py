"""CLI wrapper around the hybrid search engine."""
from __future__ import annotations
<<<<<<< HEAD:src/engine/search_engine.py

from typing import Iterable

from psycopg2.extensions import connection

from engine.config import create_pg_connection, ensure_env_loaded, resolve_index_path
from engine.embedder import Embedder
from engine.hybrid_search import HybridSearch
from engine.indexer import FaissIndex
=======

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

from engine.embedder import Embedder
from engine.hybrid_search import HybridSearch
from engine.indexer import FaissIndex

# ==========================================================
#      PATH RESOLUTION FOR INDEX LOCATION
# ==========================================================
BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = (BASE_DIR.parent / "index" / "reviews.index").resolve()
print(f"[✔] Resolved FAISS index path: {INDEX_PATH}")


# ==========================================================
#              LOAD ENVIRONMENT VARIABLES (.env)
# ==========================================================
def create_pg_connection():
    load_dotenv()
    required = ["PG_NAME", "PG_USER", "PG_PASSWORD", "PG_HOST"]
    missing = [key for key in required if key not in os.environ]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    conn = psycopg2.connect(
        dbname=os.environ["PG_NAME"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        host=os.environ["PG_HOST"],
        port=os.environ.get("PG_PORT", 5432),
    )
    conn.cursor(cursor_factory=RealDictCursor)  # validate connection + cursor factory
    print("[✔] Connected to PostgreSQL")
    return conn


# ==========================================================
#              INITIALIZE HYBRID SEARCH
# ==========================================================
faiss_index = FaissIndex.load(INDEX_PATH)
embedder = Embedder()
>>>>>>> dev_c:backend/src/engine/search_engine.py


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


<<<<<<< HEAD:src/engine/search_engine.py
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
=======
# ==========================================================
#                   MAIN LOOP
# ==========================================================
if __name__ == "__main__":
    with create_pg_connection() as conn:
        hybrid = HybridSearch(faiss_index, conn, embedder)

>>>>>>> dev_c:backend/src/engine/search_engine.py
        print("\nHybrid Search Engine Ready! (v0.2.0)")
        print("Type your query or 'exit' to quit.\n")

        while True:
            query = input("\n🔍 Enter search query: ").strip()
            if query.lower() == "exit":
                print("\nGoodbye!")
                break

            results = hybrid.search(query, k=5)
            display_hybrid_results(results)
<<<<<<< HEAD:src/engine/search_engine.py
    finally:
        conn.close()
        print("[✔] PostgreSQL connection closed")
=======
>>>>>>> dev_c:backend/src/engine/search_engine.py
