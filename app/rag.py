"""Qdrant retrieval and LiteLLM provider adapters."""
import hashlib
import json
from pathlib import Path

from app.config import SETTINGS
from app.embeddings import EmbeddingModel


class QdrantRetriever:
    def __init__(self, corpus_path="data/documents/corpus.json", embedding_model=None, client=None):
        self.docs = json.loads(Path(corpus_path).read_text(encoding="utf-8"))
        self.embedding = embedding_model or EmbeddingModel()
        if client is None:
            from qdrant_client import QdrantClient
            client = QdrantClient(url=SETTINGS.qdrant_url) if SETTINGS.qdrant_url else QdrantClient(path=SETTINGS.qdrant_path)
        self.client = client
        self.collection = SETTINGS.qdrant_collection

    def close(self):
        """Release the embedded Qdrant storage lock cleanly."""
        close = getattr(self.client, "close", None)
        if close:
            close()

    def index(self, recreate=False):
        from qdrant_client.models import Distance, PointStruct, VectorParams
        names = [item.name for item in self.client.get_collections().collections]
        if recreate and self.collection in names:
            self.client.delete_collection(self.collection)
            names.remove(self.collection)
        if self.collection not in names:
            self.client.create_collection(self.collection, vectors_config=VectorParams(size=self.embedding.dimension, distance=Distance.COSINE))
        points = []
        for doc in self.docs:
            point_id = int(hashlib.sha256(doc["id"].encode()).hexdigest()[:15], 16)
            points.append(PointStruct(id=point_id, vector=self.embedding.embed(doc["text"]), payload={
                "document_id": doc["id"], "id": doc["id"], "title": doc["title"], "text": doc["text"],
                "source": doc.get("source", doc["id"]), "chunk_id": doc["id"] + ":0",
                "corpus_version": SETTINGS.corpus_version,
            }))
        self.client.upsert(self.collection, points=points, wait=True)
        return len(points)

    def retrieve(self, query, k=3):
        from qdrant_client.models import FieldCondition, Filter, MatchValue
        query_vector = self.embedding.embed(query)
        query_filter = Filter(must=[FieldCondition(key="corpus_version", match=MatchValue(value=SETTINGS.corpus_version))])
        if hasattr(self.client, "query_points"):
            hits = self.client.query_points(collection_name=self.collection, query=query_vector, query_filter=query_filter, limit=k).points
        else:
            hits = self.client.search(collection_name=self.collection, query_vector=query_vector, query_filter=query_filter, limit=k)
        return [{"id": hit.payload["document_id"], "title": hit.payload["title"], "text": hit.payload["text"],
                 "source": hit.payload.get("source"), "score": hit.score} for hit in hits]


LocalRetriever = QdrantRetriever


class LiteLLM:
    def __init__(self, api_key=None, timeout=30, completion=None):
        self.api_key, self.timeout, self.completion = api_key, timeout, completion

    def answer(self, query, docs, model):
        if not self.api_key and not self.completion:
            raise RuntimeError("GROQ_API_KEY is not configured. Add it to your local .env file.")
        context = "\n\n".join(f"[{doc['id']}] {doc['text']}" for doc in docs)
        prompt = ("Answer using only the supplied context. If it is insufficient, say exactly: I don't have enough grounded context to answer that. Include no unsupported claims.\n\n"
                  f"Context:\n{context}\n\nQuestion: {query}")
        try:
            if self.completion:
                provider_model = model
                result = self.completion(model=provider_model, messages=[{"role": "user", "content": prompt}], timeout=self.timeout, api_key=self.api_key)
            else:
                import litellm
                provider_model = model
                result = litellm.completion(model=provider_model, messages=[{"role": "user", "content": prompt}], timeout=self.timeout, api_key=self.api_key)
            choice = result.choices[0] if hasattr(result, "choices") else result["choices"][0]
            message = choice.message if hasattr(choice, "message") else choice["message"]
            content = message.content if hasattr(message, "content") else message["content"]
            usage = getattr(result, "usage", None) or (result.get("usage", {}) if isinstance(result, dict) else {})
            inp = (getattr(usage, "prompt_tokens", 0) or getattr(usage, "input_tokens", 0)
                   or (usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0) if isinstance(usage, dict) else 0))
            out = (getattr(usage, "completion_tokens", 0) or getattr(usage, "output_tokens", 0)
                   or (usage.get("completion_tokens", 0) or usage.get("output_tokens", 0) if isinstance(usage, dict) else 0))
            return str(content), int(inp or 0), int(out or 0)
        except Exception as exc:
            raise RuntimeError(f"LLM request failed: {type(exc).__name__}") from exc
