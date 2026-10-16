from app.backend.chain import RAGChain
from app.admin import store
from app.config.settings import get_settings

_rag_chain = None


def initialize_rag_system():
    global _rag_chain
    store.check_ready()
    if get_settings().vector_store == "pinecone":
        from app.backend.vectorstore import get_vectorstore, require_compatible_version

        get_vectorstore()
        require_compatible_version(store.version_info())
    _rag_chain = RAGChain()


def get_rag_chain():
    if _rag_chain is None:
        raise RuntimeError("RAG is not initialized.")
    return _rag_chain
