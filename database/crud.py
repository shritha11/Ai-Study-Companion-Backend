from sqlalchemy.orm import Session
from database.models import Document
import uuid
from database.models import StudySession
from typing import Optional

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

def get_all_documents(
    db: Session,
):
    return (
        db.query(Document)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

def create_session(
    db: Session, 
    document_name: Optional[str],
):
    session = StudySession(
        id=str(uuid.uuid4()),
        document_name=document_name,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session

def get_latest_session(
    db: Session, 
    document_name: str,
):
    return(
        db.query(StudySession)
        .filter(
            StudySession.document_name == document_name,
        )
        .order_by(
            StudySession.created_at.desc(),
        )
        .first()
    )

def delete_document(
    db: Session, 
    document_name: str,
):
    document = (
        db.query(Document)
        .filter(Document.document_name == document_name)
        .first()
    )

    if document is None:
        return None
    
    db.delete(document)
    db.commit()

    return document

def rename_document(
    db: Session,
    old_name: str, 
    new_name: str,
):
    document = (
        db.query(Document)
        .filter(Document.document_name == old_name)
        .first()
    )

    if document is None:
        return None
    
    document.document_name = new_name

    db.commit()
    db.refresh(document)

    return document