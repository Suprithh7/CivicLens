# CivicLens AI - Backend

FastAPI backend for CivicLens AI platform.

## 🏗️ Architecture

```
app/
├── main.py              # FastAPI app entry point
├── config.py            # Configuration management
├── api/
│   └── v1/
│       ├── router.py    # API v1 router
│       └── endpoints/   # API endpoints
│           └── health.py
├── core/
│   └── dependencies.py  # Shared dependencies
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic schemas
│   └── health.py
└── services/            # Business logic layer
```

## 🚀 Quick Start

### 1. Setup Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
copy .env.example .env

# Edit .env with your settings
```

### 4. Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test the API

Open your browser:
- **API Docs (Swagger):** http://localhost:8000/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/v1/health

## 📡 API Endpoints

### Current Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/api/v1/health` | Health check |

### Coming Soon

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/policies/upload` | Upload policy PDF |
| GET | `/api/v1/policies` | List all policies |
| POST | `/api/v1/eligibility/check` | Check eligibility |

## 🧪 Testing

```bash
# Run tests (coming soon)
pytest tests/
```

## 📦 Project Structure Explained

- **`main.py`**: FastAPI app initialization, CORS, middleware
- **`config.py`**: Environment-based configuration using Pydantic
- **`api/v1/`**: API version 1 (allows future v2, v3)
- **`endpoints/`**: Route handlers (controllers)
- **`schemas/`**: Request/response models (Pydantic)
- **`models/`**: Database models (SQLAlchemy)
- **`services/`**: Business logic (keeps routes thin)
- **`core/`**: Shared utilities and dependencies

## 🔧 Development Guidelines

### Adding a New Endpoint

1. Create schema in `schemas/`
2. Create endpoint in `api/v1/endpoints/`
3. Register in `api/v1/router.py`
4. Add business logic in `services/` (if complex)

### Example:

```python
# schemas/policy.py
class PolicyCreate(BaseModel):
    title: str
    content: str

# api/v1/endpoints/policies.py
@router.post("/policies")
async def create_policy(policy: PolicyCreate):
    return {"message": "Policy created"}

# api/v1/router.py
from app.api.v1.endpoints import policies
api_router.include_router(policies.router, tags=["Policies"])
```

## 🌍 Environment Variables

See `.env.example` for all available configuration options.

## 📚 Tech Stack

- **FastAPI**: Modern, fast web framework
- **Pydantic**: Data validation
- **SQLAlchemy**: ORM for PostgreSQL
- **Uvicorn**: ASGI server

---

**Built for Day 2 of CivicLens AI** 🚀
