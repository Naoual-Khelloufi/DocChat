# RAG pipeline (LangChain)
"""RAG pipeline core functionality - simplified version."""
import logging
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class RAGPipeline:
    """Simplified RAG pipeline with basic retrieval and generation."""
    
    def __init__(self, vector_store, llm_manager):
        """
        Initialize with pre-configured components.
        
        Args:
            vector_store: Your VectorStore instance from embeddings.py
            llm_manager: Your LLMManager instance from llm.py
        """
        self.vector_store = vector_store
        self.llm_manager = llm_manager
        self.chain = self._setup_simple_chain()

    def _setup_simple_chain(self):
        """Build minimal RAG chain without advanced retrieval."""
        try:
            return (
                {"context": self._retrieve_context, "question": RunnablePassthrough()}
                | self.llm_manager._get_rag_prompt()
                | self.llm_manager.llm
                | StrOutputParser()
            )
        except Exception as e:
            logger.error(f"Failed to setup chain: {e}")
            raise RuntimeError("Chain initialization error")

    def _retrieve_context(self, question: str):
        """Basic retrieval using your existing vector store."""
        return self.vector_store.similarity_search(question, k=4)

    #def get_response(self, question: str) -> str:
        """
        Get answer to user question.
        
        Args:
            question: User query string
            
        Returns:
            Generated answer
        """
    #    try:
    #        logger.info(f"Processing question: {question[:50]}...")
    #        return self.chain.invoke(question)
    #    except Exception as e:
    #        logger.error(f"Response generation failed: {e}")
    #        raise RuntimeError("Please check your input and try again")

    def get_response(self, question: str) -> str:
        """
        Get answer to user question.
        - Si aucun document n'est disponible/retourné -> réponse générale
        - Sinon -> RAG (chaîne existante)
        """
        try:
            # 1) On tente la recherche
            docs = self._retrieve_context(question)
            if not docs:   # Fallback simple
                # Réponse générale (sans contexte)
                return self.llm_manager.generate_general(question, max_tokens=600)

            # 2) Sinon: on passe par la chaîne RAG (comme avant)
            logger.info(f"Processing question: {question[:50]}...")
            return self.chain.invoke(question)

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise RuntimeError("Please check your input and try again")