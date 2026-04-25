<div align="center">

<img src="https://img.shields.io/badge/CivicLens-AI-4F46E5?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyTDIgN2wxMCA1IDEwLTVMMTIgMnpNMiAxN2wxMCA1IDEwLTVNMiAxMmwxMCA1IDEwLTUiLz48L3N2Zz4=" alt="CivicLens AI"/>

# CivicLens AI

### *Democratizing Access to Government Policy Through Artificial Intelligence*

<p>
  <a href="https://github.com/Suprithh7/CivicLens/blob/main/LICENSE">
    <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-6366F1.svg?style=flat-square"/>
  </a>
  <a href="https://www.python.org/downloads/release/python-3100/">
    <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10+-3B82F6.svg?style=flat-square&logo=python&logoColor=white"/>
  </a>
  <a href="https://fastapi.tiangolo.com">
    <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.109-009688.svg?style=flat-square&logo=fastapi&logoColor=white"/>
  </a>
  <a href="https://react.dev">
    <img alt="React 18" src="https://img.shields.io/badge/React-18-61DAFB.svg?style=flat-square&logo=react&logoColor=black"/>
  </a>
  <a href="https://github.com/Suprithh7/CivicLens/actions">
    <img alt="Tests" src="https://img.shields.io/badge/Tests-210%20Passing-22C55E.svg?style=flat-square&logo=pytest&logoColor=white"/>
  </a>
  <img alt="Code Style" src="https://img.shields.io/badge/Code%20Style-Black-000000.svg?style=flat-square"/>
</p>

<p>
  <a href="#-overview">Overview</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-reference">API Reference</a> •
  <a href="#-development">Development</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

---

> **73% of eligible citizens never claim government benefits they qualify for** — not because they don't need them, but because policy documents are inaccessible. CivicLens AI changes that.

</div>

---

## 📖 Overview

**CivicLens AI** is a full-stack, production-grade platform that applies large language models, retrieval-augmented generation (RAG), and semantic search to make government policy documents universally understandable. Citizens upload a policy PDF; CivicLens delivers a plain-language summary, personalized eligibility assessment, and a cited Q&A interface — all in their native language.

### The Problem

| Challenge | Scale |
|---|---|
| Policy documents average **47 pages** of dense legal prose | 🗂️ |
| Eligibility criteria span **3–7 separate documents** on average | 📚 |
| **Only 27%** of eligible US citizens claim SNAP benefits | 📉 |
| **$65B+** in unclaimed government benefits annually (US alone) | 💸 |

### The Solution

CivicLens attacks this problem across three dimensions:

