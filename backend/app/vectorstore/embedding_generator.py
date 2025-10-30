import os
from typing import List, Union
import openai
from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:
    """
    Generates embeddings using OpenAI, HuggingFace, or SentenceTransformers.
    Prioritizes OpenAI if API key is available, falls back to SentenceTransformers.
    """

    def __init__(self, model_name: str = None, provider: str = "auto"):
        """
        Initialize the embedding generator.
        
        Args:
            model_name: Specific model to use (optional)
            provider: 'openai', 'sentence-transformers', or 'auto' (default)
        """
        self.provider = provider
        self.model_name = model_name
        self.model = None
        
        if provider == "auto":
            # Auto-detect based on available resources
            if os.getenv("OPENAI_API_KEY"):
                self.provider = "openai"
                self.model_name = model_name or "text-embedding-3-small"
                openai.api_key = os.getenv("OPENAI_API_KEY")
            else:
                self.provider = "sentence-transformers"
                self.model_name = model_name or "all-MiniLM-L6-v2"
                self.model = SentenceTransformer(self.model_name)
        elif provider == "openai":
            self.model_name = model_name or "text-embedding-3-small"
            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                raise ValueError("OpenAI API key not found in environment")
        elif provider == "sentence-transformers":
            self.model_name = model_name or "all-MiniLM-L6-v2"
            self.model = SentenceTransformer(self.model_name)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def generate_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for given text(s).
        
        Args:
            texts: Single text string or list of text strings
            
        Returns:
            List of embedding vectors
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if self.provider == "openai":
            return self._generate_openai_embeddings(texts)
        elif self.provider == "sentence-transformers":
            return self._generate_sentence_transformer_embeddings(texts)
    
    def _generate_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using OpenAI API.
        """
        response = openai.embeddings.create(
            input=texts,
            model=self.model_name
        )
        return [item.embedding for item in response.data]
    
    def _generate_sentence_transformer_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using SentenceTransformers.
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embeddings produced by this generator.
        """
        if self.provider == "openai":
            # text-embedding-3-small: 1536, text-embedding-3-large: 3072
            if "large" in self.model_name:
                return 3072
            return 1536
        elif self.provider == "sentence-transformers":
            return self.model.get_sentence_embedding_dimension()
