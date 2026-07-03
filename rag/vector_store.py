import os
import json
import faiss
import numpy as np


class VectorStore:

    def __init__(self, dimension: int):

        self.dimension = dimension

    def _paths(self, document_name: str):

        folder = os.path.join("faiss_index", document_name)

        os.makedirs(folder, exist_ok=True)

        return (
            os.path.join(folder, "index.faiss"),
            os.path.join(folder, "chunks.json"),
        )

    def add(self, document_name, embeddings, texts):

        index_path, chunks_path = self._paths(document_name)

        vectors = np.array(embeddings).astype("float32")

        index = faiss.IndexFlatL2(self.dimension)

        index.add(vectors)

        faiss.write_index(index, index_path)

        with open(chunks_path, "w", encoding="utf-8") as f:

            json.dump(
                texts,
                f,
                ensure_ascii=False,
                indent=2,
            )

    def search(self, document_name, query_embedding, k=5):

        index_path, chunks_path = self._paths(document_name)

        index = faiss.read_index(index_path)

        with open(chunks_path, "r", encoding="utf-8") as f:

            chunks = json.load(f)

        query = np.array([query_embedding]).astype("float32")

        distances, indices = index.search(query, k)

        results = []

        for idx in indices[0]:

            if idx == -1:
                continue

            results.append(chunks[idx])

        return results