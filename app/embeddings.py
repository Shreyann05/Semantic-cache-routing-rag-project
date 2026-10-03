from functools import lru_cache
from app.config import SETTINGS


@lru_cache(maxsize=2)
def _load_model(name):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(name, local_files_only=True)


class EmbeddingModel:
    def __init__(self, model_name=None):
        self.model_name = model_name or SETTINGS.embedding_model

    @property
    def dimension(self):
        model = _load_model(self.model_name)
        getter = getattr(model, "get_embedding_dimension", None) or model.get_sentence_embedding_dimension
        return int(getter())

    def embed(self, text):
        return self.embed_many([text])[0]

    def embed_many(self, texts):
        vectors = _load_model(self.model_name).encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return vectors.tolist()


def embed(text):
    return EmbeddingModel().embed(text)


def cosine(a, b):
    return max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
