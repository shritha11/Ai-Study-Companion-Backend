from rag.document_service import DocumentService
from rag.document_repository import DocumentRepository
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AzureOpenAI
from dotenv import load_dotenv
from typing import Optional
import os, json, re, shutil 
from fastapi import UploadFile, File
import uuid

load_dotenv()

app = FastAPI()
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


# ── Request models

class ChatRequest(BaseModel):
    message: str
    document_name: Optional[str] = None

class QuizRequest(BaseModel):
    topic: str
    document_name: Optional[str] = None
    num_questions: int = 5

class FlashcardRequest(BaseModel):
    topic: str
    document_name: Optional[str] = None
    num_cards: int = 8


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
def chat(req: ChatRequest):
    context = ""
    if req.document_name:
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
    res = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": req.message},
        ],
    )
    title, actions = get_learning_actions(req.message)
    return {
        "type": "chat",
        "response": res.choices[0].message.content,
        "learning_title": title,
        "actions": actions,
    }


@app.post("/quiz")
def generate_quiz(req: QuizRequest):
    context = ""

    if req.document_name:

        chunks = document_service.retrieve(
            document_name=req.document_name,
            question=req.topic,
        )

        context = "\n\n".join(chunks)
    source = "from the uploaded PDF" if req.document_name else "using your knowledge"
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
    return clean_json(res.choices[0].message.content)


@app.post("/flashcards")
def generate_flashcards(req: FlashcardRequest):
    context = ""
    if req.document_name:
        chunks = document_service.retrieve(
            document_name=req.document_name,
            question=req.topic,
        )
        context = "\n\n".join(chunks)
    source = "from the uploaded PDF" if req.document_name else "using your knowledge"
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
    return clean_json(res.choices[0].message.content)

@app.get("/documents") 
def get_documents():
    return document_repository.get_all_documents()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...)
):

    ALLOWED_EXTENSIONS = {
        ".pdf", 
        ".docx", 
        ".pptx", 
        ".txt", 
        ".md",
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

    return {
        "success": True,
        "original_filename": file.filename,
        "stored_filename": unique_filename,
        "document_name": document_name,
        "total_chunks": total_chunks
    }
  
