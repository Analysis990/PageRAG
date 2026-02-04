from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas import ChatRequest, ChatResponse, FileUploadResponse
from app.services import rag_service, pageindex_service
import shutil
import os

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    print(f"DEBUG: Received chat request - Tool: {request.tool}, Message: {request.message[:50]}...")
    try:
        if request.tool == "find_document":
            print("DEBUG: Using PageIndex Service")
            answer, sources = await pageindex_service.query(request.message)
            return ChatResponse(response=answer, sources=sources)
        else:
            print(f"DEBUG: Using RAG Service (Tool: {request.tool})")
            answer, sources = await rag_service.query(request.message)
            return ChatResponse(response=answer, sources=sources)
    except Exception as e:
        print(f"DEBUG: Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload PDF file and automatically process it with PageIndex.
    Saves to lib/PageIndex/tests/pdfs and outputs to lib/PageIndex/tests/results.
    """
    import subprocess
    import asyncio
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save file to PageIndex tests directory
    file_location = f"lib/PageIndex/tests/pdfs/{file.filename}"
    
    try:
        # Ensure directory exists
        os.makedirs("lib/PageIndex/tests/pdfs", exist_ok=True)
        
        # Save uploaded file
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        # Automatically trigger PageIndex processing
        try:
            # Run the processing script
            result = subprocess.run(
                ["python", "scripts/process_pageindex.py"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Check if processing was successful
            if result.returncode == 0:
                # Extract document name (without .pdf extension)
                doc_name = os.path.splitext(file.filename)[0]
                output_file = f"lib/PageIndex/tests/results/{doc_name}_structure.json"
                
                # Verify result file was created
                if os.path.exists(output_file):
                    return FileUploadResponse(
                        filename=file.filename,
                        status="success",
                        message=f"File uploaded and processed successfully. Index saved to {output_file}"
                    )
                else:
                    return FileUploadResponse(
                        filename=file.filename,
                        status="partial",
                        message="File uploaded but processing output not found. Check logs."
                    )
            else:
                error_msg = result.stderr if result.stderr else "Unknown processing error"
                return FileUploadResponse(
                    filename=file.filename,
                    status="failed",
                    message=f"Processing failed: {error_msg[:200]}"
                )
                
        except subprocess.TimeoutExpired:
            return FileUploadResponse(
                filename=file.filename,
                status="failed",
                message="Processing timeout (exceeded 5 minutes)"
            )
        except Exception as proc_error:
            return FileUploadResponse(
                filename=file.filename,
                status="failed",
                message=f"Processing error: {str(proc_error)}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
