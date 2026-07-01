from rag.pdf_loader import extract_text_from_pdf
from rag.chunker import chunk_text
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


# ── Request models

class ChatRequest(BaseModel):
    message: str
    pdf_context: Optional[str] = None

class QuizRequest(BaseModel):
    topic: str
    pdf_context: Optional[str] = None
    num_questions: int = 5

class FlashcardRequest(BaseModel):
    topic: str
    pdf_context: Optional[str] = None
    num_cards: int = 8


# ── Helpers 

def clean_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()
    return json.loads(text)

def build_context(pdf_context: Optional[str]) -> str:
    if not pdf_context:
        return ""
    return (
        f"\n\nThe user has uploaded a PDF with the following content:\n"
        f"{pdf_context}\n\nUse this as your primary source when answering."
    )

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

@app.post("/chat")
def chat(req: ChatRequest):
    context = build_context(req.pdf_context)
    system = (
        "You are a smart, friendly AI study tutor called Lumina. "
        "Explain clearly with examples. "
        "If the user seems confused, ask a follow-up question to check understanding. "
        "Keep responses focused and educational."
        + context
    )
    res = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": req.message},
        ],
    )
    title, actions = get_learning_actions(req.message)
    return {
        "response": res.choices[0].message.content,
        "learning_title": title,
        "actions": actions,
    }


@app.post("/quiz")
def generate_quiz(req: QuizRequest):
    context = build_context(req.pdf_context)
    source = "from the uploaded PDF" if req.pdf_context else "using your knowledge"
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
    context = build_context(req.pdf_context)
    source = "from the uploaded PDF" if req.pdf_context else "using your knowledge"
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


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...)
):

    if not file.filename.lower().endswith(".pdf"):
        return {
            "success": False, 
            "message": "Only PDF files are allowed."
        }

    unique_filename = f"{uuid.uuid4()}.pdf"
    
    filepath = os.path.join(
        UPLOAD_DIR, 
        unique_filename,
    )

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(
            file.file, 
            buffer,
        )

    text = extract_text_from_pdf(filepath)

    chunks = chunk_text(text)
    
    return {
        "success": True, 
        "original_filename": file.filename, 
        "stored_filename": unique_filename, 
        "characters": len(text), 
        "total_chunks": len(chunks),
        "chunks": chunks[0],
    }
  
