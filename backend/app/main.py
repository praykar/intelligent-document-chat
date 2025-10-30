from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import tempfile
from app.services.pdf_chunker import process_pdf
from app.agents.orchestrator import ChatOrchestrator
from app.vectorstore.chroma_store import ChromaVectorStore

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

# Global instances
chat_orchestrator: Optional[ChatOrchestrator] = None
vector_store: Optional[ChromaVectorStore] = None

# Request/Response Models
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    top_k: Optional[int] = 5

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: Optional[List[str]] = None
    rephrased_query: Optional[str] = None
    followup_questions: Optional[List[str]] = None
    num_chunks_retrieved: Optional[int] = 0

class UploadResponse(BaseModel):
    message: str
    document_id: str
    session_id: str
    num_chunks: int

# Startup event to initialize agents and vector store
@app.on_event("startup")
async def startup_event():
    """Initialize the chat orchestrator and vector store on startup."""
    global chat_orchestrator, vector_store
    
    try:
        # Initialize vector store
        vector_store = ChromaVectorStore()
        
        # Initialize chat orchestrator with vector store
        chat_orchestrator = ChatOrchestrator(vector_store=vector_store)
        
        print("✓ Chat orchestrator and vector store initialized successfully")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize chat components: {e}")
        print("  Chat functionality may be limited until vector store is set up")

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
        
        # Add chunks to vector store if available
        if vector_store:
            try:
                vector_store.add_documents_from_session(returned_session_id)
                print(f"✓ Added {num_chunks} chunks to vector store")
            except Exception as e:
                print(f"⚠ Warning: Could not add chunks to vector store: {e}")
        
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
    1. Agent 1 (QueryAgent): Rephrase query with validation & reasoning
    2. Fetch relevant context from vector store
    3. Agent 2 (ResponseAgent): Generate response based on context
    """
    global chat_orchestrator
    
    # Check if orchestrator is initialized
    if not chat_orchestrator:
        raise HTTPException(
            status_code=503, 
            detail="Chat service not initialized. Please ensure GEMINI_API_KEY is set."
        )
    
    try:
        # Process the chat query through the orchestrator
        result = chat_orchestrator.process_chat(
            user_query=request.query,
            top_k=request.top_k or 5
        )
        
        # Handle validation errors
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Invalid query")
            )
        
        # Extract sources from chunks
        sources = []
        for chunk in result.get("chunks", []):
            metadata = chunk.get("metadata", {})
            source = metadata.get("source", "Unknown")
            if source not in sources:
                sources.append(source)
        
        return ChatResponse(
            response=result.get("response", "No response generated"),
            session_id=request.session_id or "default_session",
            sources=sources if sources else None,
            rephrased_query=result.get("rephrased_query"),
            followup_questions=result.get("followup_questions"),
            num_chunks_retrieved=result.get("num_chunks_retrieved", 0)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
