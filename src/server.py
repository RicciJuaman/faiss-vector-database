"""FastAPI service exposing the hybrid search engine."""
from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from engine.config import create_connection_pool, ensure_env_loaded, resolve_index_path
from engine.embedder import Embedder
from engine.hybrid_search import HybridSearch
from engine.indexer import FaissIndex

logger = logging.getLogger(__name__)


class HybridQuery(BaseModel):
    query: str = Field(..., description="Search query text")
    k: int = Field(5, ge=1, le=50, description="Number of results to return")
    alpha: float = Field(0.7, ge=0.0, le=1.0, description="Weight for semantic scoring")


def create_app() -> FastAPI:
    app = FastAPI(title="Hybrid Search Service", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    ensure_env_loaded()
    index_path = resolve_index_path()
    faiss_index = FaissIndex.load(index_path)
    embedder = Embedder()
    pool = create_connection_pool()

    logger.info("Hybrid search backend initialized", extra={"index_path": str(index_path)})

    def get_connection():
        conn = pool.getconn()
        try:
            yield conn
        finally:
            pool.putconn(conn)

    def get_search_engine(conn=Depends(get_connection)):
        return HybridSearch(faiss_index, conn, embedder)

    @app.post("/search/hybrid")
    def hybrid_search(payload: HybridQuery, engine: HybridSearch = Depends(get_search_engine)):
        if not payload.query.strip():
            raise HTTPException(status_code=400, detail="Query must not be empty.")

        try:
            results = engine.search(payload.query, k=payload.k, alpha=payload.alpha)
        except Exception as exc:  # pragma: no cover - surfaced to client
            logger.exception("Hybrid search failed")
            raise HTTPException(status_code=500, detail="Hybrid search failed.") from exc

        return {"results": results}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.on_event("shutdown")
    def shutdown_event():
        pool.closeall()
        logger.info("Connection pool closed")

    return app


app = create_app()
