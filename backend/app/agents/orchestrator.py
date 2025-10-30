"""Orchestrator for managing chat flow between query agent, vector store, and response agent."""

from typing import Dict, Any, List, Optional
from .query_agent import QueryAgent
from .response_agent import ResponseAgent


class ChatOrchestrator:
    """Orchestrates the chat flow using query and response agents."""

    def __init__(self, vector_store=None):
        """Initialize the orchestrator with agents and vector store.
        
        Args:
            vector_store: Vector store instance for retrieving document chunks
        """
        self.query_agent = QueryAgent()
        self.response_agent = ResponseAgent()
        self.vector_store = vector_store

    def set_vector_store(self, vector_store):
        """Set or update the vector store.
        
        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store

    def process_chat(self, user_query: str, top_k: int = 5) -> Dict[str, Any]:
        """Process a chat query through the full pipeline.
        
        Args:
            user_query: User's input query
            top_k: Number of chunks to retrieve from vector store
            
        Returns:
            Dict containing response, rephrased query, retrieved chunks, and follow-up questions
        """
        # Step 1: Validate and rephrase query
        rephrased_query = self.query_agent.process_query(user_query)
        
        if not rephrased_query:
            return {
                "success": False,
                "error": "Invalid or empty query. Please provide a meaningful question.",
                "original_query": user_query,
                "response": None,
                "chunks": [],
                "followup_questions": []
            }
        
        # Step 2: Retrieve relevant chunks from vector store
        chunks = []
        if self.vector_store:
            try:
                # Use rephrased query for better retrieval
                chunks = self.vector_store.search(rephrased_query, top_k=top_k)
            except Exception as e:
                print(f"Error retrieving from vector store: {e}")
                chunks = []
        
        # Step 3: Generate response using retrieved context
        response = self.response_agent.generate_response(rephrased_query, chunks)
        
        # Step 4: Generate follow-up questions (optional)
        followup_questions = self.response_agent.generate_followup_questions(
            user_query, response
        )
        
        return {
            "success": True,
            "original_query": user_query,
            "rephrased_query": rephrased_query,
            "response": response,
            "chunks": chunks,
            "followup_questions": followup_questions,
            "num_chunks_retrieved": len(chunks)
        }

    def process_chat_stream(self, user_query: str, top_k: int = 5):
        """Process chat query with streaming response (future enhancement).
        
        Args:
            user_query: User's input query
            top_k: Number of chunks to retrieve
            
        Yields:
            Dict containing partial responses or final result
        """
        # For now, just return the complete result
        # This can be enhanced with actual streaming in the future
        result = self.process_chat(user_query, top_k)
        yield result
