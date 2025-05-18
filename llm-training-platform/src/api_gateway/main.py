"""
API Gateway

This is the main entry point for the LLM Training Platform API.
It routes requests to the appropriate microservices.
"""

import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from loguru import logger

from src.security import tls_manager
from src.common.db.database import get_db

from src.common.config.settings import settings
from src.common.auth.api import router as auth_router
from src.common.users.api import router as users_router
from src.document_ingestion.api.routes import router as document_router


# Initialize FastAPI app
app = FastAPI(
    title="LLM Training Platform API",
    description=settings.description,
    version=settings.version,
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth_router, prefix=settings.api.api_prefix)
app.include_router(users_router, prefix=settings.api.api_prefix)
app.include_router(document_router, prefix=settings.api.api_prefix)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Custom Swagger UI
    """
    return get_swagger_ui_html(
        openapi_url=f"{settings.api.api_prefix}/openapi.json",
        title=f"{app.title} - API Documentation",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint
    """
    return {
        "name": settings.app_name,
        "version": settings.version,
        "description": settings.description,
        "docs": f"{settings.api.api_prefix}/docs"
    }


@app.get("/healthz", include_in_schema=False)
async def health_check():
    """
    Health check endpoint for monitoring and deployment validation
    """
    try:
        # Check database connection
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    # Overall health status
    status = "healthy" if db_status == "healthy" else "unhealthy"
    status_code = 200 if status == "healthy" else 503
    
    response = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.version,
        "environment": settings.environment,
        "components": {
            "database": db_status
        }
    }
    
    return JSONResponse(content=response, status_code=status_code)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler
    """
    logger.info("API Gateway starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler
    """
    logger.info("API Gateway shutting down")


if __name__ == "__main__":
    # Configure SSL if enabled
    ssl_config = {}
    if settings.security.enable_https:
        try:
            ssl_config = tls_manager.get_uvicorn_ssl_config()
            logger.info("HTTPS enabled with SSL configuration")
        except Exception as e:
            logger.error(f"Failed to configure SSL: {str(e)}")
            logger.warning("Falling back to HTTP")
    
    uvicorn.run(
        "src.api_gateway.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        **ssl_config
    )
