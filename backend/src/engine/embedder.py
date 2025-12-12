"""Wrapper around the Ollama embedding API."""
from typing import Iterable, List

import numpy as np
import requests


class Embedder:
    def __init__(self, model: str = "bge-large", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def embed_batch(self, texts: Iterable[str]) -> np.ndarray:
        """Embed a batch of texts using the configured model.

        Args:
            texts: Iterable of strings to embed.

        Returns:
            A NumPy array of shape (batch_size, embedding_dim) containing float32 vectors.
        """
        payload = {"model": self.model, "input": list(texts)}
        response = requests.post(f"{self.base_url}/api/embed", json=payload, timeout=30)
        response.raise_for_status()

        embeddings: List[List[float]] = response.json().get("embeddings", [])
        if not embeddings:
            raise ValueError("Embedding service returned no vectors.")

        return np.asarray(embeddings, dtype="float32")
