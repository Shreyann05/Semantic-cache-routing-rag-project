# Benchmark and Verification Report

**Status:** local retrieval and supporting behavior verified; the live LLM benchmark is incomplete because outbound Gemini requests are blocked in the current execution environment. No baseline-versus-optimized savings or answer-quality claims are made.

## Executive Summary

- The local corpus has 8 documents. Its existing Qdrant collection returned the expected source in the top 3 for all 8 supplied evaluation questions (retrieval recall@3: 8/8).
- FastAPI started and `/health` returned `{"status":"ok"}`.
- The current unit suite passed: 7 passed, 0 failed, 0 skipped.
- Cache paraphrase probes hit at the configured threshold 0.60, and an exact repeat bypassed a mocked LLM call.
- A material cache false hit was also observed: an answer cached for standard shipping was returned for an express shipping query (similarity 0.8275). The threshold was not changed.
- No live Gemini response was received in this run, so token totals, latency comparisons, escalation, estimated inference cost, and answer quality remain unmeasured.

## Environment

| Item | Observed value |
|---|---|
| Python | 3.13.2 |
| FastAPI | 0.142.2 |
| Sentence Transformers | 6.1.0 |
| Qdrant client | 1.19.1 |
| LiteLLM | 1.103.2 |
| Streamlit | 1.64.0 |
| pytest | 9.1.1 |
| Corpus | 8 documents in `data/documents/corpus.json` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) |
| Qdrant mode | Local embedded storage; no `QDRANT_URL` configured |
| Cache threshold / TTL | 0.60 / 86,400 seconds |
| Gemini key | Present in `.env`; value intentionally not reported |
| Small / large model IDs | Both configured as `gemini-3.8-flash` |
| Token prices | Both input and output prices are configured as 0.0 |

The same model ID is configured for both routing roles, so the router currently assigns “small” and “large” roles without selecting two distinct models. Zero token prices are placeholders and cannot support a meaningful cost estimate.

## What the Current Code Runs

