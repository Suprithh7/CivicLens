"""
API v1 router configuration.
Aggregates all v1 endpoints.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, policies, chunks, embeddings, search, rag, simplification

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(policies.router, prefix="/policies", tags=["policies"])
api_router.include_router(chunks.router, prefix="/chunks", tags=["chunks"])
api_router.include_router(embeddings.router, prefix="/embeddings", tags=["embeddings"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(simplification.router, prefix="/simplification", tags=["simplification"])

# Future endpoints will be added here:
# api_router.include_router(eligibility.router, prefix="/eligibility", tags=["Eligibility"])
