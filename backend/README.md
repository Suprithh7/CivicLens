# CivicLens Backend API

## Overview

FastAPI-based backend for CivicLens AI - an AI-powered platform to translate government policies into personalized, multilingual guidance.

## Features

- ✅ RESTful API with FastAPI
- ✅ Health check endpoint
- ✅ Configuration management with Pydantic Settings
- ✅ CORS support for frontend integration
- ✅ Auto-generated API documentation (Swagger & ReDoc)
- ✅ Modular architecture following best practices

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL (optional, for database features)

### Installation

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # Windows
   source venv/bin/activate      # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Root:** http://localhost:8000/
- **Health Check:** http://localhost:8000/api/v1/health
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── api/
│   │   └── v1/
│   │       ├── router.py    # API v1 router
│   │       └── endpoints/
│   │           └── health.py # Health check endpoint
│   ├── schemas/
│   │   └── health.py        # Pydantic schemas
│   ├── models/              # Database models
│   ├── services/            # Business logic
│   └── core/                # Core utilities
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment file
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## API Endpoints

### Health Check
```
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "app_name": "CivicLens AI",
  "version": "0.1.0",
  "environment": "development"
}
```

## Configuration

Environment variables can be set in the `.env` file:

```env
# Application
APP_NAME=CivicLens AI
APP_VERSION=0.1.0
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/civiclens_dev

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Development

### Adding New Endpoints

1. Create endpoint file in `app/api/v1/endpoints/`
2. Define Pydantic schemas in `app/schemas/`
3. Register router in `app/api/v1/router.py`

Example:
```python
# app/api/v1/endpoints/example.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/example")
async def example_endpoint():
    return {"message": "Hello World"}
```

```python
# app/api/v1/router.py
from app.api.v1.endpoints import example

api_router.include_router(
    example.router,
    prefix="/example",
    tags=["Example"]
)
```

### Running Tests

```bash
pytest
```

## Tech Stack

- **FastAPI** - Modern, fast web framework
- **Pydantic** - Data validation using Python type annotations
- **Uvicorn** - ASGI server
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL** - Database
- **Alembic** - Database migrations

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions, please open an issue on GitHub.
