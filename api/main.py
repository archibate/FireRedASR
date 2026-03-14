"""FastAPI application entry point for FireRedASR API."""

import logging
import os
import sys

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.config import settings
from api.routes.transcribe import router as transcribe_router
from api.services.asr_service import asr_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for model loading.

    Loads the ASR model at startup and keeps it in memory.
    """
    # Startup: Load model
    logger.info("Starting FireRedASR API server...")
    logger.info(f"Configuration: asr_type={settings.asr_type}, device={settings.device}")

    try:
        asr_service.load_model()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        # Continue running so health endpoint can report the error

    yield

    # Shutdown: Cleanup (if needed)
    logger.info("Shutting down FireRedASR API server...")


# Create FastAPI application
app = FastAPI(
    title="FireRedASR API",
    description="RESTful API for FireRedASR speech recognition",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transcribe_router)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "FireRedASR API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        timeout_keep_alive=settings.timeout_keep_alive,
        reload=False,
    )
