import faiss
import numpy as np
import os


class FaissIndex:
    def __init__(self, dim, index=None, id_map=None):
        self.index = index if index is not None else faiss.IndexFlatL2(dim)
        self.id_map = list(id_map) if id_map is not None else []

    def add(self, vectors, ids=None):
        if ids is not None and len(ids) != len(vectors):
            raise ValueError("Length of ids must match number of vectors")

        self.index.add(vectors)

        if ids is not None:
            self.id_map.extend([int(i) for i in ids])
        elif self.id_map:
            start = len(self.id_map)
            self.id_map.extend(range(start, start + len(vectors)))

    def search(self, query_vec, top_k=5):
        distances, indices = self.index.search(
            np.array([query_vec]).astype("float32"), top_k
        )

        if self.id_map:
            mapped_ids = np.array(
                [[self.id_map[i] for i in row] for row in indices], dtype=int
            )
        else:
            mapped_ids = indices

        return distances, mapped_ids

    def save(self, path):
        faiss.write_index(self.index, path)

        if self.id_map:
            id_path = f"{path}.ids.npy"
            np.save(id_path, np.array(self.id_map, dtype=int))

    @staticmethod
    def load(path, dim=None):
        index = faiss.read_index(path)

        id_map = []
        id_path = f"{path}.ids.npy"
        if os.path.exists(id_path):
            id_map = np.load(id_path).tolist()

        # dim is optional for compatibility; infer from index if not provided
        inferred_dim = dim if dim is not None else index.d
        return FaissIndex(inferred_dim, index=index, id_map=id_map)
