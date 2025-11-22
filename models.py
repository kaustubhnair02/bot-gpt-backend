from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime
from uuid import uuid4

# Request/Response Schemas
class MessageCreate(BaseModel):
    content: str
    role: Literal["user", "assistant"] = "user"

class ConversationCreate(BaseModel):
    mode: Literal["open_chat", "rag"] = "open_chat"
    first_message: str
    document_id: Optional[str] = None

class ConversationResponse(BaseModel):
    conversation_id: str
    mode: str
    messages: List[dict]
    created_at: datetime
    updated_at: datetime

class DocumentUpload(BaseModel):
    filename: str
    content: str  # Base64 or plain text

# MongoDB Document Models
class ConversationDB(BaseModel):
    """Merged conversation + messages model"""
    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    mode: Literal["open_chat", "rag"]
    document_id: Optional[str] = None
    messages: List[dict] = []  # [{role, content, timestamp, tokens}]
    total_tokens: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentDB(BaseModel):
    """Document storage for RAG"""
    document_id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    chunks: List[dict] = []  # [{chunk_id, text, embedding}]
    total_chunks: int = 0
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
