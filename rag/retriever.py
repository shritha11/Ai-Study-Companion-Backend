from rag.vector_store import VectorStore


class Retriever:
    def __init__(self, dimension):
        self.store = VectorStore(dimension)

    def retrieve(
        self,
        document_name,
        query_embedding,
        top_k=5,
    ):

        return self.store.search(
            document_name=document_name,
            query_embedding=query_embedding,
            k=top_k,
        )