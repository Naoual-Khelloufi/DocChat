from core.llm import LLMManager
from core.rag import RAGPipeline
from core.embeddings import VectorStore

vs = VectorStore()
llm = LLMManager()
pipe = RAGPipeline(vs, llm)

print(pipe.get_response("c'est quoi l'intelligence artificielle ?"))
