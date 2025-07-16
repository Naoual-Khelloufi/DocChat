# Embeddings generation
"""Vector embeddings and database functionality for local Ollama setup."""
import logging
from typing import List
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document as LangchainDocument  # Compatibilité avec document.py

logger = logging.getLogger(__name__)

class VectorStore:
    """Handles vector storage and retrieval with Ollama embeddings."""
    
    def __init__(self, embedding_model: str = "nomic-embed-text"):
        """
        Initialize with Ollama embeddings.
        
        Args:
            embedding_model: Name of Ollama model to use (must be pulled locally)
        """
        try:
            self.embeddings = OllamaEmbeddings(
                model=embedding_model,
                base_url="http://localhost:11434"  # Explicit local URL
            )
            self.vector_db = None
            logger.info(f"Initialized Ollama embeddings with model: {embedding_model}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            raise RuntimeError("Ensure Ollama is running (run 'ollama serve')")

    def create_vector_db(
        self, 
        documents: List[LangchainDocument],  # Type matching document.py
        collection_name: str = "local-rag",
        persist_dir: str = None
    ) -> Chroma:
        """
        Create Chroma vectorstore from processed documents.
        
        Args:
            documents: List of documents from DocumentProcessor
            collection_name: Name for the Chroma collection
            persist_dir: Optional directory to persist the database
        """
        try:
            logger.info(f"Creating vector database with {len(documents)} documents")
            
            self.vector_db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=collection_name,
                persist_directory=persist_dir  # Optional persistence
            )
            return self.vector_db
            
        except Exception as e:
            logger.error(f"Vector DB creation failed: {e}")
            raise

    def delete_collection(self) -> None:
        """Cleanup vector database resources."""
        if self.vector_db:
            try:
                logger.info("Deleting vector collection")
                self.vector_db.delete_collection()
                self.vector_db = None
            except Exception as e:
                logger.error(f"Collection deletion failed: {e}")
                raise

    def similarity_search(
        self,
        query: str,
        k: int = 4
    ) -> List[LangchainDocument]:  # Return type matches document.py
        """
        Perform similarity search against stored vectors.
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        if not self.vector_db:
            raise ValueError("Vector database not initialized")
            
        return self.vector_db.similarity_search(query, k=k)