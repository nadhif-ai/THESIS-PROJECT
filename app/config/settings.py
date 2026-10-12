from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Literal
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """
    Kelas penampung seluruh konfigurasi aplikasi yang dibaca dari file .env.

    Pydantic-settings secara otomatis mencocokkan nama field dengan nama
    variabel di file .env. Semua nilai dapat diubah tanpa mengubah kode program.

    Attributes:
        openrouter_api_key     : API Key rahasia untuk mengakses layanan OpenRouter.
        openrouter_model       : nama model LLM yang digunakan melalui OpenRouter.
        openrouter_base_url    : URL endpoint API OpenRouter.
        embedding_model        : nama model embedding HuggingFace yang digunakan.
        chroma_persist_dir     : path folder penyimpanan database vektor ChromaDB.
        chroma_collection_name : nama koleksi di dalam ChromaDB.
        api_host               : alamat IP tempat server FastAPI berjalan.
        api_port               : nomor port tempat server FastAPI mendengarkan request.
        semantic_top_k         : jumlah dokumen teratas yang diambil saat pencarian semantik.
        structured_kb_dir      : path folder yang berisi file-file dataset CSV.
        log_level              : tingkat detail pencatatan log (INFO, DEBUG, WARNING).
    """

    openrouter_api_key: str = Field(...)
    openrouter_model: str = Field(default="google/gemini-2.5-flash")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    embedding_model: str = Field(default="intfloat/multilingual-e5-small")

    chroma_persist_dir: str = Field(default="./chroma_db")
    chroma_collection_name: str = "printing_knowledge_base"

    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    semantic_top_k: int = Field(default=10)
    structured_kb_dir: str = Field(default="./dataset")
    log_level: str = Field(default="INFO")

    fonnte_token: str = Field(default="")
    vector_store: Literal["pinecone", "chroma"] = "pinecone"
    pinecone_api_key: str = ""
    pinecone_index_name: str = "chatbot-avg"
    data_dir: str = "./data"
    eval_model: str = "google/gemini-2.5-flash"
    admin_username: str = "admin"
    admin_password: str = ""
    cookie_secure: bool = False
    allowed_origins: str = "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:5173,http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Membuat dan mengembalikan instance Settings dari file .env (dengan cache).

    Menggunakan lru_cache agar file .env hanya dibaca satu kali selama
    aplikasi berjalan, bukan setiap kali fungsi dipanggil.

    Returns:
        Instance Settings berisi semua konfigurasi aplikasi.
    """
    return Settings()
