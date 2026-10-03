import json
from pathlib import Path
import streamlit as st
st.set_page_config(page_title="Semantic Cache RAG",layout="wide")
st.title("Semantic Caching & Cost-Aware Routing")
p=Path("data/runtime/benchmark.json")
if not p.exists():st.info("Run `python scripts/benchmark.py` to populate measured data.");st.stop()
d=json.loads(p.read_text()); b,o=d["baseline"],d["optimized"]
for label,key in [("Queries","total_queries"),("Cache hit rate","cache_hit_rate"),("Avg cost","average_cost"),("P95 latency (ms)","p95_latency_ms")]:
 st.metric(label,o[key],delta=(o[key]-b[key]) if isinstance(o[key],(int,float)) else None)
st.subheader("Measured baseline vs optimized")
st.dataframe({"metric":["total cost","p50 latency ms","p95 latency ms","cache hit rate","large model %","escalation rate"],"baseline":[b["total_cost"],b["p50_latency_ms"],b["p95_latency_ms"],b["cache_hit_rate"],b["large_model_pct"],b["escalation_rate"]],"optimized":[o["total_cost"],o["p50_latency_ms"],o["p95_latency_ms"],o["cache_hit_rate"],o["large_model_pct"],o["escalation_rate"]]})
