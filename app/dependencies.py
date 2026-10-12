from app.backend.chain import RAGChain
from app.admin import store, knowledge
from app.config.settings import get_settings

_rag_chain = None


def initialize_rag_system(recover_jobs=False):
    global _rag_chain
    store.initialize(recover_jobs=recover_jobs)
    if get_settings().vector_store == "pinecone":
        knowledge.bootstrap()
    _rag_chain = RAGChain()


def get_rag_chain():
    if _rag_chain is None:
        raise RuntimeError("RAG is not initialized.")
    return _rag_chain
