from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router
from app.core.database import close_db

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered platform to translate government policies into personalized, multilingual guidance",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - redirects to docs."""
    return {
        "message": "Welcome to CivicLens AI API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"💾 Database: {settings.DATABASE_URL.split('@')[-1]}")  # Hide credentials
    print(f"🔗 Docs: http://{settings.HOST}:{settings.PORT}/docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print(f"👋 {settings.APP_NAME} shutting down...")
    print("💾 Closing database connections...")
    await close_db()
    print("✅ Shutdown complete")
