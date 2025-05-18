"""
Document Ingestion Service

This service handles the ingestion and preprocessing of various document formats:
- Scanned PDFs (image-based)
- Searchable PDFs
- TXT/DOCX file formats

It includes OCR capabilities with Arabic language support and preprocessing steps
such as noise reduction, deskewing, and text normalization.
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.common.config.settings import settings
from src.document_ingestion.api.routes import router as documents_router


# Initialize FastAPI app
app = FastAPI(
    title="Document Ingestion Service",
    description="Service for ingesting and preprocessing documents",
    version="1.0.0",
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
app.include_router(documents_router)

# Configure logging
logger.add(
    "logs/document_ingestion.log", 
    rotation=settings.log.rotation, 
    level=settings.log.level
)


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler
    """
    logger.info("Document Ingestion Service starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler
    """
    logger.info("Document Ingestion Service shutting down")


if __name__ == "__main__":
    uvicorn.run(
        "src.document_ingestion.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug
    )
