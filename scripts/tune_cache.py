import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.embeddings import embed,cosine
pairs=[("What is the refund policy?","What is the company refund policy?",1),("What is the refund policy?","How long is shipping?",0),("API rate limit","What is the API request limit?",1),("Encryption policy","Refund policy",0)]
scores=[(cosine(embed(a),embed(b)),same) for a,b,same in pairs]
out=[]
for t in [.5,.6,.7,.8,.9]:
 tp=sum(s>=t and y for s,y in scores);fp=sum(s>=t and not y for s,y in scores);fn=sum(s<t and y for s,y in scores);out.append({"threshold":t,"tp":tp,"fp":fp,"fn":fn,"precision":tp/(tp+fp) if tp+fp else 0,"recall":tp/(tp+fn) if tp+fn else 0})
Path("data/runtime").mkdir(parents=True,exist_ok=True);Path("data/runtime/cache_tuning.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
