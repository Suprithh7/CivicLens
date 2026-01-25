# CivicLens AI - System Architecture

## Overview
CivicLens AI is a **3-layer system** designed for scalability, modularity, and government-grade reliability.

---

## 🏗️ **High-Level Architecture**

```
┌──────────────────────────────────────────────────────────────┐
│                        CITIZEN LAYER                          │
│  (React Frontend - Accessible, Multilingual, Mobile-First)   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ REST API (JSON)
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                        │
│                    (FastAPI Backend)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Policy    │  │  Eligibility │  │   Blockchain │        │
│  │   Service   │  │   Inference  │  │   Recorder   │        │
│  └─────────────┘  └──────────────┘  └──────────────┘        │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                        DATA LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  PostgreSQL  │  │  FAISS Index │  │   Polygon    │       │
│  │  (Policies)  │  │  (Embeddings)│  │  (Proofs)    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

---

## 📦 **Component Breakdown**

### 1. **Frontend (React + Tailwind)**
**Purpose:** Citizen-facing interface

**Key Features:**
- Upload policy PDFs
- Ask questions in natural language
- View eligibility results
- Access blockchain proof

**Tech Choices:**
- **React:** Component reusability
- **Tailwind:** Rapid, accessible UI
- **i18n:** Multilingual support (Hindi, Tamil, etc.)

---

### 2. **Backend (FastAPI)**
**Purpose:** Business logic + API gateway

**Key Modules:**

#### **Policy Service**
- Upload PDFs
- Extract text (PyPDF2/pdfplumber)
- Chunk documents for RAG
- Store in PostgreSQL + FAISS

#### **Eligibility Inference Engine**
- Accept user profile (age, income, location)
- Query LLM with RAG context
- Return matching schemes with confidence scores

#### **Blockchain Recorder**
- Hash policy interactions
- Submit to Polygon testnet (Mumbai)
- Return transaction hash as proof

**Tech Choices:**
- **FastAPI:** Async performance (handles 10k+ requests/sec)
- **Pydantic:** Type-safe API contracts
- **SQLAlchemy:** ORM for PostgreSQL

---

### 3. **AI Layer (LLM + RAG)**
**Purpose:** Intelligent policy understanding

**Pipeline:**
```
PDF Upload → Text Extraction → Chunking (512 tokens)
           ↓
    Embedding (OpenAI/Sentence-Transformers)
           ↓
    FAISS Vector Store
           ↓
    User Query → Retrieve Top-K Chunks → LLM (GPT-4/Llama)
           ↓
    Personalized Answer + Citations
```

**Tech Choices:**
- **FAISS:** Fast similarity search (1M+ vectors)
- **LangChain:** RAG orchestration
- **OpenAI API:** Production LLM (fallback: Llama 3)

---

### 4. **Database (PostgreSQL)**
**Schema:**

```sql
-- Policies table
CREATE TABLE policies (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    department TEXT,
    pdf_url TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone TEXT UNIQUE,
    language TEXT DEFAULT 'en',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Interactions table (for analytics)
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    policy_id INT REFERENCES policies(id),
    query TEXT,
    response TEXT,
    blockchain_tx TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 5. **Blockchain (Polygon)**
**Purpose:** Immutable proof of awareness

**Smart Contract (Solidity):**
```solidity
contract ProofOfAwareness {
    struct Proof {
        address citizen;
        bytes32 policyHash;
        uint256 timestamp;
    }
    
    mapping(address => Proof[]) public proofs;
    
    function recordAwareness(bytes32 _policyHash) public {
        proofs[msg.sender].push(Proof({
            citizen: msg.sender,
            policyHash: _policyHash,
            timestamp: block.timestamp
        }));
    }
}
```

**Why Polygon?**
- Low gas fees (~$0.001/tx)
- Ethereum-compatible
- Government-ready (used by Indian states)

---

## 🔄 **Data Flow Example**

**Scenario:** Farmer asks "Am I eligible for PM-KISAN?"

1. **Frontend** sends query to `/api/eligibility`
2. **Backend** retrieves user profile (age, land size)
3. **AI Layer** searches FAISS for PM-KISAN policy chunks
4. **LLM** generates answer: "Yes, you qualify if you own <2 hectares"
5. **Blockchain** records interaction hash
6. **Frontend** shows result + blockchain proof link

---

## 🔐 **Security Considerations**

| Layer | Threat | Mitigation |
|-------|--------|-----------|
| Frontend | XSS attacks | React auto-escaping + CSP headers |
| Backend | SQL injection | SQLAlchemy parameterized queries |
| AI | Prompt injection | Input sanitization + output validation |
| Blockchain | Private key exposure | Hardware wallet integration (future) |

---

## 📈 **Scalability Plan**

| Component | Current | Scale to 1M users |
|-----------|---------|-------------------|
| Backend | Single FastAPI instance | Kubernetes + load balancer |
| Database | PostgreSQL (local) | AWS RDS Multi-AZ |
| AI | OpenAI API | Self-hosted Llama on GPU cluster |
| Blockchain | Polygon Mumbai (testnet) | Polygon Mainnet |

---

## 🚀 **Deployment Strategy**

**Phase 1: Local Development** (Days 1-7)
- Docker Compose for all services
- SQLite → PostgreSQL migration
- Mock blockchain (in-memory)

**Phase 2: Cloud Pilot** (Week 2-3)
- Deploy to AWS/GCP
- Real Polygon testnet
- 100 beta users

**Phase 3: Production** (Month 2)
- CDN for frontend
- Auto-scaling backend
- Mainnet blockchain

---

**This architecture balances simplicity (for rapid development) with production-readiness (for government deployment).**
