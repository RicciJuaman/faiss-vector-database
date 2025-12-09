import numpy as np
from psycopg2.extras import RealDictCursor


class HybridSearch:
    def __init__(self, index, conn, embedder):
        """
        index     → FAISS IndexIDMap (returns real DB IDs)
        conn      → PostgreSQL connection
        embedder  → Your embedding model wrapper
        """
        self.index = index
        self.conn = conn
        self.embedder = embedder

        print("[✔] HybridSearch initialized with FAISS IndexIDMap")

    # ---------------------------------------------
    # BM25 SEARCH (PostgreSQL)
    # ---------------------------------------------
    def bm25_search(self, query, k=20):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT "Id",
                       ts_rank_cd(
                         to_tsvector('english', "Text"),
                         plainto_tsquery('english', %s)
                       ) AS bm25
                FROM reviews
                WHERE to_tsvector('english', "Text") @@ plainto_tsquery('english', %s)
                ORDER BY bm25 DESC
                LIMIT %s;
            """, (query, query, k))

            return cur.fetchall()

    # ---------------------------------------------
    # SEMANTIC SEARCH (FAISS)
    # ---------------------------------------------
    def semantic_search(self, query, k=20):
        vec = self.embedder.embed_batch([query])

        distances, ids = self.index.search(vec, k)

        results = []
        for dist, db_id in zip(distances[0], ids[0]):
            if db_id == -1:
                continue

            semantic_score = 1 - float(dist)
            results.append((int(db_id), semantic_score))

        return results

    # ---------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------
    def normalize(self, arr):
        arr = np.array(arr, dtype=float)
        if arr.max() == arr.min():
            return np.ones_like(arr, dtype=float)
        return (arr - arr.min()) / (arr.max() - arr.min())

    # ---------------------------------------------
    # HYBRID SEARCH
    # ---------------------------------------------
    def search(self, query, k=10, alpha=0.7):
        """
        alpha = weight for semantic search
        (1 - alpha) = weight for BM25
        """

        # Retrieve results
        bm25_docs = self.bm25_search(query, k=500)
        sem_docs = self.semantic_search(query, k=50)

        # Convert lists → fast lookup maps
        bm25_map = {int(row["Id"]): float(row["bm25"]) for row in bm25_docs}
        sem_map = {doc_id: score for (doc_id, score) in sem_docs}

        # Union of all doc IDs
        all_ids = set(bm25_map.keys()) | set(sem_map.keys())

        combined = []
        for doc_id in all_ids:
            bm25 = bm25_map.get(doc_id, 0.0)
            semantic = sem_map.get(doc_id, 0.0)
            combined.append({"id": doc_id, "bm25": bm25, "semantic": semantic})
        print("\nRAW BM25 scores:", [c["bm25"] for c in combined])
        print("RAW Semantic scores:", [c["semantic"] for c in combined])

        # Normalize both score sets
        bm25_norm = self.normalize([c["bm25"] for c in combined])
        sem_norm  = self.normalize([c["semantic"] for c in combined])

        # Apply weights + hybrid scoring
        for i, c in enumerate(combined):
            c["hybrid"] = alpha * sem_norm[i] + (1 - alpha) * bm25_norm[i]

        # Sort results
        combined.sort(key=lambda x: x["hybrid"], reverse=True)

        return combined[:k]
