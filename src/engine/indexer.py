import os
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
import faiss
import requests
from dotenv import load_dotenv

load_dotenv()

# ----------------------
# CONFIG
# ----------------------
BATCH_SIZE = 200
SAVE_INTERVAL = 5000

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "index"))
INDEX_PATH = os.path.join(INDEX_DIR, "reviews.index")

os.makedirs(INDEX_DIR, exist_ok=True)

PG_CONN = psycopg2.connect(
    dbname=os.environ["PG_NAME"],
    user=os.environ["PG_USER"],
    password=os.environ["PG_PASSWORD"],
    host=os.environ["PG_HOST"],
    port=os.environ.get("PG_PORT", 5432)
)
cursor = PG_CONN.cursor(cursor_factory=RealDictCursor)

# ----------------------
# EMBEDDING
# ----------------------
def embed_batch(text_list):
    response = requests.post(
        "http://localhost:11434/api/embed",
        json={"model": "bge-large", "input": text_list}
    )
    return np.array(response.json()["embeddings"], dtype="float32")

# ----------------------
# LOAD OR CREATE INDEX
# ----------------------
def load_or_init_index(dim):
    """Loads an existing FAISS index, or creates a new IndexIDMap index."""
    if os.path.exists(INDEX_PATH):
        print("[✔] Loaded existing FAISS index")
        index = faiss.read_index(INDEX_PATH)

        # If index is NOT an IndexIDMap, wrap it
        if not isinstance(index, faiss.IndexIDMap):
            print("[+] Wrapping existing index inside IndexIDMap")
            index = faiss.IndexIDMap(index)

        return index

    else:
        print("[+] Creating new FAISS IndexIDMap index")
        base = faiss.IndexFlatL2(dim)
        index = faiss.IndexIDMap(base)
        return index

# ----------------------
# MAIN INGEST
# ----------------------
def embed_all():
    print("[…] Counting rows...")
    cursor.execute("SELECT COUNT(*) FROM reviews;")
    total_rows = cursor.fetchone()["count"]
    print(f"Total rows: {total_rows}")

    print("[…] Testing embedding dimension…")
    test_vec = embed_batch(["test"])[0]
    dim = len(test_vec)

    index = load_or_init_index(dim)

    processed = index.ntotal  # continue from previous state if exists
    print(f"Starting from vector position {processed}")

    while True:
        cursor.execute("""
            SELECT "Id", "Text"
            FROM reviews
            ORDER BY "Id"
            OFFSET %s LIMIT %s;
        """, (processed, BATCH_SIZE))

        rows = cursor.fetchall()
        if not rows:
            break

        # Prepare text for embedding
        texts = [row["Text"] if row["Text"] else "" for row in rows]
        vectors = embed_batch(texts)

        # Prepare IDs for FAISS
        ids = np.array([row["Id"] for row in rows], dtype="int64")

        # Add vectors WITH IDs
        index.add_with_ids(vectors, ids)

        processed += len(rows)

        # Checkpoint save
        if processed % SAVE_INTERVAL < BATCH_SIZE:
            faiss.write_index(index, INDEX_PATH)
            print(f"[✔] Checkpoint saved at {processed}")

        print(f"[+] Embedded + indexed: {processed}/{total_rows}")

    # Final save
    faiss.write_index(index, INDEX_PATH)

    print("[✔] FINAL SAVE COMPLETE")
    print("[✔] Indexing COMPLETE — FAISS now contains DB IDs internally.")

# ----------------------
# MAIN ENTRY
# ----------------------
if __name__ == "__main__":
    embed_all()


# ----------------------
# FAISS Index Loader Class
# ----------------------
class FaissIndex:
    @staticmethod
    def load(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"FAISS index not found at: {path}")
        return faiss.read_index(path)

    @staticmethod
    def save(index, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        faiss.write_index(index, path)
