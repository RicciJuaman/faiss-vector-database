"""Hybrid BM25 + semantic search implementation."""
from typing import Dict, Iterable, List

import numpy as np
from psycopg2.extras import RealDictCursor


class HybridSearch:
    def __init__(self, index, conn, embedder, debug: bool = False):
        """
        Args:
            index: FAISS IndexIDMap (returns real DB IDs).
            conn: PostgreSQL connection.
            embedder: Embedding model wrapper.
            debug: When True, logs raw score vectors.
        """
        self.index = index
        self.conn = conn
        self.embedder = embedder
        self.debug = debug

        print("[✔] HybridSearch initialized with FAISS IndexIDMap")

    # ---------------------------------------------
    # BM25 SEARCH (PostgreSQL)
    # ---------------------------------------------
    def bm25_search(self, query: str, k: int = 20) -> List[Dict]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT "Id",
                       ts_rank_cd(
                         to_tsvector('english', "Text"),
                         plainto_tsquery('english', %s)
                       ) AS bm25
                FROM reviews
                WHERE to_tsvector('english', "Text") @@ plainto_tsquery('english', %s)
                ORDER BY bm25 DESC
                LIMIT %s;
                """,
                (query, query, k),
            )

            return cur.fetchall()

    # ---------------------------------------------
    # SEMANTIC SEARCH (FAISS)
    # ---------------------------------------------
    def semantic_search(self, query: str, k: int = 20) -> List:
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
    # DOCUMENT FETCHING
    # ---------------------------------------------
    def fetch_documents(self, doc_ids: Iterable[int]) -> Dict[int, Dict]:
        """Load document metadata for the provided IDs.

        Args:
            doc_ids: Iterable of document identifiers to hydrate.

        Returns:
            Mapping of document ID to metadata dict.
        """

        ids = [int(doc_id) for doc_id in doc_ids if doc_id is not None]
        if not ids:
            return {}

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT "Id" AS id,
                       COALESCE(NULLIF("ProfileName", ''), 'Unknown reviewer') AS profile_name,
                       COALESCE("Summary", '') AS summary,
                       COALESCE("Text", '') AS text
                FROM reviews
                WHERE "Id" = ANY(%s);
                """,
                (ids,),
            )

            return {int(row["id"]): row for row in cur.fetchall()}

    # ---------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------
    def normalize(self, arr: Iterable[float]) -> np.ndarray:
        arr = np.array(list(arr), dtype=float)
        if arr.size == 0:
            return np.array([], dtype=float)
        if arr.max() == arr.min():
            return np.ones_like(arr, dtype=float)
        return (arr - arr.min()) / (arr.max() - arr.min())

    # ---------------------------------------------
    # HYBRID SEARCH
    # ---------------------------------------------
    def search(self, query: str, k: int = 10, alpha: float = 0.7) -> List[Dict]:
        """
        alpha = weight for semantic search
        (1 - alpha) = weight for BM25
        """

        # Retrieve results
        bm25_docs = self.bm25_search(query, k=500)
        sem_docs = self.semantic_search(query, k=50)

        # Convert lists → fast lookup maps
        bm25_map = {int(row["Id"]): float(row.get("bm25") or 0.0) for row in bm25_docs}
        sem_map = {int(doc_id): float(score) for (doc_id, score) in sem_docs}

        # Union of all doc IDs
        all_ids = set(bm25_map.keys()) | set(sem_map.keys())

        combined = []
        for doc_id in all_ids:
            bm25 = bm25_map.get(doc_id, 0.0)
            semantic = sem_map.get(doc_id, 0.0)
            combined.append({"id": int(doc_id), "bm25": float(bm25), "semantic": float(semantic)})

        if self.debug:
            print("\nRAW BM25 scores:", [c["bm25"] for c in combined])
            print("RAW Semantic scores:", [c["semantic"] for c in combined])

        # Normalize both score sets
        bm25_norm = self.normalize([c["bm25"] for c in combined])
        sem_norm = self.normalize([c["semantic"] for c in combined])

        # Apply weights + hybrid scoring
        for i, c in enumerate(combined):
            c["hybrid"] = alpha * sem_norm[i] + (1 - alpha) * bm25_norm[i]

        # Sort results
        combined.sort(key=lambda x: x["hybrid"], reverse=True)

        top_results = combined[:k]
        documents = self.fetch_documents([c["id"] for c in top_results])

        hydrated = []
        for item in top_results:
            doc_meta = documents.get(item["id"], {})
            hydrated.append(
                {
                    "id": int(item["id"]),
                    "bm25": float(item.get("bm25", 0.0)),
                    "semantic": float(item.get("semantic", 0.0)),
                    "hybrid": float(item.get("hybrid", 0.0)),
                    "profile_name": doc_meta.get("profile_name", "Unknown reviewer"),
                    "summary": doc_meta.get("summary", ""),
                    "text": doc_meta.get("text", ""),
                }
            )

        return hydrated
