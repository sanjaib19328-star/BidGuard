from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
import logging
import os

from app.core.config import settings
from app.core.database import AsyncSessionLocal

# Setup logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("bidguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing BidGuard AI Backend...")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Upload directory ensured at: {os.path.abspath(settings.UPLOAD_DIR)}")
    logger.info(f"Environment: {settings.ENVIRONMENT} (Debug: {settings.DEBUG})")
    yield
    # Shutdown
    logger.info("Shutting down BidGuard AI Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="BidGuard AI - AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
from app.api.v1 import api_router

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/api/health", tags=["Health"])
async def health_check(response: Response):
    """Health check endpoint testing PostgreSQL connectivity."""
    db_status = "disconnected"
    db_error = None
    is_healthy = False

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                db_status = "connected"
                is_healthy = True
    except Exception as exc:
        db_status = "disconnected"
        db_error = str(exc)
        logger.warning(f"Database health check failed: {exc}")

    if is_healthy:
        response.status_code = status.HTTP_200_OK
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "database": db_status,
        }
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "database": db_status,
            "error": "Database connectivity check failed" if not settings.DEBUG else db_error,
        }


@app.get("/", tags=["Root"], status_code=status.HTTP_200_OK)
async def root():
    """Root redirect / information endpoint."""
    return {
        "message": "Welcome to BidGuard AI API",
        "docs": "/docs",
        "health": "/api/health",
        "version": settings.VERSION,
    }
