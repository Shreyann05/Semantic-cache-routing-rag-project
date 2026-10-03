import json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.service import RAGService
items=json.loads(Path("data/evaluation/questions.json").read_text()); service=RAGService(True)
rows=[]
for x in items:
 r=service.query(x["question"]); rows.append({"question":x["question"],"retrieval_correct":any(s["id"]==x["expected_source"] for s in r["sources"]),"answerable":bool(r["sources"])})
print(json.dumps({"n":len(rows),"retrieval_recall":sum(r["retrieval_correct"] for r in rows)/len(rows),"rows":rows},indent=2))
