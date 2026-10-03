import json, time
from pathlib import Path
from app.embeddings import embed, cosine
class SemanticCache:
 def __init__(self,path,threshold=.88,ttl_seconds=86400):
  self.path,self.threshold,self.ttl=Path(path),threshold,ttl_seconds; self.path.parent.mkdir(parents=True,exist_ok=True); self.items=json.loads(self.path.read_text()) if self.path.exists() else []
 def get(self,query,corpus_version):
  now,qv=time.time(),embed(query); self.items=[x for x in self.items if x["expires_at"]>now and x["corpus_version"]==corpus_version and x.get("answer") and x.get("sources")]; candidates=[(cosine(qv,x["embedding"]),x) for x in self.items]
  if not candidates:return None,0.0
  score,item=max(candidates,key=lambda x:x[0]); return (item if score>=self.threshold else None),score
 def put(self,query,answer,sources,corpus_version):
  if not answer.strip() or not sources:return
  self.items.append({"query":query,"embedding":embed(query),"answer":answer,"sources":sources,"corpus_version":corpus_version,"created_at":time.time(),"expires_at":time.time()+self.ttl}); self.path.write_text(json.dumps(self.items))
