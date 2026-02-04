# 🏛️ CivicLens AI

> **Translating Government Complexity into Citizen Clarity**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status: Alpha](https://img.shields.io/badge/Status-Alpha-orange.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

CivicLens AI is an open-source platform that uses AI to translate complex government policies into personalized, simple, multilingual guidance — and records proof of awareness using blockchain.

---

## 🎯 **The Problem**

**73% of eligible citizens don't claim government benefits** because:
- Policy documents are written in legal jargon
- Eligibility criteria are scattered across multiple sources
- No accountability for whether citizens were properly informed

**Example:** A farmer eligible for crop insurance doesn't know:
- That the scheme exists
- If they qualify
- How to apply

---

## 💡 **The Solution**

CivicLens AI provides:

### 1️⃣ **AI-Powered Policy Simplification**
Upload a government PDF → Get plain-language summaries in any language

### 2️⃣ **Personalized Eligibility Inference**
Answer 3-5 simple questions → Know exactly which schemes you qualify for

### 3️⃣ **Blockchain Proof of Awareness**
Every interaction is recorded on-chain → Governments can prove citizens were informed

---

## 🏗️ **Architecture**

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   React     │─────▶│   FastAPI    │─────▶│  LLM + RAG  │
│  Frontend   │      │   Backend    │      │   (FAISS)   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ├─────▶ PostgreSQL (User Data)
                            └─────▶ Polygon (Proof Records)
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

---

## 🚀 **Tech Stack**

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | React + Tailwind | Fast, accessible UI for citizens |
| **Backend** | FastAPI (Python) | High-performance async API |
| **AI** | LLM + RAG (FAISS) | Accurate policy Q&A with citations |
| **Database** | PostgreSQL | Relational data for users/policies |
| **Blockchain** | Polygon | Low-cost proof of awareness |

---

## 📂 **Project Structure**

```
CivicLens/
├── frontend/          # React app
├── backend/           # FastAPI server
├── ai/                # LLM + RAG pipeline
├── blockchain/        # Smart contracts (Solidity)
├── docs/              # Architecture & guides
└── README.md          # You are here
```

---

## 🛠️ **Getting Started**

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL 14+
- Git

### Quick Start
```bash
# Clone the repository
git clone https://github.com/suprithh7/CivicLens.git
cd CivicLens

# Setup will be added in upcoming commits
```

---

## �️ **Roadmap**

- [x] **Day 1:** Project initialization and FastAPI backend skeleton

---

## 🤝 **Contributing**

We welcome contributions! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

---

## 📜 **License**

MIT License - see [LICENSE](LICENSE) for details

**By 2027, CivicLens AI should help 10 million citizens access benefits they didn't know existed.**

This is not just a project. It's a public infrastructure for government transparency.

---

**Built with ❤️ for citizens who deserve clarity, not complexity
batman

