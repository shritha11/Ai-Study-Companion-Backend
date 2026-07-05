from rag.loaders.loader_factory import extract_text
from rag.chunker import chunk_text
from rag.embeddings import EmbeddingService
from rag.vector_store import VectorStore
from rag.retriever import Retriever
from rag.document_metadata import save_metadata

class DocumentService:
    def __init__(self):
        EMBEDDING_DIMENSION = 384
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore(EMBEDDING_DIMENSION)
        self.retriever = Retriever(EMBEDDING_DIMENSION)

    def process_document(self, file_path: str, document_name: str, original_filename: str, stored_filename: str):
        """
        Process a PDF and store its embeddings.
        """
        print("Extracting text...")
        text = extract_text(file_path)
        print("Text extracted.")
        print("Chunking text...")
        chunks = chunk_text(text)
        print("Text chunked.")
        print(f"Generated {len(chunks)} chunks")
        print("Generating embeddings...")
        embeddings = self.embedding_service.embed_chunks(chunks)
        print("Saving vectors...")
        self.vector_store.add(document_name=document_name, embeddings=embeddings, texts=chunks)
        save_metadata(document_name=document_name, original_filename=original_filename, stored_filename=stored_filename, total_chunks=len(chunks))
        print("Document indexed successfully.")
        return len(chunks)

    def retrieve(self, document_name: str, question: str, top_k: int = 5):
        """
        Retrieve relevant chunks for a question.
        """
        query_embedding = self.embedding_service.embed_text(question)
        results = self.retriever.retrieve(
            document_name=document_name,
            query_embedding=query_embedding,
            top_k=top_k
        )
        return results