from sentence_transformers import SentenceTransformer


class EmbeddingService:

    def __init__(self):
        # Loads once when the server starts
        self.model = SentenceTransformer(
            "BAAI/bge-small-en-v1.5"
        )

    def embed_text(self, text: str):
        """
        Generate embedding for a single text.
        """

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()

    def embed_chunks(self, chunks: list[str]):
        """
        Generate embeddings for multiple chunks.
        """

        embeddings = self.model.encode(
            chunks,
            normalize_embeddings=True,
        )

        return embeddings.tolist()