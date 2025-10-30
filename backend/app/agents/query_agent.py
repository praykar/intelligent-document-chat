"""Query Agent for rephrasing and validation using Gemini API."""

import google.generativeai as genai
from typing import Optional
import os


class QueryAgent:
    """Agent for query rephrasing and validation."""

    def __init__(self):
        """Initialize the Query Agent with Gemini API."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def validate_query(self, query: str) -> bool:
        """Validate if the query is meaningful and processable.
        
        Args:
            query: User's input query
            
        Returns:
            bool: True if query is valid, False otherwise
        """
        if not query or len(query.strip()) < 3:
            return False
        return True

    def rephrase_query(self, query: str) -> str:
        """Rephrase the user query for better context retrieval.
        
        Args:
            query: Original user query
            
        Returns:
            str: Rephrased query optimized for semantic search
        """
        if not self.validate_query(query):
            return query
        
        prompt = f"""Rephrase the following question to be clear, specific, and optimized for semantic search in a document database. 
Keep it concise and maintain the original intent.

Original question: {query}

Rephrased question:"""
        
        try:
            response = self.model.generate_content(prompt)
            rephrased = response.text.strip()
            return rephrased if rephrased else query
        except Exception as e:
            print(f"Error rephrasing query: {e}")
            return query

    def process_query(self, query: str) -> Optional[str]:
        """Process and validate the query, returning rephrased version.
        
        Args:
            query: User's input query
            
        Returns:
            Optional[str]: Rephrased query if valid, None otherwise
        """
        if not self.validate_query(query):
            return None
        
        return self.rephrase_query(query)
