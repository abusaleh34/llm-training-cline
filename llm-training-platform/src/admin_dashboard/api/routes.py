"""
API routes for the Admin Dashboard service.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from loguru import logger
import httpx
import asyncio
import psutil
import os
import time
from datetime import datetime, timedelta

from src.common.db.database import get_db
from src.common.auth.auth_handler import get_current_active_user
from src.common.models.user import User
from src.admin_dashboard.api.schemas import (
    SystemResourcesResponse,
    DocumentStats,
    ModelStats,
    AgentStats,
    UserStats,
    DashboardStats,
    LogEntry,
    LogFilter,
    ServiceStatus,
    SystemStatus
)
from src.admin_dashboard.service.monitoring_service import (
    get_system_resources,
    get_service_status,
    get_logs
)
from src.admin_dashboard.service.stats_service import (
    get_document_stats,
    get_model_stats,
    get_agent_stats,
    get_user_stats
)


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/system/resources", response_model=SystemResourcesResponse)
async def get_system_resources_endpoint(
    current_user: User = Depends(get_current_active_user)
):
    """Get system resource usage (CPU, memory, disk)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin resources",
        )
    
    return await get_system_resources()


@router.get("/system/status", response_model=SystemStatus)
async def get_system_status_endpoint(
    current_user: User = Depends(get_current_active_user)
):
    """Get status of all services."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin resources",
        )
    
    return await get_service_status()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin resources",
        )
    
    # Gather all stats in parallel
    document_stats_task = asyncio.create_task(get_document_stats(db))
    model_stats_task = asyncio.create_task(get_model_stats(db))
    agent_stats_task = asyncio.create_task(get_agent_stats(db))
    user_stats_task = asyncio.create_task(get_user_stats(db))
    
    # Wait for all tasks to complete
    document_stats = await document_stats_task
    model_stats = await model_stats_task
    agent_stats = await agent_stats_task
    user_stats = await user_stats_task
    
    return DashboardStats(
        document_stats=document_stats,
        model_stats=model_stats,
        agent_stats=agent_stats,
        user_stats=user_stats,
        last_updated=datetime.now()
    )


@router.get("/logs", response_model=List[LogEntry])
async def get_logs_endpoint(
    service: Optional[str] = None,
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """Get logs from all services."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin resources",
        )
    
    log_filter = LogFilter(
        service=service,
        level=level,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return await get_logs(log_filter)


@router.post("/restart-service/{service_name}")
async def restart_service(
    service_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Restart a specific service."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin resources",
        )
    
    # This would typically be handled by Docker or Kubernetes
    # For now, we'll just return a success message
    logger.info(f"Admin {current_user.username} requested restart of {service_name}")
    
    return {"message": f"Service {service_name} restart initiated"}


@router.post("/clear-cache/{cache_type}")
async def clear_cache(
    cache_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """Clear a specific type of cache."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin resources",
        )
    
    logger.info(f"Admin {current_user.username} requested clearing of {cache_type} cache")
    
    # Implement cache clearing logic based on cache_type
    # For now, we'll just return a success message
    return {"message": f"{cache_type} cache cleared successfully"}
