import os
import json
import numpy as np
from psycopg2.extras import RealDictCursor

from engine.embedder import Embedder
from engine.indexer import FaissIndex

class HybridSearch:
    def __init__(self, index_path, conn):
        self.embedder = Embedder()
        self.index = FaissIndex.load(index_path)
        self.conn = conn

        # Load vector index → DB ID mapping
        map_path = os.path.join(os.path.dirname(index_path), "id_map.json")
        with open(map_path, "r") as f:
            self.id_map = json.load(f)

        print(f"[✔] Loaded ID map ({len(self.id_map)} entries)")

    # -------------------------
    #  BM25 SEARCH
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
    #  SEMANTIC SEARCH (FAISS)
    # -------------------------
    def semantic_search(self, query, k=20):
        vec = self.embedder.embed_batch([query])[0]
        distances, vector_ids = self.index.search(vec, k)

        results = []
        for dist, vid in zip(distances[0], vector_ids[0]):
            db_id = self.id_map[vid]  # <-- FIX: correct ID
            semantic_score = 1 - float(dist)
            results.append((db_id, semantic_score))

        return results

    # -------------------------
    #  NORMALIZATION
    # -------------------------
    def normalize(self, scores):
        arr = np.array(scores)
        if arr.max() == arr.min():
            return np.ones_like(arr)
        return (arr - arr.min()) / (arr.max() - arr.min())

    # -------------------------
    #  HYBRID SEARCH
    # -------------------------
    def search(self, query, k=10, alpha=0.7):

        bm25_docs = self.bm25_search(query, k=50)
        sem_docs = self.semantic_search(query, k=50)

        # Convert semantic results to a map
        sem_map = {db_id: score for (db_id, score) in sem_docs}

        # Merge BM25 + Semantic results
        all_ids = set(sem_map.keys()) | {int(row["Id"]) for row in bm25_docs}

        combined = []
        for doc_id in all_ids:
            bm25 = next((row["bm25"] for row in bm25_docs if row["Id"] == doc_id), 0.0)
            semantic = sem_map.get(doc_id, 0.0)
            combined.append({"id": doc_id, "bm25": bm25, "semantic": semantic})

        # Normalize
        bm25_norm = self.normalize([c["bm25"] for c in combined])
        sem_norm = self.normalize([c["semantic"] for c in combined])

        # Hybrid score
        for i, c in enumerate(combined):
            c["hybrid"] = alpha * sem_norm[i] + (1 - alpha) * bm25_norm[i]

        # Sort by hybrid score
        combined.sort(key=lambda x: x["hybrid"], reverse=True)
        return combined[:k]
