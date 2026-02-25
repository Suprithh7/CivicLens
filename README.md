# 🏛️ CivicLens AI

> **Making Government Policy Accessible Through AI**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)

An AI-powered platform that transforms complex government policies into personalized, multilingual guidance with blockchain-verified proof of awareness.

---

## 🎯 Problem Statement

**73% of eligible citizens don't claim government benefits** due to:
- Policy documents written in legal jargon
- Scattered eligibility criteria across multiple sources  
- No accountability for whether citizens were properly informed

**Impact**: Millions miss out on healthcare subsidies, education grants, and social welfare programs they qualify for.

---

## 💡 Solution

CivicLens AI bridges the gap between government complexity and citizen understanding through three core capabilities:

### 1. **AI-Powered Policy Simplification**
- Upload government PDFs → Get plain-language summaries in any language
- Advanced text extraction with intelligent chunking for long documents
- Sentence-aware segmentation preserves semantic meaning

### 2. **Personalized Eligibility Inference** *(Planned)*
- Answer 3-5 simple questions → Know exactly which schemes you qualify for
- RAG-based Q&A with accurate citations from source documents

### 3. **Blockchain Proof of Awareness** *(Planned)*
- Immutable on-chain records of citizen interactions
- Governments can prove citizens were informed about benefits

---

## 🏗️ Technical Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   React SPA     │─────▶│  FastAPI Backend │─────▶│  AI Pipeline    │
│   (Frontend)    │      │  (Async Python)  │      │  (LLM + RAG)    │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │
                                  ├─────▶ SQLite (Policy Metadata)
                                  └─────▶ Polygon (Proof Records)*
```
*Blockchain integration planned

### Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React + Tailwind CSS | Fast, accessible UI with modern design |
| **Backend** | FastAPI (Python 3.10+) | High-performance async API with automatic OpenAPI docs |
| **AI/ML** | LLM + RAG (FAISS)* | Accurate policy Q&A with source citations |
| **Database** | SQLite | Lightweight, zero-config relational storage |
| **Blockchain** | Polygon* | Low-cost proof of awareness records |

*In development

---

## 🚀 Key Features Implemented

### ✅ Policy Document Management
- **PDF Upload & Validation**: Secure file handling with hash-based deduplication
- **Metadata Extraction**: Automatic categorization and indexing
- **Soft Delete**: Data retention with audit trails

### ✅ Text Extraction Pipeline
- **PDF Text Extraction**: Robust parsing with encryption detection
- **Processing Stages**: Tracked pipeline (extraction → chunking → embedding → QA-ready)
- **Error Handling**: Graceful failures with detailed error messages

### ✅ Intelligent Text Chunking
- **Sentence-Aware Segmentation**: Respects semantic boundaries (no mid-sentence splits)
- **Configurable Overlap**: Preserves context across chunk boundaries (critical for RAG)
- **Metadata Tracking**: Character positions, sentence counts, page mapping
- **Scalable Storage**: Dedicated `policy_chunks` table with efficient indexing

### ✅ RESTful API
- **OpenAPI Documentation**: Interactive Swagger UI at `/docs`
- **Async Operations**: Non-blocking I/O for high concurrency
- **Pagination**: Efficient data retrieval for large datasets
- **CORS Support**: Secure cross-origin requests

### ✅ Database Architecture
- **Normalized Schema**: Policies, processing stages, chunks
- **Alembic Migrations**: Version-controlled schema evolution
- **Indexes**: Optimized queries on `policy_id`, `status`, `chunk_index`

---

## 📂 Project Structure

```
CivicLens/
├── backend/                 # FastAPI server
│   ├── app/
│   │   ├── api/v1/         # API endpoints (policies, chunks, health)
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Business logic (text extraction, chunking)
│   │   ├── core/           # Config, dependencies, exceptions
│   │   └── utils/          # File handling, response utilities
│   ├── alembic/            # Database migrations
│   ├── tests/              # Unit & integration tests
│   └── requirements.txt
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── hooks/          # Custom React hooks
│   │   └── services/       # API client
│   └── package.json
├── ai/                     # ML pipeline (planned)
├── blockchain/             # Smart contracts (planned)
└── docs/                   # Architecture & API docs
```

---

## 🛠️ Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Git**

### Backend Setup

```bash
# Clone repository
git clone https://github.com/Suprithh7/CivicLens.git
cd CivicLens/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

**API available at**: `http://localhost:8000`  
**Interactive docs**: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**App available at**: `http://localhost:5173`

---

## 📊 API Examples

### Upload Policy Document
```bash
curl -X POST "http://localhost:8000/api/v1/policies/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@healthcare_policy.pdf"
```

### Extract Text
```bash
curl -X POST "http://localhost:8000/api/v1/policies/{policy_id}/extract-text"
```

### Chunk Text
```bash
curl -X POST "http://localhost:8000/api/v1/policies/{policy_id}/chunk?chunk_size=1000&overlap=200"
```

### Retrieve Chunks
```bash
curl "http://localhost:8000/api/v1/policies/{policy_id}/chunks?limit=10&offset=0"
```

---

## 🧪 Testing

```bash
# Run unit tests
cd backend
python -m pytest tests/ -v

# Test text chunking
python tests/test_text_chunking.py

# Test text extraction
python tests/test_text_extraction.py
```

---

## 🗺️ Roadmap

- [x] **Phase 1**: FastAPI backend with policy upload & text extraction
- [x] **Phase 2**: Intelligent text chunking for RAG pipeline
- [ ] **Phase 3**: LLM integration for policy summarization
- [ ] **Phase 4**: RAG-based Q&A with FAISS vector store
- [ ] **Phase 5**: Multilingual support (translation API)
- [ ] **Phase 6**: Blockchain proof of awareness (Polygon)
- [ ] **Phase 7**: Personalized eligibility inference engine

---

## 🎓 Technical Highlights

### Advanced Text Chunking
- **Algorithm**: Sentence-boundary detection using regex patterns
- **Overlap Strategy**: Configurable character overlap (default: 200 chars) to preserve context
- **Metadata**: Tracks character positions, sentence counts, and page numbers
- **Performance**: Handles 50+ page documents efficiently with indexed retrieval

### Async Architecture
- **Non-blocking I/O**: FastAPI's async/await for concurrent request handling
- **Database**: AsyncSession with SQLAlchemy 2.0 for async database operations
- **Scalability**: Designed for high-throughput policy processing

### Clean Code Practices
- **Type Hints**: Full type annotations for IDE support and runtime validation
- **Pydantic Schemas**: Request/response validation with automatic OpenAPI generation
- **Error Handling**: Custom exception classes with detailed error messages
- **Logging**: Structured logging for debugging and monitoring

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

---

## 🌟 Vision

**By 2027, CivicLens AI should help 10 million citizens access benefits they didn't know existed.**

This isn't just a project—it's public infrastructure for government transparency.

---

**Built with ❤️ for citizens who deserve clarity, not complexity.** 
yes yes yes 
