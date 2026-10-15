from app.backend.chain import RAGChain
from app.admin import store

_rag_chain = None


def initialize_rag_system():
    global _rag_chain
    store.check_ready()
    _rag_chain = RAGChain()


def get_rag_chain():
    if _rag_chain is None:
        raise RuntimeError("RAG is not initialized.")
    return _rag_chain
