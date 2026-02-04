from pydantic import BaseModel
from typing import List, Optional, Literal

class ChatRequest(BaseModel):
    message: str
    tool: Literal["chat", "find_document"] = "chat"

class FileUploadResponse(BaseModel):
    filename: str
    status: str  # "success", "failed", "partial"
    message: Optional[str] = None  # Detailed status message

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = None
