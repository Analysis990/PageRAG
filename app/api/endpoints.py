from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas import ChatRequest, ChatResponse, FileUploadResponse
from app.services import rag_service, pageindex_service
import shutil
import os

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if request.tool == "find_document":
            # Use PageIndex Service
            answer, sources = await pageindex_service.query(request.message)
            return ChatResponse(response=answer, sources=sources)
        else:
             # Use Basic RAG Service (LangChain)
            answer, sources = await rag_service.query(request.message)
            return ChatResponse(response=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # Save file to data/file for PageIndex
    file_location = f"data/file/{file.filename}"
    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return FileUploadResponse(filename=file.filename, status="File uploaded successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
