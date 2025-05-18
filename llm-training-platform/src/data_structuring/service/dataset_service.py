"""
Dataset service for the LLM Training Platform.
"""

import os
import uuid
from typing import List, Dict, Any, Optional, Union
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.common.models.document import Document
from src.data_structuring.models.dataset import Dataset, DatasetChunk
from src.data_structuring.models.chunk import DocumentChunk


class DatasetService:
    """Service for managing datasets."""
    
    def __init__(self, db: Session):
        """
        Initialize the dataset service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_dataset(
        self,
        name: str,
        document_ids: List[str],
        user_id: str,
        description: Optional[str] = None,
    ) -> Dataset:
        """
        Create a new dataset from documents.
        
        Args:
            name: Dataset name
            document_ids: List of document IDs to include in the dataset
            user_id: User ID
            description: Dataset description
            
        Returns:
            Dataset: Created dataset
        """
        try:
            # Validate documents
            documents = []
            
            for doc_id in document_ids:
                document = self.db.query(Document).filter(Document.id == doc_id).first()
                
                if not document:
                    logger.warning(f"Document not found: {doc_id}")
                    continue
                
                documents.append(document)
            
            if not documents:
                raise ValueError("No valid documents provided")
            
            # Create dataset
            dataset = Dataset(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                document_count=len(documents),
                user_id=user_id,
                metadata={
                    "document_ids": [doc.id for doc in documents],
                    "document_names": [doc.filename for doc in documents],
                    "document_types": [doc.file_type for doc in documents],
                }
            )
            
            self.db.add(dataset)
            
            # Associate documents with dataset
            for document in documents:
                dataset.documents.append(document)
            
            # Get chunks for documents
            chunk_count = 0
            
            for document in documents:
                chunks = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).all()
                
                if not chunks:
                    logger.warning(f"No chunks found for document: {document.id}")
                    continue
                
                # Associate chunks with dataset
                for chunk in chunks:
                    dataset_chunk = DatasetChunk(
                        id=str(uuid.uuid4()),
                        dataset_id=dataset.id,
                        chunk_id=chunk.id,
                    )
                    
                    self.db.add(dataset_chunk)
                    chunk_count += 1
            
            # Update chunk count
            dataset.chunk_count = chunk_count
            
            self.db.commit()
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error creating dataset: {str(e)}")
            self.db.rollback()
            raise
    
    async def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """
        Get a dataset by ID.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Optional[Dataset]: Dataset if found, None otherwise
        """
        try:
            return self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        except Exception as e:
            logger.error(f"Error getting dataset: {str(e)}")
            return None
    
    async def get_user_datasets(self, user_id: str) -> List[Dataset]:
        """
        Get all datasets for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[Dataset]: List of datasets
        """
        try:
            return self.db.query(Dataset).filter(Dataset.user_id == user_id).all()
        except Exception as e:
            logger.error(f"Error getting user datasets: {str(e)}")
            return []
    
    async def delete_dataset(self, dataset_id: str) -> bool:
        """
        Delete a dataset.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get dataset
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                logger.warning(f"Dataset not found: {dataset_id}")
                return False
            
            # Delete dataset
            self.db.delete(dataset)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting dataset: {str(e)}")
            self.db.rollback()
            return False
    
    async def add_documents_to_dataset(
        self,
        dataset_id: str,
        document_ids: List[str],
    ) -> bool:
        """
        Add documents to a dataset.
        
        Args:
            dataset_id: Dataset ID
            document_ids: List of document IDs to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get dataset
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                logger.warning(f"Dataset not found: {dataset_id}")
                return False
            
            # Validate documents
            documents = []
            
            for doc_id in document_ids:
                document = self.db.query(Document).filter(Document.id == doc_id).first()
                
                if not document:
                    logger.warning(f"Document not found: {doc_id}")
                    continue
                
                documents.append(document)
            
            if not documents:
                logger.warning("No valid documents provided")
                return False
            
            # Add documents to dataset
            added_count = 0
            
            for document in documents:
                # Check if document is already in dataset
                if document in dataset.documents:
                    logger.info(f"Document already in dataset: {document.id}")
                    continue
                
                # Add document to dataset
                dataset.documents.append(document)
                
                # Get chunks for document
                chunks = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).all()
                
                if not chunks:
                    logger.warning(f"No chunks found for document: {document.id}")
                    continue
                
                # Associate chunks with dataset
                for chunk in chunks:
                    # Check if chunk is already in dataset
                    existing = self.db.query(DatasetChunk).filter(
                        DatasetChunk.dataset_id == dataset.id,
                        DatasetChunk.chunk_id == chunk.id
                    ).first()
                    
                    if existing:
                        logger.info(f"Chunk already in dataset: {chunk.id}")
                        continue
                    
                    dataset_chunk = DatasetChunk(
                        id=str(uuid.uuid4()),
                        dataset_id=dataset.id,
                        chunk_id=chunk.id,
                    )
                    
                    self.db.add(dataset_chunk)
                    added_count += 1
                
                # Update document count
                dataset.document_count += 1
            
            # Update chunk count
            dataset.chunk_count += added_count
            
            # Update metadata
            if dataset.metadata:
                metadata = dataset.metadata
                metadata["document_ids"] = [doc.id for doc in dataset.documents]
                metadata["document_names"] = [doc.filename for doc in dataset.documents]
                metadata["document_types"] = [doc.file_type for doc in dataset.documents]
                dataset.metadata = metadata
            
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to dataset: {str(e)}")
            self.db.rollback()
            return False
    
    async def remove_documents_from_dataset(
        self,
        dataset_id: str,
        document_ids: List[str],
    ) -> bool:
        """
        Remove documents from a dataset.
        
        Args:
            dataset_id: Dataset ID
            document_ids: List of document IDs to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get dataset
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                logger.warning(f"Dataset not found: {dataset_id}")
                return False
            
            # Remove documents from dataset
            removed_count = 0
            
            for doc_id in document_ids:
                # Get document
                document = self.db.query(Document).filter(Document.id == doc_id).first()
                
                if not document:
                    logger.warning(f"Document not found: {doc_id}")
                    continue
                
                # Check if document is in dataset
                if document not in dataset.documents:
                    logger.info(f"Document not in dataset: {doc_id}")
                    continue
                
                # Remove document from dataset
                dataset.documents.remove(document)
                
                # Get chunks for document
                chunks = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
                
                if not chunks:
                    logger.warning(f"No chunks found for document: {doc_id}")
                    continue
                
                # Remove chunks from dataset
                for chunk in chunks:
                    dataset_chunk = self.db.query(DatasetChunk).filter(
                        DatasetChunk.dataset_id == dataset.id,
                        DatasetChunk.chunk_id == chunk.id
                    ).first()
                    
                    if dataset_chunk:
                        self.db.delete(dataset_chunk)
                        removed_count += 1
                
                # Update document count
                dataset.document_count -= 1
            
            # Update chunk count
            dataset.chunk_count -= removed_count
            
            # Update metadata
            if dataset.metadata:
                metadata = dataset.metadata
                metadata["document_ids"] = [doc.id for doc in dataset.documents]
                metadata["document_names"] = [doc.filename for doc in dataset.documents]
                metadata["document_types"] = [doc.file_type for doc in dataset.documents]
                dataset.metadata = metadata
            
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing documents from dataset: {str(e)}")
            self.db.rollback()
            return False
    
    async def get_dataset_documents(self, dataset_id: str) -> List[Document]:
        """
        Get all documents in a dataset.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            List[Document]: List of documents
        """
        try:
            # Get dataset
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                logger.warning(f"Dataset not found: {dataset_id}")
                return []
            
            return dataset.documents
            
        except Exception as e:
            logger.error(f"Error getting dataset documents: {str(e)}")
            return []
    
    async def get_dataset_chunks(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks in a dataset.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            List[Dict[str, Any]]: List of chunks
        """
        try:
            # Get dataset
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                logger.warning(f"Dataset not found: {dataset_id}")
                return []
            
            # Get dataset chunks
            dataset_chunks = self.db.query(DatasetChunk).filter(DatasetChunk.dataset_id == dataset_id).all()
            
            if not dataset_chunks:
                logger.warning(f"No chunks found for dataset: {dataset_id}")
                return []
            
            # Get chunk IDs
            chunk_ids = [dc.chunk_id for dc in dataset_chunks]
            
            # Get chunks
            chunks = self.db.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
            
            # Get document IDs
            document_ids = list(set(chunk.document_id for chunk in chunks))
            
            # Get documents
            documents = self.db.query(Document).filter(Document.id.in_(document_ids)).all()
            
            # Create document lookup
            document_lookup = {doc.id: doc for doc in documents}
            
            # Convert to response format
            result = []
            
            for chunk in chunks:
                document = document_lookup.get(chunk.document_id)
                
                if not document:
                    logger.warning(f"Document not found for chunk: {chunk.id}")
                    continue
                
                result.append({
                    "id": chunk.id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "metadata": {
                        "page_numbers": chunk.page_numbers,
                        "source_document_id": chunk.document_id,
                        "source_document_name": document.filename,
                        "position": chunk.position,
                        "additional_metadata": chunk.metadata
                    },
                    "embedding_id": chunk.embedding_id,
                    "created_at": chunk.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting dataset chunks: {str(e)}")
            return []
