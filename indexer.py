import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
import faiss
import requests
from dotenv import load_dotenv
load_dotenv()
import os

# ----------------------
# CONFIG
# ----------------------
BATCH_SIZE = 200               # good for Ollama batching
SAVE_INTERVAL = 5000           # save FAISS every 5k vectors
INDEX_PATH = "reviews.index"

PG_CONN = psycopg2.connect(
    dbname="postgres",
    user=os.environ["PG_USER"],
    password=os.environ["PG_PASSWORD"],
    host=os.environ["PG_HOST"],
    port=5432
)

cursor = PG_CONN.cursor(cursor_factory=RealDictCursor)

# ----------------------
# EMBEDDING via Ollama
# ----------------------
def embed_batch(text_list):
    response = requests.post(
        "http://localhost:11434/api/embed",
        json={
            "model": "bge-large",
            "input": text_list
        }
    )
    vectors = response.json()["embeddings"]
    return np.array(vectors, dtype="float32")

# ----------------------
# FAISS INDEX LOADING
# ----------------------
def load_or_init_index(dim):
    try:
        index = faiss.read_index(INDEX_PATH)
        print("[✔] Loaded existing FAISS index")
    except:
        index = faiss.IndexFlatL2(dim)
        print("[+] Created new FAISS flat L2 index")
    return index

# ----------------------
# MAIN INGEST LOOP
# ----------------------
def embed_all():

    print("[…] Counting rows...")
    cursor.execute("SELECT COUNT(*) FROM reviews;")
    total_rows = cursor.fetchone()["count"]
    print(f"Total rows: {total_rows}")

    print("[…] Testing embedding dimension…")
    test_vec = embed_batch(["test"])[0]
    dim = len(test_vec)
    print(f"Vector dimension = {dim}")

    index = load_or_init_index(dim)

    processed = index.ntotal
    print(f"Starting from position {processed}/{total_rows}")

    while True:

        cursor.execute(
            '''
            SELECT "Id", "Text"
            FROM reviews
            ORDER BY "Id"
            OFFSET %s LIMIT %s;
            ''',
            (processed, BATCH_SIZE)
        )
        rows = cursor.fetchall()

        if not rows:
            print("No more rows. Finished embedding.")
            break

        texts = [row["Text"] if row["Text"] else "" for row in rows]

        # embed batch
        vectors = embed_batch(texts)

        # add to FAISS
        index.add(vectors)

        processed += len(rows)

        # Save periodically
        if processed % SAVE_INTERVAL < BATCH_SIZE:
            faiss.write_index(index, INDEX_PATH)
            print(f"Saved checkpoint at {processed}/{total_rows}")

        print(f"[+]Embedded + indexed: {processed}/{total_rows}")

    faiss.write_index(index, INDEX_PATH)
    print("FINAL SAVE COMPLETE")
    print("Embedding + Indexing COMPLETE!")

# ----------------------
if __name__ == "__main__":
    embed_all()
