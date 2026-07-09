from sqlalchemy.orm import Session
from database.models import Document
import uuid
from database.models import StudySession
from typing import Optional
from database.models import Message, User

def create_document(
    db: Session, 
    document_name: str, 
    original_filename: str, 
    stored_filename: str, 
    total_chunks: int,
    user_id: int
):
    document = Document(
        document_name=document_name, 
        original_filename=original_filename, 
        stored_filename=stored_filename, 
        total_chunks=total_chunks,
        user_id=user_id,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document

def get_all_documents(
    db: Session,
    user_id: int,
):
    return (
        db.query(Document)
        .filter(Document.user_id == user_id)
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
    
    document.original_filename = new_name

    db.commit()
    db.refresh(document)

    return document

def add_message(
    db: Session, 
    session_id: str, 
    role: str,
    content: str,
):
    message = Message(
        session_id=session_id,
        role=role,
        content=content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message

def get_messages(
    db: Session,
    session_id: str,
):
   
    return (
        db.query(Message)
        .filter(
            Message.session_id == session_id,
        )
        .order_by(
            Message.created_at.asc(),
        )
        .all()
    )

def get_user_by_email(
    db: Session,
    email: str,
):
    return(
        db.query(User)
        .filter(User.email == email)
        .first()
    )

def create_user(
    db: Session,
    name: str,
    email: str,
    password_hash: str,
):

    user = User(
        name=name,
        email=email,
        password_hash=password_hash,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user