import os
import uuid
from typing import List, Tuple, Dict, Any
from PyPDF2 import PdfReader
import re

from app.vectorstore import VectorStoreManager, EmbeddingGenerator


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        # If not at the end, try to break at sentence boundary
        if end < text_length:
            # Look for sentence endings within the last 20% of chunk
            search_start = end - int(chunk_size * 0.2)
            search_text = text[search_start:end + 100]  # Look ahead a bit
            
            # Find the last sentence ending
            sentence_endings = [m.end() for m in re.finditer(r'[.!?]\s+', search_text)]
            if sentence_endings:
                # Use the last sentence ending found
                end = search_start + sentence_endings[-1]
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position, accounting for overlap
        start = end - overlap if end < text_length else text_length
    
    return chunks


def convert_to_markdown(chunks: List[str], document_name: str) -> List[str]:
    """
    Convert text chunks to markdown format.
    
    Args:
        chunks: List of text chunks
        document_name: Name of the source document
        
    Returns:
        List of markdown-formatted chunks
    """
    markdown_chunks = []
    
    for i, chunk in enumerate(chunks, 1):
        # Create markdown with metadata
        markdown = f"# {document_name} - Chunk {i}\n\n"
        markdown += f"---\n\n"
        markdown += chunk
        markdown += f"\n\n---\n"
        markdown += f"*Chunk {i} of {len(chunks)}*"
        markdown_chunks.append(markdown)
    
    return markdown_chunks


def save_chunks_to_disk(
    chunks: List[str], 
    document_id: str, 
    session_id: str, 
    base_dir: str = "backend/app/chunks"
) -> List[str]:
    """
    Save markdown chunks to disk.
    
    Args:
        chunks: List of markdown-formatted chunks
        document_id: Unique identifier for the document
        session_id: Session identifier
        base_dir: Base directory for storing chunks
        
    Returns:
        List of file paths where chunks were saved
    """
    # Create directory structure: base_dir/session_id/document_id/
    chunk_dir = os.path.join(base_dir, session_id, document_id)
    os.makedirs(chunk_dir, exist_ok=True)
    
    file_paths = []
    
    for i, chunk in enumerate(chunks):
        # Save each chunk as a separate markdown file
        filename = f"chunk_{i+1}.md"
        filepath = os.path.join(chunk_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(chunk)
        
        file_paths.append(filepath)
    
    return file_paths


def generate_and_store_embeddings(
    markdown_chunks: List[str],
    document_id: str,
    session_id: str,
    embedding_generator: EmbeddingGenerator,
    vector_store: VectorStoreManager
) -> List[str]:
    """
    Generate embeddings for markdown chunks and store them in vector database.
    
    Args:
        markdown_chunks: List of markdown-formatted text chunks
        document_id: Unique identifier for the document
        session_id: Session identifier
        embedding_generator: Instance of EmbeddingGenerator
        vector_store: Instance of VectorStoreManager
        
    Returns:
        List of vector IDs assigned to stored embeddings
    """
    # Generate embeddings for all chunks in bulk
    embeddings = embedding_generator.generate_embeddings(markdown_chunks)
    
    # Prepare metadata for each chunk
    metadatas = [
        {
            'document_id': document_id,
            'session_id': session_id,
            'chunk_index': i,
            'total_chunks': len(markdown_chunks)
        }
        for i in range(len(markdown_chunks))
    ]
    
    # Bulk add to vector store
    vector_ids = vector_store.add_embeddings(
        embeddings=embeddings,
        documents=markdown_chunks,
        metadatas=metadatas
    )
    
    return vector_ids


def process_pdf(
    pdf_path: str,
    session_id: str = None,
    chunk_size: int = 1000,
    overlap: int = 200,
    base_dir: str = "backend/app/chunks",
    enable_vectorization: bool = True,
    vector_store_dir: str = "./data/vectorstore"
) -> Dict[str, Any]:
    """
    Complete PDF processing pipeline: extract, chunk, convert to markdown, save, 
    and generate embeddings with vector storage.
    
    Args:
        pdf_path: Path to the PDF file
        session_id: Session identifier (generates new if not provided)
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks
        base_dir: Base directory for storing chunks
        enable_vectorization: Whether to generate embeddings and store in vector DB
        vector_store_dir: Directory for vector store persistence
        
    Returns:
        Dictionary containing:
            - document_id: Unique document identifier
            - session_id: Session identifier
            - num_chunks: Number of chunks created
            - file_paths: List of file paths where chunks were saved
            - vector_ids: List of vector IDs (if vectorization enabled)
    """
    # Generate IDs
    document_id = str(uuid.uuid4())
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Extract document name from path
    document_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    
    # Chunk the text
    text_chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    
    # Convert to markdown
    markdown_chunks = convert_to_markdown(text_chunks, document_name)
    
    # Save to disk
    file_paths = save_chunks_to_disk(markdown_chunks, document_id, session_id, base_dir)
    
    result = {
        'document_id': document_id,
        'session_id': session_id,
        'num_chunks': len(markdown_chunks),
        'file_paths': file_paths
    }
    
    # Generate embeddings and store in vector database
    if enable_vectorization:
        try:
            # Initialize embedding generator (auto-detects OpenAI or falls back to SentenceTransformers)
            embedding_generator = EmbeddingGenerator(provider="auto")
            
            # Initialize vector store (prefers ChromaDB, falls back to FAISS)
            vector_store = VectorStoreManager(
                persist_directory=vector_store_dir,
                collection_name="document_chunks",
                use_chroma=True
            )
            
            # Generate embeddings and store them
            vector_ids = generate_and_store_embeddings(
                markdown_chunks=markdown_chunks,
                document_id=document_id,
                session_id=session_id,
                embedding_generator=embedding_generator,
                vector_store=vector_store
            )
            
            result['vector_ids'] = vector_ids
            print(f"Successfully stored {len(vector_ids)} embeddings in vector database")
            
        except Exception as e:
            print(f"Warning: Failed to generate/store embeddings: {str(e)}")
            print("Continuing without vectorization...")
            result['vector_ids'] = []
    else:
        result['vector_ids'] = []
    
    return result
