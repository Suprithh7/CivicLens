from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.config import settings
from app.api.v1.router import api_router
from app.core.database import close_db
from app.core.logging_config import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.exceptions import CivicLensException
from app.core.exception_handlers import (
    civiclens_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

# Setup logging
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR,
    log_to_file=settings.LOG_TO_FILE,
    log_to_console=settings.LOG_TO_CONSOLE,
    json_logs=settings.LOG_JSON_FORMAT
)

logger = logging.getLogger(__name__)

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

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Register exception handlers
app.add_exception_handler(CivicLensException, civiclens_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API v1 router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - redirects to docs."""
    logger.debug("Root endpoint accessed")
    return {
        "message": "Welcome to CivicLens AI API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info(f"📍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"💾 Database: {settings.DATABASE_URL.split('@')[-1]}")  # Hide credentials
    logger.info(f"🔗 Docs: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"📝 Logging: Level={settings.LOG_LEVEL}, Dir={settings.LOG_DIR}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"👋 {settings.APP_NAME} shutting down...")
    logger.info("💾 Closing database connections...")
    await close_db()
    logger.info("✅ Shutdown complete")

