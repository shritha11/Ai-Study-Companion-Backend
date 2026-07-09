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