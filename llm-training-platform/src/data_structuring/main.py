"""
Main module for the Data Structuring service.
"""

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.common.config.settings import settings
from src.data_structuring.api.routes import router as data_structuring_router
from src.common.db.database import init_db

# Create FastAPI app
app = FastAPI(
    title="LLM Training Platform - Data Structuring Service",
    description="Service for structuring and indexing document data",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data_structuring_router)

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Initializing database connection...")
    init_db()
    logger.info("Database connection initialized.")
    
    # Initialize vector store
    from src.data_structuring.vector_store.vector_store import init_vector_store
    await init_vector_store()
    
    logger.info("Data Structuring service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Data Structuring service...")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "data_structuring"}


if __name__ == "__main__":
    uvicorn.run(
        "src.data_structuring.main:app",
        host=settings.service.host,
        port=settings.service.port,
        reload=settings.api.debug,
    )
