"""
API schemas for data structuring service
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChunkStrategy(str, Enum):
    """Chunking strategy for document text"""
    
    FIXED_SIZE = "FIXED_SIZE"
    SENTENCE = "SENTENCE"
    PARAGRAPH = "PARAGRAPH"
    SEMANTIC = "SEMANTIC"


class ChunkingConfigRequest(BaseModel):
    """Request model for document chunking configuration"""
    
    chunk_size: int = Field(default=1000, description="Size of each chunk in tokens/characters")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks in tokens/characters")
    chunk_strategy: ChunkStrategy = Field(default=ChunkStrategy.FIXED_SIZE, description="Strategy for chunking")
    
    class Config:
        schema_extra = {
            "example": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "chunk_strategy": "FIXED_SIZE"
            }
        }


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk"""
    
    page_numbers: List[int] = Field(default_factory=list, description="Page numbers where this chunk appears")
    source_document_id: str = Field(..., description="ID of the source document")
    source_document_name: str = Field(..., description="Name of the source document")
    position: int = Field(..., description="Position of the chunk in the document")
    additional_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ChunkResponse(BaseModel):
    """Response model for a document chunk"""
    
    id: str = Field(..., description="Chunk ID")
    document_id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Chunk text content")
    metadata: ChunkMetadata = Field(..., description="Chunk metadata")
    embedding_id: Optional[str] = Field(default=None, description="ID of the embedding in the vector store")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "document_id": "123e4567-e89b-12d3-a456-426614174001",
                "text": "This is a sample chunk of text from a document...",
                "metadata": {
                    "page_numbers": [1, 2],
                    "source_document_id": "123e4567-e89b-12d3-a456-426614174001",
                    "source_document_name": "sample_document.pdf",
                    "position": 0,
                    "additional_metadata": {
                        "section": "Introduction"
                    }
                },
                "embedding_id": "vector_123",
                "created_at": "2023-01-01T00:00:00Z"
            }
        }


class ChunkListResponse(BaseModel):
    """Response model for a list of document chunks"""
    
    document_id: str = Field(..., description="Document ID")
    chunks: List[ChunkResponse] = Field(..., description="List of chunks")
    count: int = Field(..., description="Number of chunks")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174001",
                "chunks": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "document_id": "123e4567-e89b-12d3-a456-426614174001",
                        "text": "This is a sample chunk of text from a document...",
                        "metadata": {
                            "page_numbers": [1, 2],
                            "source_document_id": "123e4567-e89b-12d3-a456-426614174001",
                            "source_document_name": "sample_document.pdf",
                            "position": 0,
                            "additional_metadata": {
                                "section": "Introduction"
                            }
                        },
                        "embedding_id": "vector_123",
                        "created_at": "2023-01-01T00:00:00Z"
                    }
                ],
                "count": 1
            }
        }


class DatasetCreateRequest(BaseModel):
    """Request model for creating a dataset"""
    
    name: str = Field(..., description="Dataset name")
    description: Optional[str] = Field(default=None, description="Dataset description")
    document_ids: List[str] = Field(..., description="List of document IDs to include in the dataset")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Legal Contracts Dataset",
                "description": "A collection of legal contracts for training",
                "document_ids": [
                    "123e4567-e89b-12d3-a456-426614174001",
                    "123e4567-e89b-12d3-a456-426614174002"
                ]
            }
        }


class DatasetResponse(BaseModel):
    """Response model for a dataset"""
    
    id: str = Field(..., description="Dataset ID")
    name: str = Field(..., description="Dataset name")
    description: Optional[str] = Field(default=None, description="Dataset description")
    document_count: int = Field(..., description="Number of documents in the dataset")
    chunk_count: int = Field(..., description="Number of chunks in the dataset")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    user_id: str = Field(..., description="ID of the user who created the dataset")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "name": "Legal Contracts Dataset",
                "description": "A collection of legal contracts for training",
                "document_count": 2,
                "chunk_count": 150,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "user_id": "123e4567-e89b-12d3-a456-426614174004"
            }
        }


class DatasetListResponse(BaseModel):
    """Response model for a list of datasets"""
    
    datasets: List[DatasetResponse] = Field(..., description="List of datasets")
    count: int = Field(..., description="Number of datasets")
    
    class Config:
        schema_extra = {
            "example": {
                "datasets": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174003",
                        "name": "Legal Contracts Dataset",
                        "description": "A collection of legal contracts for training",
                        "document_count": 2,
                        "chunk_count": 150,
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z",
                        "user_id": "123e4567-e89b-12d3-a456-426614174004"
                    }
                ],
                "count": 1
            }
        }


class ProcessingResponse(BaseModel):
    """Response model for processing operations"""
    
    id: str = Field(..., description="ID of the processed resource")
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Processing message")
    error: Optional[str] = Field(default=None, description="Error message if operation failed")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "success": True,
                "message": "Document chunked successfully",
                "error": None
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors"""
    
    detail: str = Field(..., description="Error message")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Document not found: 123e4567-e89b-12d3-a456-426614174001"
            }
        }
