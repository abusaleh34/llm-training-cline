"""
Main entry point for the Agent Deployment service.
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
from src.agent_deployment.api.routes import router as agent_deployment_router
from src.agent_deployment.service.agent_manager import stop_all_agents


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
)
logger.add(
    f"logs/agent_deployment_{os.getpid()}.log",
    rotation=settings.LOG_ROTATION,
    level=settings.LOG_LEVEL,
)

# Create FastAPI app
app = FastAPI(
    title="LLM Training Platform - Agent Deployment Service",
    description="Service for deploying and interacting with AI agents",
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
app.include_router(agent_deployment_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and other resources on startup."""
    logger.info("Starting Agent Deployment service")
    
    # Initialize database
    await init_db()
    
    # Create necessary directories
    os.makedirs(settings.MODEL_STORAGE_PATH, exist_ok=True)
    
    logger.info(f"Model storage path: {settings.MODEL_STORAGE_PATH}")
    logger.info(f"Maximum deployed agents: {settings.MAX_DEPLOYED_AGENTS}")
    logger.info(f"Agent timeout seconds: {settings.AGENT_TIMEOUT_SECONDS}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Agent Deployment service")
    
    # Stop all active agents
    await stop_all_agents()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "agent_deployment"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Agent Deployment",
        "version": "0.1.0",
        "description": "Service for deploying and interacting with AI agents",
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
