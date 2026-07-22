from rag.document_service import DocumentService
from rag.document_repository import DocumentRepository
from rag.session_repository import SessionRepository
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AzureOpenAI
from dotenv import load_dotenv
from typing import Optional
import os, json, re, shutil 
from fastapi import UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid
from database.database import engine, get_db
from database.crud import create_document, get_all_documents, delete_document, rename_document, create_session, get_latest_session_for_document, add_message, create_quiz, create_flashcard_set, get_quiz_count, get_flashcard_count, get_messages, get_continue_learning, get_recent_sessions, get_session_count, get_document_count, update_streak
from database.models import Base, User, StudySession
from auth.security import (
    hash_password,
    verify_password,
    create_access_token,
)

from database.schemas import (
    SignupRequest,
    LoginRequest,
    UserResponse,
    DashboardResponse,
    DashboardStats,
)

from database.crud import (
    get_user_by_email,
    create_user,
    get_user_by_id,
)
from auth.security import get_current_user

load_dotenv()

app = FastAPI()
Base.metadata.create_all(bind=engine)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
document_service = DocumentService()
document_repository = DocumentRepository()
session_repository = SessionRepository()


# ── Request models

class ChatRequest(BaseModel):
    message: str
    document_name: Optional[str] = None
    document_names: Optional[list[str]] = None
    session_id: Optional[str] = None

class RenameRequest(BaseModel):
    new_name: str

class QuizRequest(BaseModel):
    topic: str
    document_name: Optional[str] = None
    document_names: Optional[list[str]] = None
    session_id: str
    num_questions: int = 5

class FlashcardRequest(BaseModel):
    topic: str
    document_name: Optional[str] = None
    document_names: Optional[list[str]] = None
    session_id: str
    num_cards: int = 8

class SessionRequest(BaseModel):
    document_name: Optional[str] = None


# ── Helpers 

def clean_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()
    return json.loads(text)


def get_learning_actions(user_message: str):
    text = user_message.lower()
    title = "Choose your next step"
    actions = ["quiz", "flashcards", "summary"]

    if any(w in text for w in ["binary", "tree", "graph", "algorithm", "dsa", "array", "linked list"]):
        title = "Ready to practice?"
        actions.append("coding")
    elif any(w in text for w in ["flutter", "dart", "javascript", "python", "java"]):
        title = "Deepen your understanding"
        actions.append("examples")
    elif any(w in text for w in ["dbms", "database", "sql"]):
        title = "Test your knowledge"
    else:
        actions.append("examples")

    # deduplicate while preserving order
    seen = set()
    unique = []
    for a in actions:
        if a not in seen:
            seen.add(a)
            unique.append(a)

    return title, unique


# ── Routes 

def detect_intent(message: str):
    text = message.lower()

    if "quiz" in text:
        return "quiz"
    
    if "flashcard" in text or "flash card" in text:
        return "flashcards"

    if "summary" in text or "summarize" in text:
        return "summary"

    if "example" in text or "examples" in text:
        return "examples"
    
    if "coding" in text or "practice" in text or "code" in text:
        return "coding"
    
    return "chat"

@app.post("/chat")
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ):
    context = ""
    if req.document_names:
        all_chunks = []

        for document in req.document_names:
            chunks = document_service.retrieve(
                document_name=document,
                question=req.message,
            )
            all_chunks.extend(chunks)

        context = "\n\n".join(all_chunks)

    elif req.document_name:
        chunks = document_service.retrieve(
            document_name=req.document_name,
            question=req.message,
        )

        context = "\n\n".join(chunks)
    
    intent = detect_intent(req.message)

    if intent != "chat":
        return {
            "type": intent, 
            "topic": req.message,
        }
    
    system = f"""
You are Eunoia, an AI study tutor.

When context is provided, use it as your primary source.

Do not invent facts that are not present in the context.

If the answer cannot be found in the provided context, clearly tell the user.

Context:

{context}
"""

    if req.session_id:
        add_message(
            db,
            req.session_id, 
            "user", 
            req.message,
        )

    session = (
        db.query(StudySession)
        .filter(StudySession.id == req.session_id)
        .first()
    )

    if session:
        if session.title == "New Chat":
            session.title = req.message[:60]
            db.commit()

    
    res = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": req.message},
        ],
    )

    answer = res.choices[0].message.content

    if req.session_id:
        add_message(
            db,
            req.session_id, 
            "assistant",
            answer,
        )

    update_streak(
        db, 
        current_user,
    )

    title, actions = get_learning_actions(req.message)

    return {
        "type": "chat",
        "response": answer,
        "learning_title": title,
        "actions": actions,
    }


