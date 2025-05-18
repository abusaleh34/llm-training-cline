"""
API routes for data structuring service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from loguru import logger

from src.common.db.database import get_db_session_dependency
from src.common.models.document import Document, DocumentStatus
from src.common.auth.auth_handler import get_current_active_user
from src.common.models.user import User
from src.data_structuring.api.schemas import (
    ChunkResponse,
    ChunkListResponse,
    DatasetResponse,
    DatasetListResponse,
    DatasetCreateRequest,
    ChunkingConfigRequest,
    ErrorResponse,
    ProcessingResponse
)
from src.data_structuring.service.structuring_service import StructuringService
from src.data_structuring.service.dataset_service import DatasetService


router = APIRouter(
    prefix="/data",
    tags=["data_structuring"],
    responses={404: {"model": ErrorResponse}}
)


@router.post("/documents/{document_id}/chunk", response_model=ProcessingResponse)
async def chunk_document(
    document_id: str,
    config: ChunkingConfigRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session_dependency)
):
    """
    Chunk a document into smaller pieces for processing
    """
    try:
        # Get the document
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        # Check if user has access to the document
        if document.user_id != current_user.id and current_user.role not in ["ADMIN", "MANAGER"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this document"
            )
        
        # Check if document is processed
        if document.status != DocumentStatus.PROCESSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document must be processed before chunking"
            )
        
        # Chunk the document
        service = StructuringService(db)
        result = await service.chunk_document(
            document_id=document_id,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            chunk_strategy=config.chunk_strategy
        )
        
        return ProcessingResponse(
            id=document_id,
            success=result["success"],
            message=result["message"],
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error chunking document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error chunking document: {str(e)}"
        )


@router.get("/documents/{document_id}/chunks", response_model=ChunkListResponse)
async def get_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session_dependency)
):
    """
    Get all chunks for a document
    """
    try:
        # Get the document
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        # Check if user has access to the document
        if document.user_id != current_user.id and current_user.role not in ["ADMIN", "MANAGER"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this document"
            )
        
        # Get chunks
        service = StructuringService(db)
        chunks = await service.get_document_chunks(document_id)
        
        return ChunkListResponse(
            document_id=document_id,
            chunks=chunks,
            count=len(chunks)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document chunks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document chunks: {str(e)}"
        )


@router.post("/datasets", response_model=DatasetResponse)
async def create_dataset(
    dataset: DatasetCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session_dependency)
):
    """
    Create a new dataset from documents
    """
    try:
        # Check if user has access to all documents
        for doc_id in dataset.document_ids:
            document = db.query(Document).filter(Document.id == doc_id).first()
            
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document not found: {doc_id}"
                )
            
            if document.user_id != current_user.id and current_user.role not in ["ADMIN", "MANAGER"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to access document: {doc_id}"
                )
        
        # Create dataset
        service = DatasetService(db)
        dataset_obj = await service.create_dataset(
            name=dataset.name,
            description=dataset.description,
            document_ids=dataset.document_ids,
            user_id=current_user.id
        )
        
        return DatasetResponse(
            id=dataset_obj.id,
            name=dataset_obj.name,
            description=dataset_obj.description,
            document_count=len(dataset.document_ids),
            chunk_count=dataset_obj.chunk_count,
            created_at=dataset_obj.created_at,
            updated_at=dataset_obj.updated_at,
            user_id=dataset_obj.user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating dataset: {str(e)}"
        )


@router.get("/datasets", response_model=DatasetListResponse)
async def get_datasets(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session_dependency)
):
    """
    Get all datasets for the current user
    """
    try:
        service = DatasetService(db)
        datasets = await service.get_user_datasets(current_user.id)
        
        return DatasetListResponse(
            datasets=[
                DatasetResponse(
                    id=ds.id,
                    name=ds.name,
                    description=ds.description,
                    document_count=ds.document_count,
                    chunk_count=ds.chunk_count,
                    created_at=ds.created_at,
                    updated_at=ds.updated_at,
                    user_id=ds.user_id
                )
                for ds in datasets
            ],
            count=len(datasets)
        )
        
    except Exception as e:
        logger.error(f"Error getting datasets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting datasets: {str(e)}"
        )


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session_dependency)
):
    """
    Get a dataset by ID
    """
    try:
        service = DatasetService(db)
        dataset = await service.get_dataset(dataset_id)
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset not found: {dataset_id}"
            )
        
        # Check if user has access to the dataset
        if dataset.user_id != current_user.id and current_user.role not in ["ADMIN", "MANAGER"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this dataset"
            )
        
        return DatasetResponse(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            document_count=dataset.document_count,
            chunk_count=dataset.chunk_count,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            user_id=dataset.user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting dataset: {str(e)}"
        )


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session_dependency)
):
    """
    Delete a dataset
    """
    try:
        service = DatasetService(db)
        dataset = await service.get_dataset(dataset_id)
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset not found: {dataset_id}"
            )
        
        # Check if user has access to the dataset
        if dataset.user_id != current_user.id and current_user.role not in ["ADMIN", "MANAGER"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this dataset"
            )
        
        # Delete dataset
        success = await service.delete_dataset(dataset_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete dataset"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting dataset: {str(e)}"
        )
