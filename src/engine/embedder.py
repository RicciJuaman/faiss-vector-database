import requests
import numpy as np

class Embedder:
    def __init__(self, model="bge-large"):
        self.model = model

    def embed_batch(self, texts):
        response = requests.post(
            "http://localhost:11434/api/embed",
            json={"model": self.model, "input": texts}
        )
        vectors = response.json()["embeddings"]
        return np.array(vectors, dtype="float32")