1. **Comprehension** — LLM-powered simplification converts legalese into plain language, grade-8 reading level
2. **Personalization** — A deterministic rule engine + RAG pipeline assesses *your specific* eligibility
3. **Verification** — Blockchain-anchored proof of awareness creates accountability for both citizens and institutions

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        CivicLens AI Platform                       │
│                                                                    │
│   ┌──────────────┐       ┌────────────────────────────────────┐   │
│   │   React SPA  │◄─────►│         FastAPI Backend            │   │
│   │  (Vite + TS) │  REST │  Async Python · OpenAPI 3.1        │   │
│   └──────────────┘       └────────────┬───────────────────────┘   │
│                                       │                            │
│              ┌────────────────────────┼──────────────────────┐    │
│              ▼                        ▼                       ▼    │
│   ┌──────────────────┐  ┌──────────────────────┐  ┌───────────┐  │
│   │   AI Pipeline    │  │   Vector Store       │  │  SQLite   │  │
│   │  OpenAI GPT-4o   │  │   FAISS (L2 Index)   │  │ Alembic   │  │
│   │  sentence-xfmrs  │  │  384-dim embeddings  │  │ AsyncORM  │  │
│   └──────────────────┘  └──────────────────────┘  └───────────┘  │
│                                                                    │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │              Processing Pipeline (Async)                 │    │
│   │  PDF Upload → Text Extraction → Chunking → Embedding    │    │
│   │            → FAISS Index → RAG-ready ✓                  │    │
│   └──────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
```

### Technology Decisions

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| **Frontend** | React + Vite + Tailwind CSS | 18 / 5 / 3 | HMR dev experience, production-optimized bundles |
| **API** | FastAPI | 0.109 | Async-first, automatic OpenAPI 3.1 docs, Pydantic v2 validation |
| **ORM** | SQLAlchemy (Async) | 2.0 | Async sessions, type-safe queries, Alembic migrations |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | 2.3 | 384-dim, 5× faster than Ada-002, comparable quality for domain text |
| **Vector Search** | FAISS (CPU) | 1.7 | Sub-millisecond ANN search over millions of policy chunks |
| **LLM** | OpenAI GPT-4o | 1.12 | Best-in-class instruction following for structured simplification |
| **Caching** | cachetools TTLCache | 5.3 | 24hr simplification cache; estimated $0.001/hit savings |
| **Language Detection** | langdetect | 1.0 | Automatic multilingual routing |
| **Blockchain** | Polygon *(planned)* | — | Low gas, EVM-compatible proof-of-awareness anchoring |

---

## ✨ Features

<details>
<summary><b>📄 Policy Document Management</b></summary>

- **Secure PDF Upload** with SHA-256 hash-based deduplication (no duplicate storage)
- **Soft Delete** with audit trails — data is never permanently lost
- **Policy Versioning** — every PATCH creates an immutable historical snapshot; one-command restore to any prior version
- **Metadata Catalogue** — title, jurisdiction, policy type, effective/expiry dates, source URL
- **Pagination** on all list endpoints with configurable `limit`/`offset`

</details>

<details>
<summary><b>🔍 Text Extraction Pipeline</b></summary>

- **pypdf-powered extraction** with per-page graceful fallback (a single bad page never kills the job)
- **Encrypted PDF detection** with user-friendly error messaging
- **Processing state machine** — `PENDING → IN_PROGRESS → COMPLETED / FAILED` tracked per document
- **Extraction statistics** — character count, word count, text preview in API response
- **Force re-extraction** flag for correcting previously failed jobs

</details>

<details>
<summary><b>✂️ Intelligent Text Chunking</b></summary>

- **Sentence-boundary aware** splits using regex-based boundary detection — zero mid-sentence breaks
- **Configurable overlap** (default 200 chars) preserves cross-chunk context critical for RAG accuracy
- **Configurable chunk size** (10–5000 chars) accommodates short policy memos to 100-page legislation
- **Rich metadata** per chunk: character positions, sentence count, page mapping
- **Atomic re-chunking** — force flag deletes existing chunks before recreating

</details>

<details>
<summary><b>🧠 Semantic Embedding & Vector Search</b></summary>

- **Batch embedding generation** via `sentence-transformers` run in a thread pool (non-blocking event loop)
- **FAISS flat L2 index** auto-built after embedding, serialized to disk for persistence across restarts
- **Similarity scoring** converts L2 distance to exponential decay score (0–1, higher = more similar)
- **Singleton model loader** — model loaded once, reused across all requests (< 50ms warm inference)
- **Cross-policy search** — query across the entire corpus or scope to a specific policy

</details>

<details>
<summary><b>🤖 AI Simplification & RAG Q&A</b></summary>

- **GPT-4o simplification** with structured prompts targeting grade-8 readability
- **Multiple explanation modes**: summary, key points, eligibility criteria, examples
- **Streaming responses** for real-time UI feedback on long documents
- **TTL-based response cache** (24hr) using normalized SHA-256 keys — identical queries never re-hit the LLM
- **RAG pipeline** with FAISS retrieval + citation-backed answers referencing exact policy chunks
- **Output evaluation suite** — relevance, coherence, completeness, source grounding, hallucination risk, citation quality, bias detection

</details>

<details>
<summary><b>⚖️ Eligibility Engine</b></summary>

- **Deterministic rule engine** for PSLF and extensible to any policy type
- **User profile model** — captures income, employment, citizenship, education, student loans, veterans status, and 15+ additional dimensions
- **Eligibility result taxonomy**: `ELIGIBLE / NOT_ELIGIBLE / PARTIAL / NEEDS_MORE_INFO`
- **Heuristic improvements** for inference when data is incomplete
- **Evidence-backed explanations** — every result includes matched criteria, failed criteria, and missing fields
- **Immutable check history** — every evaluation permanently recorded for audit

</details>

<details>
<summary><b>🔒 Policy Versioning & Audit</b></summary>

- **Snapshot-on-write** — every PATCH captures the pre-edit state in `policy_versions`
- **No-op detection** — patches with identical values skip version bumps entirely
- **One-click restore** to any historical version (creates a new version, preserving the full chain)
- **Version diff access** — retrieve any snapshot by `version_number`

</details>

<details>
<summary><b>📊 Observability & Quality</b></summary>

- **Structured logging** with request tracing middleware (start/end, status codes, latency)
- **AI output evaluation** — every LLM response is scored across 7 quality dimensions before delivery
- **Cache hit rate tracking** with estimated cost savings in USD
- **210 unit + integration tests** covering all services, endpoints, and business rules

</details>

---

## 📂 Project Structure

```
CivicLens/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   │           ├── policies.py        # CRUD, versioning, upload
│   │   │           ├── chunks.py          # Chunking pipeline endpoints
│   │   │           ├── embeddings.py      # Embedding generation
│   │   │           ├── search.py          # Semantic search
│   │   │           ├── simplification.py  # LLM simplification
│   │   │           ├── rag.py             # RAG Q&A
│   │   │           ├── eligibility.py     # Eligibility checks
│   │   │           └── cache.py           # Cache management
│   │   ├── models/
│   │   │   ├── policy.py          # Policy, Chunk, Processing, Version
│   │   │   └── eligibility.py     # UserEligibilityProfile, EligibilityCheck
│   │   ├── services/
│   │   │   ├── text_extraction.py         # PDF → raw text
│   │   │   ├── text_chunking.py           # Text → overlapping chunks
│   │   │   ├── embedding_service.py       # Chunks → 384-dim vectors
│   │   │   ├── faiss_service.py           # Vector index management
│   │   │   ├── search_service.py          # Semantic similarity search
│   │   │   ├── simplification_service.py  # LLM simplification pipeline
│   │   │   ├── rag_service.py             # RAG retrieval + generation
│   │   │   ├── evaluation_service.py      # AI output quality scoring
│   │   │   ├── cache_service.py           # TTL response caching
│   │   │   ├── policy_version_service.py  # Versioning & snapshots
│   │   │   ├── language_service.py        # Language detection & routing
│   │   │   └── eligibility_rules/
│   │   │       └── engine.py              # Deterministic rule engine
│   │   ├── schemas/               # Pydantic v2 request/response models
│   │   ├── core/
│   │   │   ├── config.py          # Settings (pydantic-settings)
│   │   │   ├── database.py        # Async SQLAlchemy engine + session
│   │   │   ├── exceptions.py      # CivicLensException base class
│   │   │   ├── exception_handlers.py  # Global FastAPI error handlers
│   │   │   └── middleware.py      # Request tracing middleware
│   │   └── constants.py           # Centralized configuration constants
│   ├── alembic/
│   │   └── versions/              # Database migration scripts
│   ├── tests/                     # 210+ tests across 17 test files
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── components/            # Reusable React components
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── services/              # API client layer
│   │   └── utils/                 # Shared utilities
│   ├── package.json
│   └── vite.config.js
├── ai/                            # Standalone ML pipeline experiments
├── blockchain/                    # Smart contract prototypes (Polygon)
└── docs/                          # Architecture diagrams, ADRs
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Git | Any | `git --version` |
| OpenAI API Key | — | [platform.openai.com](https://platform.openai.com) |

### 1. Clone

```bash
git clone https://github.com/Suprithh7/CivicLens.git
cd CivicLens
```

### 2. Backend

```bash
cd backend

# Create & activate virtual environment
python -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...

# Apply database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| Endpoint | URL |
|---|---|
| REST API | http://localhost:8000 |
| Interactive Docs (Swagger) | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

### 3. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# VITE_API_URL=http://localhost:8000

# Start development server
npm run dev
```

App available at: **http://localhost:5173**

---

## 📡 API Reference

All endpoints are versioned under `/api/v1`. Full interactive documentation available at `/docs`.

### Policies

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/policies/upload` | Upload a PDF policy document |
| `GET` | `/policies` | List all policies (paginated) |
| `GET` | `/policies/{policy_id}` | Get policy metadata |
| `PATCH` | `/policies/{policy_id}` | Update metadata (auto-snapshots prior version) |
| `DELETE` | `/policies/{policy_id}` | Soft-delete a policy |
| `GET` | `/policies/{policy_id}/versions` | List version history |
| `GET` | `/policies/{policy_id}/versions/{n}` | Get specific historical snapshot |
| `POST` | `/policies/{policy_id}/versions/{n}/restore` | Restore to a prior version |

### Processing Pipeline

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/policies/{id}/extract-text` | Extract raw text from PDF |
| `GET` | `/policies/{id}/extract-text/status` | Check extraction status |
| `POST` | `/policies/{id}/chunk` | Chunk extracted text |
| `GET` | `/policies/{id}/chunks` | Retrieve chunks (paginated) |
| `POST` | `/policies/{id}/embeddings` | Generate vector embeddings |
| `GET` | `/policies/{id}/embeddings/status` | Check embedding status |

### AI Features

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/policies/{id}/simplify` | Generate LLM simplification |
| `POST` | `/policies/{id}/simplify/stream` | Streaming simplification |
| `POST` | `/search` | Semantic search across all policies |
| `POST` | `/policies/{id}/search` | Semantic search within one policy |
| `POST` | `/rag/query` | RAG-based Q&A with citations |
| `GET` | `/cache/stats` | Cache hit rates & cost savings |
| `DELETE` | `/cache` | Clear response cache |

### Eligibility

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/eligibility/profiles` | Create user eligibility profile |
| `GET` | `/eligibility/profiles/{id}` | Get profile |
| `POST` | `/eligibility/check` | Run eligibility check against a policy |
| `GET` | `/eligibility/checks/{id}` | Get check result with explanation |

### Example Requests

```bash
# 1. Upload a policy document
curl -X POST http://localhost:8000/api/v1/policies/upload \
  -F "file=@healthcare_policy.pdf" \
  -F "title=Medicaid Eligibility Guidelines 2024"

# 2. Run the full processing pipeline
POLICY_ID="pol_abc123xyz"
curl -X POST http://localhost:8000/api/v1/policies/$POLICY_ID/extract-text
curl -X POST "http://localhost:8000/api/v1/policies/$POLICY_ID/chunk?chunk_size=1000&overlap=200"
curl -X POST http://localhost:8000/api/v1/policies/$POLICY_ID/embeddings

# 3. Ask a question (RAG)
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Who qualifies for Medicaid?", "policy_id": "pol_abc123xyz"}'

# 4. Get a plain-language simplification
curl -X POST http://localhost:8000/api/v1/policies/$POLICY_ID/simplify \
  -H "Content-Type: application/json" \
  -d '{"explanation_type": "key_points", "language": "en"}'

# 5. Run a semantic search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "income limits for housing assistance", "top_k": 5}'
```

---

## 🧪 Development

### Running Tests

```bash
cd backend

# Run full test suite (210 tests)
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_pslf_rules.py -v          # Eligibility engine
python -m pytest tests/test_evaluation_service.py -v  # AI quality scoring
python -m pytest tests/test_policy_versioning.py -v   # Version history
python -m pytest tests/test_cache_service.py -v       # Caching layer

# Run with coverage report
python -m pytest tests/ --cov=app --cov-report=html
```

### Code Quality

```bash
# Format (Black)
black app/ tests/

# Type checking (mypy)
mypy app/

# Lint (ruff)
ruff check app/ tests/
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "describe your change"

# Apply all pending migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1

# Show migration history
alembic history --verbose
```

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API key for LLM calls |
| `DATABASE_URL` | ❌ | `sqlite+aiosqlite:///./civiclens.db` | Async database connection string |
| `UPLOAD_DIR` | ❌ | `uploads/policies` | Directory for uploaded PDFs |
| `FAISS_INDEX_DIR` | ❌ | `faiss_indices` | Directory for persisted FAISS indexes |
| `LOG_LEVEL` | ❌ | `INFO` | Logging verbosity |
| `MAX_FILE_SIZE_MB` | ❌ | `10` | Maximum PDF upload size |

---

## 🗺️ Roadmap

```
Phase 1  ✅  Core API — Policy upload, text extraction, pagination
Phase 2  ✅  Chunking — Sentence-aware chunking with overlap and metadata
Phase 3  ✅  Embeddings — sentence-transformers + FAISS vector indexing
Phase 4  ✅  Simplification — GPT-4o pipeline with streaming + caching
Phase 5  ✅  RAG Q&A — FAISS retrieval + cited LLM answers
Phase 6  ✅  Eligibility Engine — Deterministic PSLF rule engine + user profiles
Phase 7  ✅  Input Validation — Cross-field validators, schema hardening
Phase 8  ✅  AI Evaluation — 7-dimension output quality scoring
Phase 9  ✅  Policy Versioning — Snapshot-on-write, restore, diff
Phase 10 ✅  Heuristic Inference — Improved eligibility reasoning under uncertainty
Phase 11 🔄  Performance — Query optimization, lazy loading, response compression
Phase 12 🔜  Multilingual — DeepL/Google Translate integration for 50+ languages
Phase 13 🔜  Blockchain PoA — Polygon smart contracts for proof-of-awareness
Phase 14 🔜  Auth & Multi-tenancy — OAuth2, role-based access, agency portals
Phase 15 🔜  Mobile — React Native app for offline-first access
```

---

## 🎓 Technical Deep Dives

### RAG Pipeline Design

The retrieval pipeline follows a **retrieve → re-rank → generate** pattern:

1. **Query Embedding** — User query → 384-dim vector via `all-MiniLM-L6-v2` (thread-pooled, non-blocking)
2. **FAISS ANN Search** — Top-K chunks retrieved using L2 flat index (< 1ms for 10K chunks)
3. **Score Normalization** — L2 distances converted to similarity via `exp(-d)` (0–1 monotonic)
4. **Context Assembly** — Top chunks formatted with chunk index and policy source for LLM context
5. **GPT-4o Generation** — Structured prompt enforces citation format, factual grounding
6. **Quality Evaluation** — 7 metrics computed post-generation: relevance, coherence, completeness, grounding, hallucination risk, citation quality, safety

### Embedding Architecture

The singleton `EmbeddingModel` wrapper ensures the 80MB `all-MiniLM-L6-v2` model loads exactly once per process. Batch inference runs in `asyncio.to_thread()` to avoid blocking the async event loop during CPU-bound encoding. FAISS indices are persisted to disk and loaded on first access.

### Caching Strategy

Response caching uses SHA-256 hashed keys over normalized parameter dicts (None fields excluded, keys sorted). Clearing any cache type also resets the corresponding hit/miss counters to prevent cross-session stat pollution. Estimated savings are tracked at $0.001/cache hit and surfaced via `/cache/stats`.

### Policy Versioning

Every `PATCH` request triggers a **snapshot-on-write**: the current policy state is atomically persisted to `policy_versions` before any mutation. A value-comparison pass skips the snapshot entirely if the submitted values are identical to the current state (true no-op detection). Restoration creates a new version rather than mutating history, preserving the complete audit chain.

---

## 🤝 Contributing

We welcome contributions of all kinds! Please read our [Contributing Guide](docs/CONTRIBUTING.md) before opening a PR.

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feat/your-feature`
3. **Write tests** for your changes (we maintain >90% coverage)
4. **Format** your code: `black app/ tests/`
5. **Submit** a pull request with a clear description

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add multilingual simplification support
fix: resolve FAISS index reload on restart
docs: update API reference for RAG endpoint
test: add coverage for eligibility edge cases
perf: lazy-load embedding model on first request
```

---

## 📜 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for full terms.

---

## 🌟 Vision

> *"By 2028, every citizen on Earth should be able to understand any government document in 60 seconds, in their own language, with a clear answer to 'do I qualify?'"*

CivicLens is public infrastructure for government transparency. The goal is not a startup exit — it's a world where complexity stops being a barrier to dignity.

---

<div align="center">

**Built with purpose, not just passion.**

*If CivicLens helped you or your community, please consider giving it a ⭐*

[![GitHub stars](https://img.shields.io/github/stars/Suprithh7/CivicLens?style=social)](https://github.com/Suprithh7/CivicLens)

</div>
