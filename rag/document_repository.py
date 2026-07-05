import os
import json
FAISS_FOLDER = "faiss_index"

class DocumentRepository:
    def get_all_documents(self):
        documents = []

        if not os.path.exists(FAISS_FOLDER):
            return documents

        for folder in os.listdir(FAISS_FOLDER):
            metadata_path = os.path.join(
                FAISS_FOLDER, 
                folder, 
                "metadata.json",
            )

            if os.path.exists(metadata_path):
                with open(
                    metadata_path,
                    "r",
                    encoding="utf-8",
                ) as f:
                    
                    documents.append(json.load(f))
        
        documents.sort(key=lambda x: x["uploaded_at"], reverse=True)

        return documents
        