@app.post("/quiz")
def generate_quiz(
    req: QuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ):
    context = ""

    if req.document_names:
        all_chunks = []

        for document in req.document_names:
            chunks = document_service.retrieve(
                document_name=req.document,
                question=req.topic,
            )
            all_chunks.extend(chunks)

        context = "\n\n".join[:8]

    elif req.document_name:
        chunks = document_service.retrieve(
            document_name=req.document_name,
            question=req.topic,
        )
        context = "\n\n".join(chunks)

    # if req.document_name:

    #     chunks = document_service.retrieve(
    #         document_name=req.document_name,
    #         question=req.topic,
    #     )

    #     context = "\n\n".join(chunks)
    source = (
        "from the uploaded documents"
        if req.document_name or req.document_names
        else "using your knowledge"
    )
    prompt = f"""Generate {req.num_questions} multiple choice questions on "{req.topic}" {source}.{context}

    Return ONLY valid JSON, no explanation, no markdown:
{{
  "questions": [
    {{
      "question": "...",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 0
    }}
  ]
}}

Rules:
- Exactly 4 options per question.
- correct_index is 0-based.
- Vary difficulty from easy to hard.
- Wrong options must be plausible.
- Return only JSON."""

    res = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    create_quiz(
        db=db,
        session_id=req.session_id,
        user_id=current_user.id,
    )

    update_streak(
        db,
        current_user,
    )
    return clean_json(res.choices[0].message.content)


@app.post("/flashcards")
def generate_flashcards(
    req: FlashcardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ):
    context = ""
    if req.document_names:
        all_chunks = []

        for document in req.document_names:
            chunks = document_service.retrieve(
                document_name=req.document,
                question=req.topic,
            )
            all_chunks.extend(chunks)

        context = "\n\n".join[:8]

    elif req.document_name:
        chunks = document_service.retrieve(
            document_name=req.document_name,
            question=req.topic,
        )
        context = "\n\n".join(chunks)
    source = (
        "from the uploaded documents"
        if req.document_name or req.document_names
        else "using your knowledge"
    )
    prompt = f"""Create {req.num_cards} flashcards on "{req.topic}" {source}.{context}

Return ONLY valid JSON, no explanation, no markdown:
{{
  "flashcards": [
    {{
      "front": "Question or term here",
      "back": "Clear, concise answer or definition here"
    }}
  ]
}}

Rules:
- Front should be a question or key term.
- Back should be a clear, memorable answer.
- Cover the most important concepts.
- Return only JSON."""

    res = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        response_format={"type": "json_object"},
    )

    create_flashcard_set(
        db=db,
        session_id=req.session_id,
        user_id=current_user.id,
    )
    update_streak(
        db,
        current_user,
    )
    return clean_json(res.choices[0].message.content)

@app.get("/documents") 
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_all_documents(
        db,
        current_user.id,
        )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.delete("/documents/{document_name}") 
def delete_document_route(
    document_name: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ):

    deleted = delete_document(
        db,
        document_name,
        current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404, 
            detail="Document not found",
        )

    return {
        "success": True,
    }

