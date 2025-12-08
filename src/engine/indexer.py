import os
import json
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
ID_MAP_PATH = os.path.join(INDEX_DIR, "id_map.json")

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
    if os.path.exists(INDEX_PATH):
        print("[✔] Loaded existing FAISS index")
        return faiss.read_index(INDEX_PATH)
    else:
        print("[+] Creating new FAISS index")
        return faiss.IndexFlatL2(dim)

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

    id_map = []  # <--- vector index → DB ID mapping

    processed = index.ntotal
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

        texts = [row["Text"] if row["Text"] else "" for row in rows]
        vectors = embed_batch(texts)

        index.add(vectors)

        # Store DB IDs in exact vector order
        for row in rows:
            id_map.append(int(row["Id"]))

        processed += len(rows)

        if processed % SAVE_INTERVAL < BATCH_SIZE:
            faiss.write_index(index, INDEX_PATH)
            with open(ID_MAP_PATH, "w") as f:
                json.dump(id_map, f)
            print(f"[✔] Checkpoint saved at {processed}")

        print(f"[+] Embedded + indexed: {processed}/{total_rows}")

    # Final save
    faiss.write_index(index, INDEX_PATH)
    with open(ID_MAP_PATH, "w") as f:
        json.dump(id_map, f)

    print("[✔] FINAL SAVE COMPLETE")
    print("[✔] Indexing & ID map generation COMPLETE")

if __name__ == "__main__":
    embed_all()
