from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Date

from database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    email = Column(
        String,
        unique=True,
        nullable=False,
    )

    password_hash = Column(
        String, 
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    current_streak = Column(
        Integer,
        default=0,
        nullable=False,
    )

    longest_streak = Column(
        Integer,
        default=0,
        nullable=False,
    )

    last_study_date = Column(
        Date,
        nullable=True,
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    document_name = Column(
        String,
        nullable=False,
    )

    original_filename = Column(
        String,
        nullable=False,
    )

    stored_filename = Column(
        String,
        nullable=False,
    )

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    total_chunks = Column(Integer)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
    )

    user = relationship("User")

class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(String, primary_key=True)

    document_name = Column(String)
    
    title = Column(
        String,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(), 
        onupdate=func.now(),
    )

    user_id = Column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=False,
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(
        Integer, 
        primary_key=True, 
        index=True,
    )

    session_id = Column(
        String, 
        ForeignKey("study_sessions.id"),
        nullable=False,
    )

    role = Column(
        String, 
        nullable=False,
    )

    content = Column(
        String, 
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    session_id = Column(
        String,
        ForeignKey("study_sessions.id"),
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    session = relationship("StudySession")
    user = relationship("User")

class FlashcardSet(Base):
    __tablename__ = "flashcard_sets"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    session_id = Column(
        String, 
        ForeignKey("study_sessions.id"),
        nullable=False,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    session = relationship("StudySession")
    user = relationship("User")