@app.post("/voice") 
async def voice_chat(file: UploadFile = File(...)):
    audio = await file.read()
    with open("temp_audio.m4a", "wb") as f:
        f.write(audio)

    with open("temp_audio.m4a", "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper",
            file=audio_file,
        )

    return {
        "text": transcript.text
    }

@app.put("/documents/{document_name}")
def rename_document_route(
    document_name: str,
    req: RenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    success = rename_document(
        db,
        document_name,
        req.new_name,
        current_user.id,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return {"success": True}

@app.post("/sessions") 
def create_session_route(
    req: SessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ):

    return create_session(
        db,
        req.document_name,
        current_user.id,
    )

@app.get("/me",response_model= UserResponse,
)
def get_me(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
):
    return get_user_by_id(
        db,
        current_user.id,
    )

@app.get("/dashboard",response_model= DashboardResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db),
):
    return {
        "user": get_user_by_id(
            db,
            current_user.id,
        ),
        "stats": {
            "sessions": get_session_count(
                db,
                current_user.id,
            ),
            "documents": get_document_count(
                db,
                current_user.id,
            ),
            "quizzes": get_quiz_count(
                db, 
                current_user.id,
            ),
            "flashcards": get_flashcard_count(
                db,
                current_user.id,
            ),
        },
        "continue_learning": get_continue_learning(
            db,
            current_user.id,
        ),
        "recent_sessions": get_recent_sessions(
            db,
            current_user.id,
        ),

    }

@app.post("/signup")
def signup(
    req: SignupRequest, 
    db: Session = Depends(get_db),
):
    existing = get_user_by_email(
        db, 
        req.email,
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    user = create_user(
        db,
        req.name,
        req.email,
        hash_password(req.password),
    )

    token = create_access_token({
        "sub": str(user.id),
    })

    return {
        "access_token": token, 
        "user_id": user.id,
        "name": user.name, 
        "email": user.email,
    }

@app.post("/login") 
def login(
    req: LoginRequest, 
    db: Session = Depends(get_db),
):

    user = get_user_by_email(
        db,
        req.email,
    )

    if user is None:
        raise HTTPException(
            status_code=401, 
            detail="Invalid email or password",
        )

    if not verify_password(
        req.password, 
        user.password_hash,
    ): 
        raise HTTPException(
            status_code=401, 
            detail="Invalid email or password",
        )

    token = create_access_token({
        "sub": str(user.id),
    })

    return {
        "access_token": token, 
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
    }

@app.get("/sessions/{document_name}") 
def get_session(
    document_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ):
    session = get_latest_session_for_document(
        db,
        document_name,
        current_user.id,
    )

    if session is None:
        return {
            "exists": False,
        }

    return {
        "exists": True, 
        "session": session,
    }

@app.get("/sessions/{session_id}/messages")
def get_messages_route(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_messages(
        db,
        session_id,
        current_user.id,
    )

@app.post("/upload")
async def upload_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...)
):

    ALLOWED_EXTENSIONS = {
        ".pdf", 
        ".docx", 
        ".pptx", 
        ".txt", 
        ".md",
        ".jpg",
        ".jpeg",
        ".png",
   }

    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return {
            "success": False, 
            "message": "Unsupported file type."
        }

    unique_filename = f"{uuid.uuid4()}{extension}"
    
    filepath = os.path.join(
        UPLOAD_DIR, 
        unique_filename,
    )

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(
            file.file, 
            buffer,
        )

    document_name = os.path.splitext(file.filename)[0]
    total_chunks = document_service.process_document(
        file_path=filepath, 
        document_name=document_name,
        original_filename=file.filename, 
        stored_filename=unique_filename,
    )
    create_document(
        db=db,
        document_name=document_name, 
        original_filename=file.filename, 
        stored_filename=unique_filename, 
        total_chunks=total_chunks,
        user_id=current_user.id,
    )

    return {
        "success": True,
        "original_filename": file.filename,
        "stored_filename": unique_filename,
        "document_name": document_name,
        "total_chunks": total_chunks
    }
  
