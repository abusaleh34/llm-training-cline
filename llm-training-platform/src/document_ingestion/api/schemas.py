"""
API schemas for document ingestion service
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from src.common.models.document import DocumentStatus


class ErrorResponse(BaseModel):
    """Error response schema"""
    
    detail: str


class DocumentBase(BaseModel):
    """Base document schema"""
    
    id: str
    filename: str
    file_type: str
    document_type: Optional[str] = None
    language: str
    status: DocumentStatus


class DocumentResponse(DocumentBase):
    """Document response schema"""
    
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    upload_date: datetime
    processing_started_date: Optional[datetime] = None
    processing_completed_date: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        orm_mode = True


class DocumentListResponse(BaseModel):
    """Document list response schema"""
    
    documents: List[DocumentResponse]
    count: int


class DocumentUploadResponse(DocumentBase):
    """Document upload response schema"""
    
    upload_date: datetime
    message: str


class DocumentProcessResponse(BaseModel):
    """Document process response schema"""
    
    id: str
    filename: str
    status: DocumentStatus
    success: bool
    error: Optional[str] = None
    processing_started_date: Optional[datetime] = None
    processing_completed_date: Optional[datetime] = None
    message: str


class DocumentTextResponse(BaseModel):
    """Document text response schema"""
    
    id: str
    filename: str
    text: str
    language: str
    word_count: Optional[int] = None


class DocumentMetadataResponse(BaseModel):
    """Document metadata response schema"""
    
    id: str
    filename: str
    metadata: dict
