# Semantic Cache RAG

**A measurable retrieval-augmented generation (RAG) service that combines semantic caching, query-aware model routing, and grounded answers.** Built with FastAPI, Qdrant, Sentence Transformers, and LiteLLM.


## Highlights

- **Grounded retrieval:** embeds queries with `sentence-transformers/all-MiniLM-L6-v2` and searches a Qdrant collection for the top three relevant documents.
- **Semantic response cache:** reuses eligible answers using embedding similarity, a configurable score threshold and TTL, and corpus-version checks.
- **Cost-aware routing:** sends short factual questions to the configured small-model role and multi-part or reasoning-style questions to the large-model role.
- **Escalation path:** retries a weak small-role response with the large model.
- **Observable requests:** records latency, cache status, model role, token usage, estimated cost, and escalation metadata.
- **Evaluation tooling:** provides an eight-question labeled retrieval set and a repeatable 11-query baseline/optimized benchmark that saves timestamped run artifacts.
- **Service interfaces:** exposes query, health, metrics, and evaluation endpoints through FastAPI, with a Streamlit dashboard and Docker Compose configuration.

## Architecture

```text
Client
  │
  ▼
FastAPI ──► Semantic cache ── hit ──► Cached grounded answer
  │               │ miss
  │               ▼
  ├────────► Query router ──► Qdrant top-3 retrieval
  │                                  │
  │                                  ▼
  └──────────────────────────────► LiteLLM model call
                                      │
                         weak small-role answer?
                              yes ──► large-role retry
                                      │
                         answer + sources + metrics
```

The cache stores an answer together with its sources and corpus version. Model responses are prompted to use retrieved context and return a fixed fallback when context is insufficient. Baseline mode bypasses both caching and routing and uses the large-model role for every request.

## Measured local results

The checked-in verification report records these results for the current eight-document demo corpus:

| Check | Result |
|---|---:|
| Retrieval recall@3 on labeled questions | 8/8 (100%) |
| Router assignments on the 11-query workload | 10 small-role, 1 large-role |
| Unit tests in the recorded verification run | 7 passed |
| FastAPI health check | Passed |

Retrieval recall measures whether the expected source appeared in the top three results; it is **not** an answer-quality score. A local cache probe also found a false hit between standard- and express-shipping questions at the current threshold. This is a useful correctness limitation to keep visible while improving semantic cache validation.

## Tech stack

| Area | Tools |
|---|---|
| API | FastAPI, Pydantic, Uvicorn |
| Retrieval | Qdrant, Sentence Transformers, cosine similarity |
| Model adapter | LiteLLM; Groq is the default provider configuration |
| Cache and metrics | JSON-backed semantic cache and request metrics |
| Dashboard and packaging | Streamlit, Docker, Docker Compose |

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/query` | Retrieve context and generate a grounded answer |
| `GET` | `/metrics` | Summarize in-memory request metrics |
| `GET` | `/evaluation` | Read the legacy benchmark summary when available |

Interactive API documentation is available at `/docs` while the service is running.

## Project layout

```text
app/                  API, retrieval, routing, cache, metrics, configuration
scripts/              Corpus indexing, evaluation, benchmark, and provider check
data/documents/       Demo knowledge corpus
data/evaluation/      Labeled retrieval questions
dashboard/             Streamlit benchmark dashboard
benchmark_results.md  Detailed verification report and limitations
```

## Roadmap

- Add targeted cache safety checks for near-miss questions and verify whether retrieved sources support a cache match.
- Run the complete benchmark with successful provider calls and publish reproducible baseline-versus-optimized results.
- Evaluate generated answer quality with a labeled dataset and a groundedness/relevance rubric.
- Align the dashboard and evaluation endpoint with the timestamped benchmark artifact format.

## License

No license file is currently included. Add a license before redistributing or reusing this project.

