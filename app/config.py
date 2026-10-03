from dataclasses import dataclass
import os
from dotenv import load_dotenv
load_dotenv()
@dataclass(frozen=True)
class Settings:
    provider: str = os.getenv("LLM_PROVIDER", "groq")
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    small_model: str = os.getenv("SMALL_MODEL", "groq/openai/gpt-oss-20b")
    large_model: str = os.getenv("LARGE_MODEL", "groq/openai/gpt-oss-120b")
    threshold: float = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.60"))
    ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "86400"))
    corpus_version: str = os.getenv("CORPUS_VERSION", "demo-v1")
    data_dir: str = os.getenv("DATA_DIR", "data/runtime")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    qdrant_url: str = os.getenv("QDRANT_URL", "")
    qdrant_path: str = os.getenv("QDRANT_PATH", "data/qdrant")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "rag_documents")
SETTINGS = Settings()
# USD / 1M tokens. Populate only with verified current Groq rates; zero disables estimates.
PRICING = {SETTINGS.small_model: (float(os.getenv("SMALL_MODEL_INPUT_USD_PER_M", "0")), float(os.getenv("SMALL_MODEL_OUTPUT_USD_PER_M", "0"))), SETTINGS.large_model: (float(os.getenv("LARGE_MODEL_INPUT_USD_PER_M", "0")), float(os.getenv("LARGE_MODEL_OUTPUT_USD_PER_M", "0")))}
