from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

from engine.embedder import Embedder
from engine.hybrid_search import HybridSearch
from engine.indexer import FaissIndex

# --------------------------------------------------
# App + CORS
# --------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Load ENV + DB
# --------------------------------------------------
load_dotenv()

def create_pg_connection():
    return psycopg2.connect(
        dbname=os.environ["PG_NAME"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        host=os.environ["PG_HOST"],
        port=os.environ.get("PG_PORT", 5432),
        cursor_factory=RealDictCursor,
    )

# --------------------------------------------------
# Initialize engine ONCE (important)
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "index" / "reviews.index"

faiss_index = FaissIndex.load(INDEX_PATH)
embedder = Embedder()
conn = create_pg_connection()
hybrid = HybridSearch(faiss_index, conn, embedder)

# --------------------------------------------------
# API schema
# --------------------------------------------------
class SearchRequest(BaseModel):
    query: str
    k: int = 5

# --------------------------------------------------
# Routes
# --------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/search/hybrid")
def search(req: SearchRequest):
    results = hybrid.search(req.query, k=req.k)

    # make JSON-safe
    clean = []
    for r in results:
        clean.append({
            "id": r["id"],
            "hybrid": float(r["hybrid"]),
            "semantic": float(r["semantic"]),
            "bm25": float(r["bm25"]),
        })

    return {"results": clean}

