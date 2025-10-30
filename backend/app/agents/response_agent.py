"""Response Agent for generating responses using Gemini API with retrieved context."""

import google.generativeai as genai
from typing import List, Dict, Any
import os


class ResponseAgent:
    """Agent for generating responses using retrieved context."""

    def __init__(self):
        """Initialize the Response Agent with Gemini API."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into context string.
        
        Args:
            chunks: List of retrieved document chunks with metadata
            
        Returns:
            str: Formatted context string
        """
        if not chunks:
            return "No relevant context found."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get('content', chunk.get('text', ''))
            metadata = chunk.get('metadata', {})
            source = metadata.get('source', 'Unknown')
            
            context_parts.append(
                f"[Context {i}] (Source: {source})\n{content}\n"
            )
        
        return "\n".join(context_parts)

    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Generate response using query and retrieved context.
        
        Args:
            query: User's query (potentially rephrased)
            context_chunks: Retrieved document chunks
            
        Returns:
            str: Generated response
        """
        context = self.format_context(context_chunks)
        
        prompt = f"""You are a helpful AI assistant that answers questions based on the provided context.

Context from documents:
{context}

User Question: {query}

Instructions:
- Answer the question using ONLY the information from the provided context
- If the context doesn't contain enough information to answer the question, say so clearly
- Be concise but comprehensive
- Cite which context section(s) you used if relevant
- If multiple contexts provide information, synthesize them coherently

Answer:"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def generate_followup_questions(self, query: str, response: str) -> List[str]:
        """Generate relevant follow-up questions based on the query and response.
        
        Args:
            query: Original user query
            response: Generated response
            
        Returns:
            List[str]: List of follow-up questions
        """
        prompt = f"""Based on this Q&A, suggest 3 relevant follow-up questions the user might ask:

Question: {query}
Answer: {response}

Provide only the questions, one per line, without numbering."""
        
        try:
            result = self.model.generate_content(prompt)
            questions = [q.strip() for q in result.text.strip().split('\n') if q.strip()]
            return questions[:3]  # Limit to 3 questions
        except Exception as e:
            print(f"Error generating follow-up questions: {e}")
            return []
