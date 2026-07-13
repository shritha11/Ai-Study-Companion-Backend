from pydantic import BaseModel 
from datetime import datetime

class DocumentBase(BaseModel):
    document_name: str
    original_filename: str
    stored_filename: str
    total_chunks: int

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True
        
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class DashboardStats(BaseModel):
    sessions: int
    documents: int
    quizzes: int = 0
    flashcards: int = 0

class DashboardResponse(BaseModel):
    user: UserResponse
    stats: DashboardStats

