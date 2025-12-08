import numpy as np
from engine.embedder import Embedder
from engine.indexer import FaissIndex
from psycopg2.extras import RealDictCursor
import psycopg2
import os

class HybridSearch:
    def __init__(self, index_path, conn):
        self.embedder = Embedder()
        self.index = FaissIndex.load(index_path)
        self.conn = conn

    # -------------------------
    #  BM25 / FTS RETRIEVAL
    # -------------------------
    def bm25_search(self, query, k=20):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT "Id",
                       ts_rank(
                         to_tsvector('english', "Text"),
                         plainto_tsquery('english', %s)
                       ) AS bm25
                FROM reviews
                WHERE to_tsvector('english', "Text") @@ plainto_tsquery('english', %s)
                ORDER BY bm25 DESC
                LIMIT %s;
            """, (query, query, k))
            return cur.fetchall()

    # -------------------------
    #  SEMANTIC SEARCH
    # -------------------------
    def semantic_search(self, query, k=20):
        vec = self.embedder.embed_batch([query])
        distances, indices = self.index.search(vec, k)
        return list(zip(distances[0], indices[0]))

    # -------------------------
    #  NORMALIZATION
    # -------------------------
    def normalize(self, scores):
        arr = np.array(scores)
        if arr.max() == arr.min():
            return np.ones_like(arr)
        return (arr - arr.min()) / (arr.max() - arr.min())

    # -------------------------
    #  HYBRID COMBINATION
    # -------------------------
    def search(self, query, k=10, alpha=0.7):
        print("Semantic raw:", self.semantic_search(query, k=5))
        bm25_docs = self.bm25_search(query, k=20)
        sem_docs = self.semantic_search(query, k=20)

        # Map ID → semantic_score
        sem_map = {int(i): (1 - d) for d, i in sem_docs}

        # Build combined list
        combined = []
        for row in bm25_docs:
            doc_id = int(row["Id"])
            bm25 = row["bm25"]
            semantic = sem_map.get(doc_id, 0.0)  # fallback if not in semantic list
            combined.append({
                "id": doc_id,
                "bm25": bm25,
                "semantic": semantic
            })

        # Normalize both
        bm25_norm = self.normalize([c["bm25"] for c in combined])
        sem_norm = self.normalize([c["semantic"] for c in combined])

        # Combine scores
        for i, c in enumerate(combined):
            c["hybrid"] = alpha * sem_norm[i] + (1 - alpha) * bm25_norm[i]

        combined.sort(key=lambda x: x["hybrid"], reverse=True)
        return combined[:k]
