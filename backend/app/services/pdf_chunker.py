import os
import uuid
from typing import List, Tuple
from PyPDF2 import PdfReader
import re

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

def save_chunks_to_disk(chunks: List[str], document_id: str, session_id: str, base_dir: str = "backend/app/chunks") -> List[str]:
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

def process_pdf(
    pdf_path: str,
    session_id: str = None,
    chunk_size: int = 1000,
    overlap: int = 200,
    base_dir: str = "backend/app/chunks"
) -> Tuple[str, str, int, List[str]]:
    """
    Complete PDF processing pipeline: extract, chunk, convert to markdown, and save.
    
    Args:
        pdf_path: Path to the PDF file
        session_id: Session identifier (generates new if not provided)
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks
        base_dir: Base directory for storing chunks
        
    Returns:
        Tuple of (document_id, session_id, number_of_chunks, file_paths)
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
    
    return document_id, session_id, len(markdown_chunks), file_paths
