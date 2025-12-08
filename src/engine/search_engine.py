import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# === Load helper modules ===
from engine.hybrid_search import HybridSearch
from engine.embedder import Embedder
from engine.indexer import FaissIndex

import numpy as np

# ==========================================================
#      PATH RESOLUTION FOR INDEX LOCATION
# ==========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "index", "reviews.index"))
print(f"[✔] Resolved FAISS index path: {INDEX_PATH}")

# ==========================================================
#              LOAD ENVIRONMENT VARIABLES (.env)
# ==========================================================
load_dotenv()

PG_CONN = psycopg2.connect(
    dbname=os.environ["PG_NAME"],
    user=os.environ["PG_USER"],
    password=os.environ["PG_PASSWORD"],
    host=os.environ["PG_HOST"],
    port=os.environ.get("PG_PORT", 5432)
)
cursor = PG_CONN.cursor(cursor_factory=RealDictCursor)
print("[✔] Connected to PostgreSQL")

# ==========================================================
#              INITIALIZE HYBRID SEARCH
# ==========================================================
from engine.indexer import FaissIndex
from engine.embedder import Embedder
from engine.hybrid_search import HybridSearch

# Load FAISS index
faiss_index = FaissIndex.load(INDEX_PATH)

# Create embedder
embedder = Embedder()

# Create hybrid engine
hybrid = HybridSearch(faiss_index, PG_CONN, embedder)


# ==========================================================
#              DISPLAY HYBRID RESULTS
# ==========================================================
def display_hybrid_results(results):
    print("\n==================== HYBRID RESULTS ====================\n")

    for i, r in enumerate(results, start=1):
        print(f"Result {i}")
        print(f"Document ID:    {r['id']}")
        print(f"Hybrid Score:   {r['hybrid']:.4f}")
        print(f"Semantic Score: {r['semantic']:.4f}")
        print(f"BM25 Score:     {r['bm25']:.4f}")
        print("--------------------------------------------------")

    print("\n=========================================================\n")

# ==========================================================
#                   MAIN LOOP
# ==========================================================
if __name__ == "__main__":
    print("\nHybrid Search Engine Ready! (v0.2.0)")
    print("Type your query or 'exit' to quit.\n")

    while True:
        query = input("\n🔍 Enter search query: ").strip()
        if query.lower() == "exit":
            print("\nGoodbye!")
            break

        results = hybrid.search(query, k=5)
        display_hybrid_results(results)
