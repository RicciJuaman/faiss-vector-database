"""
Hybrid BM25 + Semantic Search Engine

Pipeline:
1. BM25 search via PostgreSQL
2. Semantic search via FAISS
3. Score normalization
4. Hybrid scoring
5. Top-K ranking
6. Payload hydration (fetch document text)
"""

from typing import Dict, Iterable, List, Tuple
import numpy as np
from psycopg2.extras import RealDictCursor


class HybridSearch:
    def __init__(self, index, conn, embedder, debug: bool = False):
        """
        Args:
            index: FAISS IndexIDMap (returns DB document IDs)
            conn: psycopg2 PostgreSQL connection
            embedder: embedding model wrapper
            debug: enable verbose logging
        """
        self.index = index
        self.conn = conn
        self.embedder = embedder
        self.debug = debug

        print("[✔] HybridSearch initialized with FAISS IndexIDMap")

    # ==========================================================
    # BM25 SEARCH (PostgreSQL Full-Text Search)
    # ==========================================================
    def bm25_search(self, query: str, k: int = 500) -> Dict[int, float]:
        """
        Returns:
            { doc_id: bm25_score }
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                WITH query AS (
                    SELECT websearch_to_tsquery('english', %s) AS q
                )
                SELECT
                    r."Id",
                    ts_rank_cd(
                        setweight(to_tsvector('english', COALESCE(r."Summary", '')), 'B') ||
                        setweight(to_tsvector('english', COALESCE(r."Text", '')), 'D'),
                        q,
                        32
                    ) AS bm25
                FROM reviews r, query
                WHERE q <> ''::tsquery
                  AND to_tsvector('english', COALESCE(r."Summary", '') || ' ' || COALESCE(r."Text", '')) @@ q
                ORDER BY bm25 DESC
                LIMIT %s;
                """,
                (query, k),
            )

            rows = cur.fetchall()

        return {int(row["Id"]): float(row["bm25"]) for row in rows}

    # ==========================================================
    # SEMANTIC SEARCH (FAISS)
    # ==========================================================
    def semantic_search(self, query: str, k: int = 50) -> Dict[int, float]:
        """
        Returns:
            { doc_id: semantic_score }
        """
        vector = self.embedder.embed_batch([query])
        distances, ids = self.index.search(vector, k)

        results: Dict[int, float] = {}

        for dist, doc_id in zip(distances[0], ids[0]):
            if doc_id == -1:
                continue

            # Convert L2 distance → similarity
            semantic_score = 1.0 - float(dist)
            results[int(doc_id)] = semantic_score

        return results

    # ==========================================================
    # SCORE NORMALIZATION (MIN-MAX)
    # ==========================================================
    def normalize(self, values: Iterable[float]) -> np.ndarray:
        values = np.array(list(values), dtype=float)

        if values.size == 0:
            return np.array([], dtype=float)

        min_v, max_v = values.min(), values.max()

        if min_v == max_v:
            return np.ones_like(values)

        return (values - min_v) / (max_v - min_v)

    # ==========================================================
    # HYBRID SEARCH (MAIN ENTRY)
    # ==========================================================
    def search(
        self,
        query: str,
        k: int = 5,
        alpha: float = 0.7,
    ) -> List[Dict]:
        """
        alpha:
            weight for semantic score
            (1 - alpha) is BM25 weight
        """

        # ----------------------------
        # Retrieve candidate scores
        # ----------------------------
        bm25_scores = self.bm25_search(query)
        semantic_scores = self.semantic_search(query)

        all_doc_ids = set(bm25_scores.keys()) | set(semantic_scores.keys())

        if not all_doc_ids:
            return []

        # ----------------------------
        # Merge raw scores
        # ----------------------------
        merged = []
        for doc_id in all_doc_ids:
            merged.append({
                "id": doc_id,
                "bm25": bm25_scores.get(doc_id, 0.0),
                "semantic": semantic_scores.get(doc_id, 0.0),
            })

        if self.debug:
            print("RAW BM25:", [m["bm25"] for m in merged])
            print("RAW SEM :", [m["semantic"] for m in merged])

        # ----------------------------
        # Normalize scores
        # ----------------------------
        bm25_norm = self.normalize(m["bm25"] for m in merged)
        sem_norm = self.normalize(m["semantic"] for m in merged)

        # ----------------------------
        # Hybrid scoring
        # ----------------------------
        for i, doc in enumerate(merged):
            doc["hybrid"] = (
                alpha * sem_norm[i]
                + (1.0 - alpha) * bm25_norm[i]
            )

        # ----------------------------
        # Rank + select top-K
        # ----------------------------
        merged.sort(key=lambda x: x["hybrid"], reverse=True)
        top_results = merged[:k]

        # ----------------------------
        # Hydrate with document text
        # ----------------------------
        ids = [r["id"] for r in top_results]

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT "Id", "ProfileName", "Summary", "Text"
                FROM reviews
                WHERE "Id" = ANY(%s);
                """,
                (ids,),
            )
            rows = cur.fetchall()

        text_map = {
            int(row["Id"]): {
                "profile_name": row.get("ProfileName"),
                "summary": row.get("Summary"),
                "review_text": row.get("Text"),
            }
            for row in rows
        }

        for r in top_results:
            metadata = text_map.get(r["id"], {})
            r.update(metadata)

        return top_results
