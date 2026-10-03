"""Validate the local corpus; production adapters can push these documents to Qdrant."""
import json
from pathlib import Path
docs=json.loads(Path("data/documents/corpus.json").read_text())
assert all({"id","title","text"} <= d.keys() and d["text"].strip() for d in docs)
print(f"Validated {len(docs)} documents for corpus version demo-v1")
