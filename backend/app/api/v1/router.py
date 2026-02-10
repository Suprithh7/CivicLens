from fastapi import APIRouter
from app.api.v1.endpoints import health, policies, chunks, embeddings

# Create API v1 router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    health.router,
    tags=["Health"]
)

api_router.include_router(
    policies.router,
    prefix="/policies",
    tags=["Policies"]
)

api_router.include_router(
    chunks.router,
    prefix="/policies",
    tags=["Chunks"]
)

api_router.include_router(
    embeddings.router,
    prefix="/policies",
    tags=["Embeddings"]
)

# Future endpoints will be added here:
# api_router.include_router(eligibility.router, prefix="/eligibility", tags=["Eligibility"])
