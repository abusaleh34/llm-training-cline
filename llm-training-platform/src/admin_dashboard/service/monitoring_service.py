"""
Monitoring service for the Admin Dashboard.
"""

import os
import psutil
import platform
import socket
import time
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import glob
from loguru import logger

from src.common.config.settings import settings
from src.admin_dashboard.api.schemas import (
    SystemResourcesResponse,
    ResourceUsage,
    DiskUsage,
    ServiceStatus,
    SystemStatus,
    LogEntry,
    LogFilter
)


async def get_system_resources() -> SystemResourcesResponse:
    """Get system resource usage (CPU, memory, disk)."""
    # Get CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_times = psutil.cpu_times_percent(interval=1)
    
    # Get memory usage
    memory = psutil.virtual_memory()
    
    # Get disk usage
    disk = psutil.disk_usage('/')
    
    # Get GPU usage if available
    gpu_usage = None
    try:
        # This would typically use a library like pynvml for NVIDIA GPUs
        # For now, we'll just return None
        pass
    except Exception as e:
        logger.warning(f"Failed to get GPU usage: {str(e)}")
    
    # Calculate average and peak usage (mock data for now)
    # In a real implementation, this would come from a time-series database
    cpu_avg = max(0, min(100, cpu_percent - 5 + (10 * (time.time() % 10) / 10)))
    cpu_peak = max(0, min(100, cpu_percent + 10))
    
    mem_avg = max(0, min(100, memory.percent - 5 + (10 * (time.time() % 10) / 10)))
    mem_peak = max(0, min(100, memory.percent + 10))
    
    return SystemResourcesResponse(
        cpu=ResourceUsage(
            current=cpu_percent,
            average=cpu_avg,
            peak=cpu_peak,
            time_period_minutes=60
        ),
        memory=ResourceUsage(
            current=memory.percent,
            average=mem_avg,
            peak=mem_peak,
            time_period_minutes=60
        ),
        disk=DiskUsage(
            total_gb=disk.total / (1024 ** 3),
            used_gb=disk.used / (1024 ** 3),
            free_gb=disk.free / (1024 ** 3),
            usage_percent=disk.percent
        ),
        gpu=gpu_usage,
        timestamp=datetime.now()
    )


async def get_service_status() -> SystemStatus:
    """Get status of all services."""
    services = [
        "api-gateway",
        "document-ingestion",
        "data-structuring",
        "model-training",
        "agent-deployment",
        "admin-dashboard"
    ]
    
    service_statuses = []
    overall_health = "healthy"
    
    for service in services:
        # In a real implementation, this would check the actual service status
        # For now, we'll just return mock data
        
        # Simulate some services having issues
        status = "running"
        health = "healthy"
        
        if service == "model-training" and time.time() % 30 < 5:
            status = "warning"
            health = "warning"
            overall_health = "degraded"
        
        if service == "data-structuring" and time.time() % 60 < 3:
            status = "error"
            health = "unhealthy"
            overall_health = "critical"
        
        service_statuses.append(
            ServiceStatus(
                name=service,
                status=status,
                uptime="3d 12h 45m",
                health=health,
                version="1.0.0",
                last_restart=datetime.now() - timedelta(days=3, hours=12, minutes=45)
            )
        )
    
    return SystemStatus(
        services=service_statuses,
        overall_health=overall_health,
        timestamp=datetime.now()
    )


async def get_logs(log_filter: LogFilter) -> List[LogEntry]:
    """Get logs from all services."""
    logs = []
    
    # In a real implementation, this would query logs from a centralized logging system
    # For now, we'll just return mock data
    
    # Define some sample log messages
    sample_messages = [
        "Service started successfully",
        "Processing document: document1.pdf",
        "Document processed successfully",
        "Training model: model1",
        "Model training completed successfully",
        "Error processing document: invalid format",
        "Warning: high memory usage detected",
        "User authentication failed: invalid credentials",
        "Database connection established",
        "API request received: GET /api/documents"
    ]
    
    # Define some sample services
    sample_services = [
        "api-gateway",
        "document-ingestion",
        "data-structuring",
        "model-training",
        "agent-deployment",
        "admin-dashboard"
    ]
    
    # Define some sample log levels
    sample_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
    
    # Generate mock logs
    for i in range(log_filter.limit):
        # Calculate a timestamp that's somewhat recent but varies
        hours_ago = (i % 24)
        minutes_ago = (i % 60)
        seconds_ago = (i % 60)
        timestamp = datetime.now() - timedelta(
            hours=hours_ago, 
            minutes=minutes_ago, 
            seconds=seconds_ago
        )
        
        # Select a service, message, and level based on the index
        service = sample_services[i % len(sample_services)]
        message = sample_messages[i % len(sample_messages)]
        level = sample_levels[i % len(sample_levels)]
        
        # Apply filters
        if log_filter.service and service != log_filter.service:
            continue
        
        if log_filter.level and level != log_filter.level:
            continue
        
        if log_filter.start_time and timestamp < log_filter.start_time:
            continue
        
        if log_filter.end_time and timestamp > log_filter.end_time:
            continue
        
        # Create a log entry
        log_entry = LogEntry(
            timestamp=timestamp,
            service=service,
            level=level,
            message=message,
            context={"request_id": f"req-{i}", "user_id": f"user-{i % 10}"},
            trace_id=f"trace-{i}"
        )
        
        logs.append(log_entry)
    
    # Sort logs by timestamp (newest first)
    logs.sort(key=lambda x: x.timestamp, reverse=True)
    
    return logs
