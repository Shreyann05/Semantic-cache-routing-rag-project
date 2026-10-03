"""Validate and index the current corpus into configured Qdrant."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.rag import QdrantRetriever


if __name__ == "__main__":
    docs = json.loads(Path("data/documents/corpus.json").read_text(encoding="utf-8"))
    if not docs or not all({"id", "title", "text"} <= d.keys() and d["text"].strip() for d in docs):
        raise ValueError("Corpus contains an invalid or empty document")
    retriever = QdrantRetriever()
    try:
        count = retriever.index(recreate=True)
        print(
            f"Indexed {count} documents into {retriever.collection}; "
            f"model={retriever.embedding.model_name}, dimension={retriever.embedding.dimension}"
        )
    finally:
        retriever.close()
