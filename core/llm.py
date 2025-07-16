"""LLM management for RAG system with local Ollama models."""
import logging
from typing import List
from langchain_ollama.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document as LangchainDocument

logger = logging.getLogger(__name__)

class LLMManager:
    """Handles LLM interactions and prompt engineering for the RAG system."""
    
    def __init__(self, model_name: str = "llama3.2:latest"):
        """
        Initialize the LLM with local Ollama.
        
        Args:
            model_name: Ollama model name (must be pulled locally)
        """
        try:
            self.llm = ChatOllama(
                model=model_name,
                temperature=0.3,  # Balances creativity/factuality
                base_url="http://localhost:11434",  # Matches embeddings.py
                num_ctx=2048, # Consistent context window
                num_threads=2
            )
            logger.info(f"Initialized LLM with model: {model_name}")
        except Exception as e:
            logger.error(f"LLM initialization failed: {e}")
            raise RuntimeError("Ensure Ollama is running and model is downloaded (run 'ollama serve')")

    def generate_answer(
        self,
        context: List[LangchainDocument],  # Type matches document.py/embeddings.py
        question: str,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate answer from context using RAG pattern.
        
        Args:
            context: Documents retrieved from VectorStore
            question: User query
            max_tokens: Limit response length
            
        Returns:
            Generated answer string
        """
        try:
            # Format context from your document chunks
            context_text = "\n\n".join([doc.page_content for doc in context])
            
            response = self.llm.invoke(
                self._get_rag_prompt().format(
                    context=context_text,
                    question=question
                )
            )
            return response.content
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            raise

    def _get_rag_prompt(self) -> ChatPromptTemplate:
        """Core RAG prompt template in English."""
        return ChatPromptTemplate.from_template(
            """Answer the question using ONLY the following context:
            {context}
            
            Question: {question}
            
            Your response should be precise and include relevant details from the context.
            If the answer isn't in the context, say "I don't have that information"."""
        )

    def expand_query(self, question: str) -> List[str]:
        """
        Generate alternative query phrasings for improved retrieval.
        
        Args:
            question: Original user question
            
        Returns:
            List of alternative phrasings (including original)
        """
        try:
            prompt = """Generate 2 alternative phrasings for this search query.
            Maintain the original meaning but vary the wording.
            Original question: {question}
            Responses (1 per line):"""
            
            result = self.llm.invoke(prompt.format(question=question))
            alternatives = result.content.strip().split('\n')
            return [question] + alternatives[:2]  # Keep max 2 alternatives
            
        except Exception as e:
            logger.warning(f"Query expansion failed, using original: {e}")
            return [question]