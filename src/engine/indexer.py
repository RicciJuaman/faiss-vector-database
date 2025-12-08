import faiss
import numpy as np

class FaissIndex:
    def __init__(self, dim):
        self.index = faiss.IndexFlatL2(dim)

    def add(self, vectors):
        self.index.add(vectors)

    def search(self, query_vec, top_k=5):
        return self.index.search(np.array([query_vec]).astype("float32"), top_k)

    def save(self, path):
        faiss.write_index(self.index, path)

    @staticmethod
    def load(path):
        return faiss.read_index(path)
