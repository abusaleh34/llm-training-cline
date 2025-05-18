"""
API schemas for the Admin Dashboard service.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ResourceUsage(BaseModel):
    """System resource usage."""
    
    current: float = Field(..., description="Current usage percentage")
    average: float = Field(..., description="Average usage over time period")
    peak: float = Field(..., description="Peak usage over time period")
    time_period_minutes: int = Field(..., description="Time period in minutes for average and peak")


class DiskUsage(BaseModel):
    """Disk usage information."""
    
    total_gb: float = Field(..., description="Total disk space in GB")
    used_gb: float = Field(..., description="Used disk space in GB")
    free_gb: float = Field(..., description="Free disk space in GB")
    usage_percent: float = Field(..., description="Usage percentage")


class SystemResourcesResponse(BaseModel):
    """System resources response."""
    
    cpu: ResourceUsage = Field(..., description="CPU usage")
    memory: ResourceUsage = Field(..., description="Memory usage")
    disk: DiskUsage = Field(..., description="Disk usage")
    gpu: Optional[ResourceUsage] = Field(None, description="GPU usage if available")
    timestamp: datetime = Field(..., description="Timestamp of the measurement")


class ServiceStatus(BaseModel):
    """Service status information."""
    
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status (running, stopped, error)")
    uptime: Optional[str] = Field(None, description="Service uptime")
    health: str = Field(..., description="Health status (healthy, unhealthy, warning)")
    version: Optional[str] = Field(None, description="Service version")
    last_restart: Optional[datetime] = Field(None, description="Last restart time")


class SystemStatus(BaseModel):
    """Overall system status."""
    
    services: List[ServiceStatus] = Field(..., description="Status of all services")
    overall_health: str = Field(..., description="Overall system health (healthy, degraded, critical)")
    timestamp: datetime = Field(..., description="Timestamp of the status check")


class DocumentStats(BaseModel):
    """Document statistics."""
    
    total_documents: int = Field(..., description="Total number of documents")
    documents_by_type: Dict[str, int] = Field(..., description="Documents by type")
    total_pages: int = Field(..., description="Total number of pages")
    total_size_mb: float = Field(..., description="Total size in MB")
    documents_processed_24h: int = Field(..., description="Documents processed in last 24 hours")
    processing_success_rate: float = Field(..., description="Processing success rate")


class ModelStats(BaseModel):
    """Model statistics."""
    
    total_models: int = Field(..., description="Total number of models")
    models_by_type: Dict[str, int] = Field(..., description="Models by type")
    fine_tuned_models: int = Field(..., description="Number of fine-tuned models")
    total_training_hours: float = Field(..., description="Total training hours")
    average_training_time: float = Field(..., description="Average training time in hours")
    training_jobs_24h: int = Field(..., description="Training jobs in last 24 hours")


class AgentStats(BaseModel):
    """Agent statistics."""
    
    total_agents: int = Field(..., description="Total number of agents")
    active_agents: int = Field(..., description="Number of active agents")
    agents_by_type: Dict[str, int] = Field(..., description="Agents by type")
    total_interactions: int = Field(..., description="Total number of interactions")
    interactions_24h: int = Field(..., description="Interactions in last 24 hours")
    average_response_time_ms: float = Field(..., description="Average response time in ms")


class UserStats(BaseModel):
    """User statistics."""
    
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    users_by_role: Dict[str, int] = Field(..., description="Users by role")
    logins_24h: int = Field(..., description="Logins in last 24 hours")
    average_session_duration: float = Field(..., description="Average session duration in minutes")


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    
    document_stats: DocumentStats = Field(..., description="Document statistics")
    model_stats: ModelStats = Field(..., description="Model statistics")
    agent_stats: AgentStats = Field(..., description="Agent statistics")
    user_stats: UserStats = Field(..., description="User statistics")
    last_updated: datetime = Field(..., description="Last updated timestamp")


class LogLevel(str, Enum):
    """Log level enum."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry(BaseModel):
    """Log entry."""
    
    timestamp: datetime = Field(..., description="Log timestamp")
    service: str = Field(..., description="Service name")
    level: LogLevel = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    trace_id: Optional[str] = Field(None, description="Trace ID for distributed tracing")


class LogFilter(BaseModel):
    """Log filter."""
    
    service: Optional[str] = Field(None, description="Filter by service name")
    level: Optional[LogLevel] = Field(None, description="Filter by log level")
    start_time: Optional[datetime] = Field(None, description="Filter by start time")
    end_time: Optional[datetime] = Field(None, description="Filter by end time")
    limit: int = Field(100, description="Limit number of logs")
