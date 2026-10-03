import json
from pathlib import Path
def cost(model,inp,out,pricing):
 p=pricing.get(model,(0,0)); return (inp*p[0]+out*p[1])/1_000_000
class Metrics:
 def __init__(self,path):
  self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self.rows=json.loads(self.path.read_text()) if self.path.exists() else []
 def add(self,row): self.rows.append(row); self.path.write_text(json.dumps(self.rows,indent=2))
 def summary(self):
  r=self.rows; lat=sorted(x["latency_ms"] for x in r); pct=lambda p:lat[int((len(lat)-1)*p)] if lat else 0
  return {"total_queries":len(r),"cache_hit_rate":sum(x["cache_hit"] for x in r)/len(r) if r else 0,"total_cost":sum(x["cost"] for x in r),"average_cost":sum(x["cost"] for x in r)/len(r) if r else 0,"p50_latency_ms":pct(.5),"p95_latency_ms":pct(.95),"small_model_pct":sum(x["model_role"]=="small" for x in r)/len(r) if r else 0,"large_model_pct":sum(x["model_role"]=="large" for x in r)/len(r) if r else 0,"escalation_rate":sum(x["escalated"] for x in r)/len(r) if r else 0}
