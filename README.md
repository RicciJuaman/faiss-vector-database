# FAISS Vector Database – Built from Scratch

This project is a full **vector database system built entirely from scratch**, using:

- **FAISS** (Facebook AI Similarity Search) as the vector index  
- **Ollama + BGE-Large (1024-dim embeddings)** as the embedding engine  
- **PostgreSQL** as the metadata store  
- **Python** for ingestion, embedding, indexing, and semantic search  

The goal of this project is to **design, build, and operate a production-style vector database** without relying on hosted services like Pinecone, Weaviate, or pgvector extensions.  
Everything here demonstrates **AI infrastructure engineering** from first principles.

---

## Project Overview

This system:

1. Loads a dataset (in this case: 500k+ Amazon reviews) from PostgreSQL  
2. Generates dense vector embeddings using **bge-large** running locally via Ollama  
3. Builds a FAISS index for fast approximate nearest-neighbor (ANN) search  
4. Stores FAISS index + ID mappings on disk  
5. Performs semantic search by:
   - Embedding user queries  
   - Querying FAISS for the top-k similar vectors  
   - Pulling full metadata from PostgreSQL  

This architecture mirrors how modern AI systems perform **RAG (Retrieval-Augmented Generation)** and semantic search at scale.

---

## Why Build a Vector Database Yourself?

Most engineers only use hosted vector databases.  
This project proves a deeper level of understanding:

- How embeddings work  
- How vectors are stored  
- How ANN indexes operate  
- How semantic search is built  
- How to connect vector storage to relational metadata  
- How retrieval systems are designed internally  

By building this manually, you gain hands-on mastery of the same components used by:

- OpenAI  
- Google DeepMind  
- Meta  
- Databricks  
- Snowflake  
- NVIDIA  
- Every modern RAG pipeline  

This is practical AI infrastructure engineering.

---
## 🙌 Author

Ricci — Data Scientist & AI Engineer in training  
Building real AI infrastructure from the ground up.
