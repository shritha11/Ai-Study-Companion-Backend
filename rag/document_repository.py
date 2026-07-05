import os
import json
import shutil

FAISS_FOLDER = "faiss_index"

class DocumentRepository:
    def delete_document(self, document_name: str):
        # Everything inside this method needs to be indented by one extra level (typically 4 spaces)
        metadata = self.get_all_documents()
        document = None

        for doc in metadata:
            print("Metadata :", doc["document_name"])
            print("Request  :", document_name)

            if doc["document_name"].strip().lower() == document_name.strip().lower():
                document = doc
                break

        if document is None:
            return False

        upload_path = os.path.join(
            "uploads",
            document["stored_filename"],
        )

        if os.path.exists(upload_path):
            os.remove(upload_path)

        faiss_path = os.path.join(
            FAISS_FOLDER,
            document_name,
        )

        if os.path.exists(faiss_path):
            shutil.rmtree(faiss_path)

        return True

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