- FastAPI entry point: `app.api:app`.
- Retrieval: Sentence Transformer query embeddings and local Qdrant vector search, filtered by corpus version.
- Indexing: `scripts/index_corpus.py` indexes the existing corpus and derives vector size from the embedding model.
- Cache: JSON-backed semantic cache with embedding similarity, TTL, source presence, and corpus-version checks. Cache storage is separate from Qdrant.
- Routing: deterministic query-shape heuristic; short factual queries get the small role, multi-part/reasoning cues get the large role.
- Escalation: weak small-role answer check calls the large role, but live escalation was not exercised.
- LLM: LiteLLM adapter reads `prompt_tokens` and `completion_tokens`; service calculates total tokens and latency. After the observed Vertex ADC error, unprefixed model names are routed with LiteLLM’s `gemini/` Google AI Studio prefix. This provider route has not received a successful live response in this environment. LiteLLM documents Google AI Studio model IDs in the `gemini/<model>` form ([LiteLLM example](https://docs.litellm.ai/docs/harness/gateway)).
- Metrics: request metrics are written to JSON. The existing service does not persist to SQLite.
- Dashboard: Streamlit reads the legacy `data/runtime/benchmark.json` shape. The safer benchmark runner writes timestamped files under `data/runtime/benchmarks/<run-id>/benchmark.json`, so the dashboard does not yet read its new output.

The README is stale relative to the current code: it describes LangChain Gemini and a local/custom retriever, and includes an older reported live request. Current model calls go through LiteLLM and retrieval goes through Qdrant. I did not independently reproduce the README's older token/latency figures in this run.

## Tests and Local Application Checks

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: **7 passed, 0 failed, 0 skipped** (19.13 seconds on the final run).

The app was started locally with Uvicorn and `/health` returned `{"status":"ok"}`. The process was stopped after the health check. No Gemini-backed `/query` response was obtained.

## Retrieval Evaluation

The fixed evaluation file contains 8 questions with expected document IDs. Direct local Qdrant retrieval at top-3 returned the expected document for every question:

| Query topic | Expected document | Top-3 included expected source |
|---|---|---|
| Refund policy | refund | Yes |
| Refund eligibility paraphrase | refund | Yes |
| Standard shipping | shipping | Yes |
| Encryption | security | Yes |
| Refund vs cancellation | refund | Yes |
| API rate limit | api | Yes |
| Support hours | support | Yes |
| Uptime objective | availability | Yes |

**Measured retrieval recall@3: 8/8 (100%).** This evaluates source retrieval only; it is not an answer-quality score.

## Cache Checks

Configured threshold: **0.60**.

| Cached query | Probe query | Similarity | Result |
|---|---|---:|---|
| “What is your refund policy?” | “How can I get a refund?” | 0.7292 | Hit |
| “What is your refund policy?” | “Tell me the rules for refunds.” | 0.7666 | Hit |
| “What is your refund policy?” | “How long does standard shipping take?” | 0.1396 | Miss |
| “What is your refund policy?” | “How long does express shipping take?” | 0.1703 | Miss |

Near-miss risk:

| Cached query | Probe query | Similarity | Result |
|---|---|---:|---|
| “How long does standard shipping take?” | “How long does express shipping take?” | 0.8275 | **False hit** |

The express-shipping query can receive the standard-shipping cached answer. This is a correctness risk with the current threshold and embedding behavior. The threshold was left unchanged; more targeted cache validation or a safer cache policy is needed before claiming reliable semantic reuse.

Other checks:

- An exact repeat produced miss then hit; a counting fake LLM was called once across the two queries. This confirms the cache branch bypasses the LLM in that controlled test, not in a live Gemini trace.
- An immediately expired entry was rejected using a negative test TTL.
- A cache entry with a different corpus version was rejected.
- These cases also passed within the 7-test suite.

## Routing and Escalation

Applying the current router to the existing 11-query benchmark workload assigned 10 queries to the small role and 1 to the large role: **90.9% / 9.1% router assignments**. This is a direct local execution of the router, not a count of completed Gemini requests. Both roles currently point to the same configured model ID, `gemini-3.8-flash`.

Escalation count and rate: **NOT MEASURED**. No live model response was available to exercise the weak-answer check.

## Baseline vs. Optimized Benchmark

The existing fixed workload is 11 queries (8 evaluation queries plus 3 repeated/paraphrased refund queries). No complete baseline or optimized run was produced, so comparison values are deliberately omitted.

| Metric | Baseline | Optimized | Change |
|---|---:|---:|---:|
| Successful model-backed requests | NOT MEASURED | NOT MEASURED | NOT MEASURED |
| Failed benchmark requests | NOT MEASURED | NOT MEASURED | NOT MEASURED |
| Cache hit rate | Not applicable to no-cache baseline | NOT MEASURED in full run | NOT MEASURED |
| Input / output / total tokens | NOT MEASURED | NOT MEASURED | NOT MEASURED |
| Average / P50 / P95 latency | NOT MEASURED | NOT MEASURED | NOT MEASURED |
| Estimated inference cost | NOT ESTIMATED | NOT ESTIMATED | NOT ESTIMATED |
| Answer quality | NOT MEASURED | NOT MEASURED | NOT MEASURED |

One live RAG request attempt could not complete: the execution environment rejected outbound sockets (`WinError 10013`) before a Gemini response was received. A prior evaluation log also showed unprefixed model IDs being routed to Vertex AI and failing because ADC credentials were absent. The adapter now adds the Google AI Studio prefix when needed, but the corrected route still needs to be run from a network-enabled local terminal.

Cost is not estimated because configured input and output prices are both zero. This report makes no claim about actual billing or money saved. No reliable answer-quality judge or labelled answer-quality dataset is present, so **quality preservation was not quantitatively established**.

## Exact Commands

Start the app:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.api:app --host 127.0.0.1 --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Index the corpus:

```powershell
.\.venv\Scripts\python.exe scripts\index_corpus.py
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run the combined fixed baseline and optimized benchmark:

```powershell
.\.venv\Scripts\python.exe scripts\benchmark.py
```

The benchmark runner now writes each run into a unique `data/runtime/benchmarks/<run-id>/` directory and does not delete existing runtime data. It records failures rather than treating missing results as zero, and skips the optimized run if the baseline fails. This run did **not** execute the full benchmark because outbound provider calls are blocked here.

## Claim Classification

### Directly measured

- 7 tests passed; 0 failed; 0 skipped.
- FastAPI health endpoint returned `{"status":"ok"}`.
- Local Qdrant retrieval returned the expected source in top-3 for 8 of 8 evaluation questions.
- Cache paraphrase and near-miss similarities/results shown above, including the standard/express false hit.
- Exact-repeat cache check bypassed the mocked LLM call (one mock call across two requests).
- TTL expiration and corpus-version mismatch were rejected in tests.
- Router assigned 10/11 fixed workload queries to small role and 1/11 to large role.
- Indexing output previously observed: 8 documents, 384-dimensional vectors.

### Calculated or estimated

- Retrieval recall@3: 8 correct expected sources divided by 8 questions = 100%.
- Router assignment percentages: counts divided by 11 queries.
- **Estimated inference cost: not calculated**, because configured prices are zero and no successful model token usage was collected.

### Not measured

- Completed baseline-versus-optimized model benchmark.
- Successful Gemini token usage or live model latency.
- Live cache hit rate / real Gemini calls avoided.
- Natural escalation behavior and rate.
- Baseline or optimized answer correctness, relevance, groundedness, or completeness.
- Actual Gemini billing changes, production cost reduction, production latency improvement, or production SLA.
