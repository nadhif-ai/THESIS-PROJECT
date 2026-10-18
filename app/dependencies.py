from app.backend.chain import RAGChain
from app.admin import store
from app.config.settings import get_settings
import threading

_rag_chain = None
_rag_lock = threading.RLock()


def initialize_rag_system():
    global _rag_chain
    store.check_ready()
    if get_settings().vector_store == "pinecone":
        from app.backend.vectorstore import get_vectorstore, require_compatible_version
        from app.admin.kb_store import active_info
        active = active_info()
        if active and not active["manifest"].get("empty"):
            get_vectorstore()
            require_compatible_version(active)
    _rag_chain = RAGChain()


def get_rag_chain():
    global _rag_chain
    if _rag_chain is None:
        with _rag_lock:
            if _rag_chain is None:
                _rag_chain = RAGChain()
    return _rag_chain
