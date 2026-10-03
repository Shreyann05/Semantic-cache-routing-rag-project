"""Run the fixed baseline/optimized workload without deleting previous data."""
import json
import sys
import uuid
import os
import re
import traceback
import math
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from statistics import median
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.service import RAGService


ROOT = Path("data/runtime/benchmarks")
questions = json.loads(Path("data/evaluation/questions.json").read_text(encoding="utf-8"))
workload = [x["question"] for x in questions] + [
    "What is the company refund policy?",
    "What is the refund policy?",
    "Can I get my money back within thirty days?",
]
run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
run_dir = ROOT / run_id
PRICING = __import__("app.config", fromlist=["PRICING"]).PRICING
pricing_configured = bool(PRICING) and all(
    len(rates) == 2 and all(math.isfinite(rate) and rate > 0 for rate in rates)
    for rates in PRICING.values()
)


def safe_error_text(value):
    """Avoid writing configured credentials to console or benchmark reports."""
    text = str(value)
    secrets = [os.getenv("GROQ_API_KEY")]
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return re.sub(r"(?i)(api[_ -]?key\s*[=:]\s*)[^\s,;]+", r"\1[REDACTED]", text)


def run_mode(name, optimized):
    service = RAGService(optimized=optimized, data_dir=run_dir / name)
    rows = []
    try:
        for index, query in enumerate(workload, start=1):
            started = perf_counter()
            try:
                result = service.query(query)
                rows.append({
                    "query_id": f"q{index:02d}", "query": query, "success": True,
                    "request_id": result.get("request_id"), "latency_ms": result.get("latency_ms"),
                    "provider": "groq",
                    "input_tokens": result.get("input_tokens", 0), "output_tokens": result.get("output_tokens", 0),
                    "total_tokens": result.get("total_tokens", 0), "model": result.get("model"),
                    "cost": result.get("cost") if pricing_configured else None,
                    "estimated_cost": result.get("cost") if pricing_configured else None,
                    "cache_hit": result.get("cache_hit", False), "route": result.get("route"),
                    "model_role": result.get("model_role"), "escalated": result.get("escalated", False),
                    "similarity": result.get("similarity"), "llm_calls": result.get("llm_calls"),
                })
            except Exception as exc:
                import traceback

                error_details = {
                    "query_id": f"q{index:02d}",
                    "query": query,
                    "success": False,
                    "latency_ms": round((perf_counter() - started) * 1000, 2),
                    "error_type": type(exc).__name__,
                    "error_message": safe_error_text(exc),
                    "traceback": safe_error_text(traceback.format_exc()),
                }

                print("\n===== BENCHMARK ERROR =====")
                print(f"Query: {query}")
                print(f"Error type: {type(exc).__name__}")
                print(f"Error message: {safe_error_text(exc)}")
                print(safe_error_text(traceback.format_exc()))
                print("===========================\n")

                rows.append(error_details)
                break
    finally:
        service.close()
    successful = [row for row in rows if row["success"]]
    latencies = sorted(row["latency_ms"] for row in successful if row.get("latency_ms") is not None)
    def percentile(p):
        if not latencies:
            return None
        return latencies[max(0, ceil(len(latencies) * p) - 1)]
    total = len(successful)
    attempted = len(rows)
    hits = sum(row.get("cache_hit", False) for row in successful)
    summary = {
        "requests_attempted": attempted, "successful": len(successful), "failed": attempted - len(successful),
        "llm_calls_avoided": hits,
        "cache_hits": hits, "cache_hit_rate": hits / total if total else None,
        "input_tokens": sum(row.get("input_tokens", 0) for row in successful),
        "output_tokens": sum(row.get("output_tokens", 0) for row in successful),
        "total_tokens": sum(row.get("total_tokens", 0) for row in successful),
        "estimated_cost": sum(row["estimated_cost"] for row in successful if row.get("estimated_cost") is not None) if pricing_configured else None,
        "estimated_cost_per_request": (sum(row["estimated_cost"] for row in successful if row.get("estimated_cost") is not None) / total) if pricing_configured and total else None,
        "input_tokens_per_request": sum(row.get("input_tokens", 0) for row in successful) / total if total else None,
        "output_tokens_per_request": sum(row.get("output_tokens", 0) for row in successful) / total if total else None,
        "total_tokens_per_request": sum(row.get("total_tokens", 0) for row in successful) / total if total else None,
        "average_latency_ms": sum(latencies) / len(latencies) if latencies else None,
        "median_latency_ms": median(latencies) if latencies else None,
        "p50_latency_ms": median(latencies) if latencies else None,
        "p95_latency_ms": percentile(0.95),
        "min_latency_ms": min(latencies) if latencies else None, "max_latency_ms": max(latencies) if latencies else None,
        "small_model_pct": sum(row.get("model_role") == "small" for row in successful) / total if total else None,
        "large_model_pct": sum(row.get("model_role") == "large" for row in successful) / total if total else None,
        "escalations": sum(row.get("escalated", False) for row in successful),
        "escalation_rate": sum(row.get("escalated", False) for row in successful) / total if total else None,
    }
    return {"summary": summary, "requests": rows}


baseline = run_mode("baseline", optimized=False)
optimized = run_mode("optimized", optimized=True) if baseline["summary"]["failed"] == 0 else None
report = {
    "run_id": run_id, "workload_size": len(workload), "workload": workload,
    "pricing_configured": pricing_configured, "baseline": baseline, "optimized": optimized,
    "note": "Estimated inference cost is omitted unless nonzero token prices are configured. Quality is not automatically scored.",
}
ROOT.mkdir(parents=True, exist_ok=True)
(run_dir / "benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"run_id": run_id, "workload_size": len(workload),
                  "baseline": baseline["summary"],
                  "optimized": optimized["summary"] if optimized else "NOT RUN: baseline had failures",
                  "report": str(run_dir / "benchmark.json")}, indent=2))
