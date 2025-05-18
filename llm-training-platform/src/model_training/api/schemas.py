"""
API schemas for the Model Training service.
"""

from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ModelType(str, Enum):
    """Model type enum."""
    
    FINE_TUNED = "fine_tuned"
    RAG = "rag"


class ModelStatus(str, Enum):
    """Model status enum."""
    
    CREATED = "created"
    TRAINING = "training"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class TrainingType(str, Enum):
    """Training type enum."""
    
    FULL_FINE_TUNING = "full_fine_tuning"
    LORA = "lora"
    QLORA = "qlora"
    PEFT = "peft"


class TrainingStatus(str, Enum):
    """Training job status enum."""
    
    PENDING = "pending"
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorResponse(BaseModel):
    """Error response model."""
    
    detail: str


class TrainingConfigRequest(BaseModel):
    """Training configuration request model."""
    
    model_name: str = Field(..., description="Name of the model")
    base_model: str = Field(..., description="Base model to fine-tune")
    training_type: TrainingType = Field(..., description="Type of training")
    dataset_id: str = Field(..., description="Dataset ID to use for training")
    description: Optional[str] = Field(None, description="Model description")
    tags: Optional[List[str]] = Field(None, description="Model tags")
    hyperparameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Training hyperparameters",
        example={
            "learning_rate": 5e-5,
            "batch_size": 8,
            "epochs": 3,
            "warmup_steps": 100,
            "weight_decay": 0.01,
            "lora_r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
        },
    )


class RAGConfigRequest(BaseModel):
    """RAG configuration request model."""
    
    model_name: str = Field(..., description="Name of the model")
    base_model: str = Field(..., description="Base model for generation")
    embedding_model: str = Field(..., description="Embedding model for retrieval")
    dataset_id: str = Field(..., description="Dataset ID to use for retrieval")
    description: Optional[str] = Field(None, description="Model description")
    tags: Optional[List[str]] = Field(None, description="Model tags")
    retrieval_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Retrieval configuration",
        example={
            "top_k": 5,
            "similarity_threshold": 0.7,
            "reranking_enabled": False,
        },
    )
    generation_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Generation configuration",
        example={
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 50,
            "max_tokens": 1024,
        },
    )


class ModelResponse(BaseModel):
    """Model response model."""
    
    id: str = Field(..., description="Model ID")
    name: str = Field(..., description="Model name")
    model_type: ModelType = Field(..., description="Model type")
    base_model: str = Field(..., description="Base model")
    status: ModelStatus = Field(..., description="Model status")
    user_id: str = Field(..., description="User ID")
    description: Optional[str] = Field(None, description="Model description")
    tags: Optional[List[str]] = Field(None, description="Model tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Model metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        orm_mode = True


class ModelListResponse(BaseModel):
    """Model list response model."""
    
    models: List[ModelResponse] = Field(..., description="List of models")
    count: int = Field(..., description="Total count of models")


class TrainingJobResponse(BaseModel):
    """Training job response model."""
    
    id: str = Field(..., description="Training job ID")
    model_id: str = Field(..., description="Model ID")
    training_type: TrainingType = Field(..., description="Training type")
    dataset_id: str = Field(..., description="Dataset ID")
    status: TrainingStatus = Field(..., description="Training job status")
    progress: float = Field(..., description="Training progress (0-100)")
    hyperparameters: Optional[Dict[str, Any]] = Field(None, description="Training hyperparameters")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Training metrics")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        orm_mode = True


class TrainingJobListResponse(BaseModel):
    """Training job list response model."""
    
    jobs: List[TrainingJobResponse] = Field(..., description="List of training jobs")
    count: int = Field(..., description="Total count of training jobs")


class InferenceRequest(BaseModel):
    """Inference request model."""
    
    model_id: str = Field(..., description="Model ID")
    prompt: str = Field(..., description="Input prompt")
    generation_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Generation configuration",
        example={
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 50,
            "max_tokens": 1024,
        },
    )


class InferenceResponse(BaseModel):
    """Inference response model."""
    
    model_id: str = Field(..., description="Model ID")
    prompt: str = Field(..., description="Input prompt")
    generated_text: str = Field(..., description="Generated text")
    generation_config: Dict[str, Any] = Field(..., description="Generation configuration used")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Inference metadata")


class RetrievedContext(BaseModel):
    """Retrieved context model."""
    
    text: str = Field(..., description="Context text")
    document_id: str = Field(..., description="Document ID")
    document_name: str = Field(..., description="Document name")
    chunk_id: str = Field(..., description="Chunk ID")
    score: float = Field(..., description="Retrieval score")
    page_numbers: Optional[List[int]] = Field(None, description="Page numbers")


class RAGInferenceRequest(BaseModel):
    """RAG inference request model."""
    
    model_id: str = Field(..., description="RAG model ID")
    query: str = Field(..., description="User query")
    retrieval_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Retrieval configuration (overrides model defaults)",
        example={
            "top_k": 5,
            "similarity_threshold": 0.7,
        },
    )
    generation_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Generation configuration (overrides model defaults)",
        example={
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 1024,
        },
    )


class RAGInferenceResponse(BaseModel):
    """RAG inference response model."""
    
    model_id: str = Field(..., description="RAG model ID")
    query: str = Field(..., description="User query")
    answer: str = Field(..., description="Generated answer")
    contexts: List[RetrievedContext] = Field(..., description="Retrieved contexts")
    retrieval_config: Dict[str, Any] = Field(..., description="Retrieval configuration used")
    generation_config: Dict[str, Any] = Field(..., description="Generation configuration used")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Inference metadata")
