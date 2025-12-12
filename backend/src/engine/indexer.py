"""Index creation pipeline for FAISS."""
from __future__ import annotations

import os
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Iterable

import faiss
import numpy as np
import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

from engine.embedder import Embedder

# ----------------------
# CONFIG
# ----------------------
BATCH_SIZE = 200
SAVE_INTERVAL = 5000

BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR.parent / "index"
INDEX_PATH = INDEX_DIR / "reviews.index"


# ----------------------
# ENV + DB
# ----------------------
def load_env() -> None:
    load_dotenv()
    required = ["PG_NAME", "PG_USER", "PG_PASSWORD", "PG_HOST"]
    missing = [key for key in required if key not in os.environ]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")


def create_pg_connection() -> connection:
    return psycopg2.connect(
        dbname=os.environ["PG_NAME"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        host=os.environ["PG_HOST"],
        port=os.environ.get("PG_PORT", 5432),
    )


# ----------------------
# EMBEDDING
# ----------------------
def embed_batch(embedder: Embedder, text_list: Iterable[str]) -> np.ndarray:
    return embedder.embed_batch(text_list)


# ----------------------
# LOAD OR CREATE INDEX
# ----------------------
def load_or_init_index(dim: int, index_path: Path) -> faiss.IndexIDMap:
    """Load an existing FAISS index or create a new IndexIDMap."""
    if index_path.exists():
        print("[✔] Loaded existing FAISS index")
        index = faiss.read_index(str(index_path))

        # If index is NOT an IndexIDMap, wrap it
        if not isinstance(index, faiss.IndexIDMap):
            print("[+] Wrapping existing index inside IndexIDMap")
            index = faiss.IndexIDMap(index)

        return index

    print("[+] Creating new FAISS IndexIDMap index")
    base = faiss.IndexFlatL2(dim)
    return faiss.IndexIDMap(base)


# ----------------------
# MAIN INGEST
# ----------------------
def embed_all(conn: connection, embedder: Embedder, batch_size: int = BATCH_SIZE) -> None:
    print("[…] Counting rows...")
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT COUNT(*) FROM reviews;")
        total_rows = cursor.fetchone()["count"]
    print(f"Total rows: {total_rows}")

    print("[…] Testing embedding dimension…")
    test_vec = embed_batch(embedder, ["test"])[0]
    dim = len(test_vec)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index = load_or_init_index(dim, INDEX_PATH)

    processed = index.ntotal  # continue from previous state if exists
    print(f"Starting from vector position {processed}")

    while True:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT "Id", "Text"
                FROM reviews
                ORDER BY "Id"
                OFFSET %s LIMIT %s;
                """,
                (processed, batch_size),
            )
            rows = cursor.fetchall()

        if not rows:
            break

        texts = [row["Text"] if row["Text"] else "" for row in rows]
        vectors = embed_batch(embedder, texts)

        ids = np.array([row["Id"] for row in rows], dtype="int64")
        index.add_with_ids(vectors, ids)

        processed += len(rows)

        if processed % SAVE_INTERVAL < batch_size:
            FaissIndex.save(index, INDEX_PATH)
            print(f"[✔] Checkpoint saved at {processed}")

        print(f"[+] Embedded + indexed: {processed}/{total_rows}")

    FaissIndex.save(index, INDEX_PATH)

    print("[✔] FINAL SAVE COMPLETE")
    print("[✔] Indexing COMPLETE — FAISS now contains DB IDs internally.")


# ----------------------
# CLI
# ----------------------
def parse_args() -> Namespace:
    parser = ArgumentParser(description="Embed and index review data into FAISS.")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Number of rows to embed per batch")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    load_env()
    embedder = Embedder()
    with create_pg_connection() as conn:
        embed_all(conn, embedder, batch_size=args.batch_size)


# ----------------------
# FAISS Index Loader Class
# ----------------------
class FaissIndex:
    @staticmethod
    def load(path: Path) -> faiss.Index:
        if not path.exists():
            raise FileNotFoundError(f"FAISS index not found at: {path}")
        return faiss.read_index(str(path))

    @staticmethod
    def save(index: faiss.Index, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(path))
