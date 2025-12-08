import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# === Load helper modules ===
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
#                     LOAD FAISS INDEX
# ==========================================================
print("[…] Loading FAISS index…")
index = FaissIndex.load(INDEX_PATH)
print(f"[✔] FAISS index loaded ({index.ntotal} vectors)")

# ==========================================================
#                INITIALIZE EMBEDDER
# ==========================================================
embedder = Embedder(model="bge-large")

# ==========================================================
#               SEMANTIC SEARCH FUNCTION
# ==========================================================
def semantic_search(query, k=5):
    print("\n[1] Embedding your query…")
    q_vec = embedder.embed_batch([query])

    print("[2] Running FAISS nearest-neighbor search…")
    distances, indices = index.search(q_vec, k)

    print(f"[✔] Found {len(indices[0])} nearest neighbors")

    neighbor_ids = [int(i) for i in indices[0]]

    print(f"[3] Fetching {len(neighbor_ids)} documents from PostgreSQL…")
    cursor.execute("""
        SELECT "Id", "Summary", "Text"
        FROM reviews
        WHERE "Id" = ANY(%s);
    """, (neighbor_ids,))

    rows = cursor.fetchall()

    results = []
    for score, row_id, row_data in zip(distances[0], neighbor_ids, rows):
        results.append({
            "score": float(score),
            "id": row_id,
            "summary": row_data["Summary"],
            "text": row_data["Text"],
        })

    return results

# ==========================================================
#                    DISPLAY RESULTS
# ==========================================================
def display_results(results):
    print("\n==================== RESULTS ====================\n")

    for i, r in enumerate(results, start=1):
        print(f"Result {i}")
        print(f"Vector ID: {r['id']}")
        print(f"Similarity Score: {1 - r['score']:.4f}")
        print(f"Summary: {r['summary']}")
        print(f"Text: {r['text'][:250]}…")
        print("--------------------------------------------------")

    print("\n=================================================\n")

# ==========================================================
#                   MAIN LOOP
# ==========================================================
if __name__ == "__main__":
    print("\nSemantic Search Engine Ready!")
    print("Type your query or 'exit' to quit.\n")

    while True:
        query = input("\n🔍 Enter search query: ").strip()
        if query.lower() == "exit":
            print("\nGoodbye!")
            break

        results = semantic_search(query, k=5)
        display_results(results)
