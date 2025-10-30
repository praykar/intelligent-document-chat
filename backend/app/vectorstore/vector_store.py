import os
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import faiss
import numpy as np
import pickle
from pathlib import Path


class VectorStoreManager:
    """
    Manages vector storage using ChromaDB (preferred) or FAISS (fallback).
    Handles embedding storage and retrieval for document chunks.
    """

    def __init__(self, 
                 persist_directory: str = "./data/vectorstore",
                 collection_name: str = "document_chunks",
                 use_chroma: bool = True):
        """
        Initialize the vector store manager.
        
        Args:
            persist_directory: Directory to persist vector store data
            collection_name: Name of the collection/index
            use_chroma: Whether to use ChromaDB (True) or FAISS (False)
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.use_chroma = use_chroma
        
        # Create persist directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        if use_chroma:
            self._initialize_chroma()
        else:
            self._initialize_faiss()
    
    def _initialize_chroma(self):
        """
        Initialize ChromaDB with persistent storage.
        """
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"ChromaDB initialized with collection: {self.collection_name}")
        except Exception as e:
            print(f"Failed to initialize ChromaDB: {e}")
            print("Falling back to FAISS...")
            self.use_chroma = False
            self._initialize_faiss()
    
    def _initialize_faiss(self):
        """
        Initialize FAISS index as fallback.
        """
        self.index = None
        self.id_map = {}
        self.metadata_store = {}
        self.dimension = None
        
        # Try to load existing index
        index_path = os.path.join(self.persist_directory, f"{self.collection_name}.index")
        metadata_path = os.path.join(self.persist_directory, f"{self.collection_name}.metadata")
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            self.index = faiss.read_index(index_path)
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.id_map = data['id_map']
                self.metadata_store = data['metadata_store']
                self.dimension = data['dimension']
            print(f"FAISS index loaded from {index_path}")
        else:
            print("No existing FAISS index found. Will create on first add.")
    
    def add_embeddings(self,
                      embeddings: List[List[float]],
                      documents: List[str],
                      metadatas: List[Dict[str, Any]],
                      ids: Optional[List[str]] = None) -> List[str]:
        """
        Add embeddings to the vector store.
        
        Args:
            embeddings: List of embedding vectors
            documents: List of document text chunks
            metadatas: List of metadata dictionaries for each chunk
            ids: Optional list of IDs (will be generated if not provided)
            
        Returns:
            List of IDs assigned to the added embeddings
        """
        if ids is None:
            # Generate IDs based on document_id and chunk_index from metadata
            ids = [
                f"{meta.get('document_id', 'doc')}_{meta.get('chunk_index', i)}"
                for i, meta in enumerate(metadatas)
            ]
        
        if self.use_chroma:
            return self._add_to_chroma(embeddings, documents, metadatas, ids)
        else:
            return self._add_to_faiss(embeddings, documents, metadatas, ids)
    
    def _add_to_chroma(self,
                       embeddings: List[List[float]],
                       documents: List[str],
                       metadatas: List[Dict[str, Any]],
                       ids: List[str]) -> List[str]:
        """
        Add embeddings to ChromaDB.
        """
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        return ids
    
    def _add_to_faiss(self,
                      embeddings: List[List[float]],
                      documents: List[str],
                      metadatas: List[Dict[str, Any]],
                      ids: List[str]) -> List[str]:
        """
        Add embeddings to FAISS index.
        """
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Initialize index if this is the first add
        if self.index is None:
            self.dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatL2(self.dimension)
        
        # Add vectors to index
        start_idx = self.index.ntotal
        self.index.add(embeddings_array)
        
        # Store metadata and ID mapping
        for i, (doc, meta, doc_id) in enumerate(zip(documents, metadatas, ids)):
            idx = start_idx + i
            self.id_map[doc_id] = idx
            self.metadata_store[idx] = {
                'id': doc_id,
                'document': doc,
                'metadata': meta
            }
        
        # Persist FAISS index
        self._persist_faiss()
        return ids
    
    def _persist_faiss(self):
        """
        Persist FAISS index and metadata to disk.
        """
        index_path = os.path.join(self.persist_directory, f"{self.collection_name}.index")
        metadata_path = os.path.join(self.persist_directory, f"{self.collection_name}.metadata")
        
        faiss.write_index(self.index, index_path)
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'id_map': self.id_map,
                'metadata_store': self.metadata_store,
                'dimension': self.dimension
            }, f)
    
    def query(self,
              query_embeddings: List[List[float]],
              n_results: int = 5,
              where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query the vector store for similar embeddings.
        
        Args:
            query_embeddings: List of query embedding vectors
            n_results: Number of results to return per query
            where: Optional metadata filter (ChromaDB only)
            
        Returns:
            Dictionary containing ids, documents, metadatas, and distances
        """
        if self.use_chroma:
            return self._query_chroma(query_embeddings, n_results, where)
        else:
            return self._query_faiss(query_embeddings, n_results)
    
    def _query_chroma(self,
                      query_embeddings: List[List[float]],
                      n_results: int,
                      where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query ChromaDB.
        """
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )
        return results
    
    def _query_faiss(self,
                     query_embeddings: List[List[float]],
                     n_results: int) -> Dict[str, Any]:
        """
        Query FAISS index.
        """
        if self.index is None or self.index.ntotal == 0:
            return {'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
        
        query_array = np.array(query_embeddings).astype('float32')
        distances, indices = self.index.search(query_array, n_results)
        
        # Format results similar to ChromaDB
        results = {
            'ids': [],
            'documents': [],
            'metadatas': [],
            'distances': []
        }
        
        for i, (dist_list, idx_list) in enumerate(zip(distances, indices)):
            query_ids = []
            query_docs = []
            query_metas = []
            query_dists = []
            
            for dist, idx in zip(dist_list, idx_list):
                if idx in self.metadata_store:
                    stored = self.metadata_store[idx]
                    query_ids.append(stored['id'])
                    query_docs.append(stored['document'])
                    query_metas.append(stored['metadata'])
                    query_dists.append(float(dist))
            
            results['ids'].append(query_ids)
            results['documents'].append(query_docs)
            results['metadatas'].append(query_metas)
            results['distances'].append(query_dists)
        
        return results
    
    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        """
        Retrieve documents by their IDs.
        
        Args:
            ids: List of document IDs
            
        Returns:
            Dictionary containing documents and metadatas
        """
        if self.use_chroma:
            return self.collection.get(ids=ids)
        else:
            # FAISS implementation
            results = {'ids': [], 'documents': [], 'metadatas': []}
            for doc_id in ids:
                if doc_id in self.id_map:
                    idx = self.id_map[doc_id]
                    if idx in self.metadata_store:
                        stored = self.metadata_store[idx]
                        results['ids'].append(stored['id'])
                        results['documents'].append(stored['document'])
                        results['metadatas'].append(stored['metadata'])
            return results
    
    def delete_by_document_id(self, document_id: str):
        """
        Delete all chunks associated with a document.
        
        Args:
            document_id: The document ID to delete
        """
        if self.use_chroma:
            self.collection.delete(
                where={"document_id": document_id}
            )
        else:
            # FAISS doesn't support efficient deletion
            # We'd need to rebuild the index without these items
            print(f"Warning: FAISS doesn't support efficient deletion. "
                  f"Consider using ChromaDB for better delete support.")
    
    def count(self) -> int:
        """
        Get the total number of embeddings in the store.
        """
        if self.use_chroma:
            return self.collection.count()
        else:
            return self.index.ntotal if self.index else 0
