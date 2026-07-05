import os
import json
from datetime import datetime
def save_metadata(
    document_name: str, 
    original_filename: str, 
    stored_filename: str, 
    total_chunks: int,
):

    folder = os.path.join("faiss_index", document_name)
    os.makedirs(folder, exist_ok=True)

    metadata = {
        "document_name": document_name, 
        "original_filename": original_filename, 
        "stored_filename": stored_filename, 
        "total_chunks": total_chunks, 
        "uploaded_at": datetime.now().isoformat(),
    }

    with open(os.path.join(folder, "metadata.json"), "w", encoding="utf-8",) as f:
        json.dump(metadata, f, indent=4)