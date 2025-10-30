from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import tempfile
from app.services.pdf_chunker import process_pdf

app = FastAPI(
    title="Intelligent Document Chat API",
    description="Backend API for document chat application",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: Optional[List[str]] = None

class UploadResponse(BaseModel):
    message: str
    document_id: str
    session_id: str
    num_chunks: int

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Intelligent Document Chat API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# File upload endpoint
@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), session_id: Optional[str] = None):
    """
    Upload a PDF document for processing.
    The document will be extracted, chunked, converted to markdown, and saved to disk.
    """
    # Validate file type (PDF)
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Create a temporary file to save the uploaded PDF
    temp_file = None
    try:
        # Create temporary file with PDF extension
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Save uploaded file to temporary location
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        # Process the PDF: extract text, chunk, convert to markdown, and save
        document_id, returned_session_id, num_chunks, file_paths = process_pdf(
            pdf_path=temp_file_path,
            session_id=session_id,
            chunk_size=1000,
            overlap=200,
            base_dir="backend/app/chunks"
        )
        
        return UploadResponse(
            message=f"Document uploaded and processed successfully. {num_chunks} chunks created.",
            document_id=document_id,
            session_id=returned_session_id,
            num_chunks=num_chunks
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass

# Chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a user query and return a response.
    Flow:
    1. Agent 1: Rephrase query with self-validation & reasoning
    2. Fetch relevant context from vector store
    3. Agent 2: Generate response based on context
    """
    # TODO: Implement chat logic
    # - Use Agent 1 to rephrase and understand query
    # - Retrieve relevant chunks from vector store
    # - Use Agent 2 to draft response
    # - Return response with sources
    
    return ChatResponse(
        response="This is a placeholder response. Chat logic not yet implemented.",
        session_id=request.session_id or "session_placeholder_123",
        sources=[]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
