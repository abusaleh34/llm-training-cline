"""
Main entry point for the Model Training service.
"""

import os
import sys
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import uvicorn

# Add parent directory to path to allow imports from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.common.config.settings import settings
from src.common.db.database import init_db, get_db
from src.model_training.api.routes import router as model_training_router
from src.model_training.training.training_manager import stop_all_training_jobs


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
)
logger.add(
    f"logs/model_training_{os.getpid()}.log",
    rotation=settings.LOG_ROTATION,
    level=settings.LOG_LEVEL,
)

# Create FastAPI app
app = FastAPI(
    title="LLM Training Platform - Model Training Service",
    description="Service for training and fine-tuning language models, as well as setting up RAG systems",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(model_training_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and other resources on startup."""
    logger.info("Starting Model Training service")
    
    # Initialize database
    await init_db()
    
    # Create necessary directories
    os.makedirs(settings.MODEL_STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.MODEL_CACHE_PATH, exist_ok=True)
    
    logger.info(f"Model storage path: {settings.MODEL_STORAGE_PATH}")
    logger.info(f"Model cache path: {settings.MODEL_CACHE_PATH}")
    logger.info(f"Maximum concurrent training jobs: {settings.MAX_TRAINING_JOBS}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Model Training service")
    
    # Stop all active training jobs
    await stop_all_training_jobs()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "model_training"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Model Training",
        "version": "0.1.0",
        "description": "Service for training and fine-tuning language models, as well as setting up RAG systems",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.ENVIRONMENT == "development",
    )
