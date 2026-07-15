from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import Document
import uuid
from database.models import StudySession
from typing import Optional
from database.models import Message, User, Quiz, FlashcardSet

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

def get_session_count(
    db: Session,
    user_id: int,
):
    return(
        db.query(func.count(StudySession.id))
        .filter(StudySession.user_id == user_id)
        .scalar()
    )

def get_document_count(
    db: Session,
    user_id: int,
):
    return(
        db.query(func.count(Document.id))
        .filter(Document.user_id == user_id)
        .scalar()
    )

def create_session(
    db: Session, 
    document_name: Optional[str],
    user_id: int,
):
    session = StudySession(
        id=str(uuid.uuid4()),
        document_name=document_name,
        title=document_name if document_name else "New Chat",
        user_id=user_id,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session

def get_latest_session_for_document(
    db: Session, 
    document_name: str,
    user_id: int,
):
    return(
        db.query(StudySession)
        .filter(
            StudySession.document_name == document_name,
            StudySession.user_id == user_id,
        )
        .order_by(
            StudySession.created_at.desc(),
        )
        .first()
    )

def delete_document(
    db: Session, 
    document_name: str,
    user_id: int,
):
    document = (
        db.query(Document)
        .filter(
            Document.document_name == document_name, 
            Document.user_id == user_id,
            )
        .first()
    )

    if document is None:
        return None
    
    db.delete(document)
    db.commit()

    return document

def get_recent_sessions(
    db: Session,
    user_id: int,
    limit: int = 5,
):
    return(
        db.query(StudySession) 
        .filter(
            StudySession.user_id == user_id,
        )
        .order_by(
            StudySession.created_at.desc()
        )
        .limit(limit)
        .all()
    )

def get_continue_learning(
    db: Session,
    user_id: int,
):
    return(
        db.query(StudySession)
        .filter(
            StudySession.user_id == user_id,
        )
        .order_by(
            StudySession.created_at.desc()
        )
        .first()
    )

def rename_document(
    db: Session,
    old_name: str, 
    new_name: str,
    user_id: int,
):
    document = (
        db.query(Document)
        .filter(
            Document.document_name == old_name, 
            Document.user_id == user_id,
            )

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
    user_id: int,
):
   
    return (
        db.query(Message)
        .join(
            StudySession,
            Message.session_id == StudySession.id,
        )
        .filter(
            Message.session_id == session_id,
            StudySession.user_id == user_id,
        )
        .order_by(
            Message.created_at.asc(),
        )
        .all()
    )

def create_quiz(
    db: Session,
    session_id: str,
    user_id: int,
):
    quiz = Quiz(
        session_id=session_id,
        user_id=user_id,
    )

    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    return quiz

def create_flashcard_set(
    db: Session,
    session_id: str,
    user_id: int,
):

    flashcard = FlashcardSet(
        session_id=session_id,
        user_id=user_id,
    )

    db.add(flashcard)
    db.commit()
    db.refresh(flashcard)

    return flashcard

def get_quiz_count(
    db: Session,
    user_id: int,
):

    return(
        db.query(func.count(Quiz.id))
        .filter(Quiz.user_id == user_id)
        .scalar()
    )

def get_flashcard_count(
    db: Session,
    user_id: int,
):
    return(
        db.query(func.count(FlashcardSet.id))
        .filter(FlashcardSet.user_id == user_id)
        .scalar()
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

def get_user_by_id(
    db: Session,
    user_id: int,
): 
    return(
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )