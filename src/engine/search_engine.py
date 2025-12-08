import os
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
import faiss
import requests

# ==========================================================
#                 PATH RESOLUTION FOR INDEX
# ==========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "index", "reviews.index"))

print(f"[✔] Resolved FAISS index path: {INDEX_PATH}")


# ==========================================================
#              LOAD ENVIRONMENT VARIABLES (.env)
# ==========================================================
from dotenv import load_dotenv
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
#               LOAD FAISS INDEX
# ==========================================================
print("[…] Loading FAISS index…")
index = faiss.read_index(INDEX_PATH)
print(f"[✔] FAISS index loaded ({index.ntotal} vectors)")


# ==========================================================
#               EMBEDDING FUNCTION (Ollama)
# ==========================================================
def embed_batch(text_list):
    """Embeds a list of text strings using Ollama."""
    response = requests.post(
        "http://localhost:11434/api/embed",
        json={"model": "bge-large", "input": text_list},
    )

    if "embeddings" not in response.json():
        raise RuntimeError("Ollama returned an invalid response.")

    vectors = response.json()["embeddings"]
    return np.array(vectors, dtype="float32")


# ==========================================================
#               SEMANTIC SEARCH FUNCTION
# ==========================================================
def semantic_search(query, k=5):
    print("\n[1] Embedding your query…")
    q_vec = embed_batch([query])

    print("[2] Running FAISS nearest-neighbor search…")
    distances, indices = index.search(q_vec, k)

    distances = distances[0]
    indices = indices[0]

    print(f"[✔] Found {len(indices)} nearest neighbors")

    # MUST convert numpy.int64 → Python int
    neighbor_ids = [int(i) for i in indices]

    print(f"[3] Fetching {len(neighbor_ids)} rows from PostgreSQL…")
    cursor.execute("""
        SELECT "Id", "Summary", "Text"
        FROM reviews
        WHERE "Id" = ANY(%s);
    """, (neighbor_ids,))

    rows = cursor.fetchall()

    return list(zip(distances, neighbor_ids, rows))


# ==========================================================
#               PRETTY PRINT RESULTS
# ==========================================================
def display_results(hits):
    print("\n==================== RESULTS ====================\n")

    for rank, (dist, vec_id, row) in enumerate(hits, start=1):
        print(f"Result {rank}")
        print(f"Vector ID: {vec_id}")
        print(f"Similarity Score: {1 - dist:.4f}")
        print(f"Summary: {row['Summary']}")
        print(f"Text: {row['Text'][:250]}…")
        print("--------------------------------------------------")

    print("\n=================================================\n")


# ==========================================================
#               MAIN INTERACTIVE LOOP
# ==========================================================
if __name__ == "__main__":
    print("\nSemantic Search Engine Ready!")
    print("Type your query or 'exit' to quit.\n")

    while True:
        q = input("\n🔍 Enter search query: ").strip()
        if q.lower() == "exit":
            print("\nGoodbye!")
            break

        hits = semantic_search(q, k=5)
        display_results(hits)
