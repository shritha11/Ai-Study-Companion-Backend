from sqlalchemy.orm import Session
from database.models import Document

def create_document(
    db: Session, 
    document_name: str, 
    original_filename: str, 
    stored_filename: str, 
    total_chunks: int,
):
    document = Document(
        document_name=document_name, 
        original_filename=original_filename, 
        stored_filename=stored_filename, 
        total_chunks=total_chunks,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document

def get_documents(
    db: Session,
):
    return db.query(Document).all()