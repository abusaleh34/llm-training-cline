"""
Main entry point for the Admin Dashboard service.
"""

import os
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import asyncio
from pathlib import Path

from src.common.config.settings import settings
from src.common.db.database import init_db
from src.common.auth.auth_handler import get_current_active_user
from src.admin_dashboard.api.routes import router as admin_router

# Configure logger
logger.add(
    f"logs/{settings.SERVICE_NAME}.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    backtrace=True,
    diagnose=True,
)

# Create FastAPI app
app = FastAPI(
    title="LLM Training Platform - Admin Dashboard",
    description="Admin Dashboard for the LLM Training Platform",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static"
)

# Set up templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Include API routes
app.include_router(admin_router)


@app.get("/", tags=["UI"])
async def index(request: Request):
    """Render the admin dashboard UI."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "LLM Training Platform - Admin Dashboard"}
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info(f"Starting {settings.SERVICE_NAME} service")
    
    # Initialize database
    await init_db()
    
    logger.info(f"{settings.SERVICE_NAME} service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Run shutdown tasks."""
    logger.info(f"Shutting down {settings.SERVICE_NAME} service")


if __name__ == "__main__":
    uvicorn.run(
        "src.admin_dashboard.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
