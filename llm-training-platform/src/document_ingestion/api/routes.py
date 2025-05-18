"""
API routes for document ingestion service
"""

import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from loguru import logger

from src.common.config.settings import settings
from src.common.db.database import get_db_session_dependency
from src.common.models.document import Document, DocumentStatus
from src.common.auth.auth_handler import get_current_active_user
from src.common.models.user import User
from src.document_ingestion.service.ingestion_service import IngestionService
from src.document_ingestion.api.schemas import (
    DocumentResponse, 
    DocumentListResponse,
    DocumentUploadResponse,
    DocumentProcessResponse,
    ErrorResponse
)


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"model": ErrorResponse}}
)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    language: str = Form("ar"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session_dependency)
):
    """
    Upload a document
    """
    try:
        # Check file size
        file_size = 0
        for chunk in file.file:
            file_size += len(chunk)
            if file_size > settings.document.max_file_size_mb * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Maximum size is {settings.document.max_file_size_mb} MB"
                )
        
        # Reset file pointer
        await file.seek(0)
        
        # Check file extension
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in settings.document.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {ext}. Supported types: {', '.join(settings.document.allowed_extensions)}"
            )
        
        # Create temp directory if it doesn't exist
        os.makedirs(settings.document.temp_dir, exist_ok=True)
        
        # Save file to temp directory
        temp_file_path = os.path.join(settings.document.temp_dir, f"{uuid.uuid4()}{ext}")
        with open(temp_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Upload document
        service = IngestionService(db)
        document = service.upload_document(
            file_path=temp_file_path,
            filename=file.filename,
            user_id=current_user.id,
            language=language,
            document_type=document_type
        )
        
        # Clean up temp file
        os.remove(temp_file_path)
        
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            document_type=document.document_type,
            language=document.language,
            status=document.status,
            upload_date=document.upload_date,
            message="Document uploaded successfully"
        )
        
    except ValueError as e:
        logger.error(f"Value error in upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.post("/{document_id}/process", response_model=DocumentProcessResponse)
async def process_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session_dependency)
):
    """
    Process a document
    """
    try:
        # Get the document
        service = IngestionService(db)
        document = service.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        # Check if user has access to the document
        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this document"
            )
        
        # Check if document is already being processed
        if document.status == DocumentStatus.PROCESSING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document is already being processed"
            )
        
        # Process the document
        result = service.process_document(document_id)
        
        # Get updated document
        document = service.get_document(document_id)
        
        return DocumentProcessResponse(
            id=document.id,
            filename=document.filename,
            status=document.status,
            success=result["success"],
            error=result.get("error"),
            processing_started_date=document.processing_started_date,
            processing_completed_date=document.processing_completed_date,
            message="Document processed successfully" if result["success"] else "Document processing failed"
        )
        
    except ValueError as e:
        logger.error(f"Value error in processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("", response_model=DocumentListResponse)
async def get_documents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session_dependency)
):
    """
    Get all documents for the current user
    """
    try:
        service = IngestionService(db)
        documents = service.get_documents_by_user(current_user.id)
        
        return DocumentListResponse(
            documents=[
                DocumentResponse(
                    id=doc.id,
                    filename=doc.filename,
                    file_type=doc.file_type,
                    document_type=doc.document_type,
                    language=doc.language,
                    status=doc.status,
                    page_count=doc.page_count,
                    word_count=doc.word_count,
                    upload_date=doc.upload_date,
                    processing_started_date=doc.processing_started_date,
                    processing_completed_date=doc.processing_completed_date,
                    error_message=doc.error_message
                )
                for doc in documents
            ],
            count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session_dependency)
):
    """
    Get a document by ID
    """
    try:
        service = IngestionService(db)
        document = service.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        # Check if user has access to the document
        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this document"
            )
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            document_type=document.document_type,
            language=document.language,
            status=document.status,
            page_count=document.page_count,
            word_count=document.word_count,
            upload_date=document.upload_date,
            processing_started_date=document.processing_started_date,
            processing_completed_date=document.processing_completed_date,
            error_message=document.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session_dependency)
):
    """
    Delete a document
    """
    try:
        service = IngestionService(db)
        document = service.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        # Check if user has access to the document
        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this document"
            )
        
        # Delete the document
        success = service.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )
