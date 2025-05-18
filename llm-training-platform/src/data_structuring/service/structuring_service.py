"""
Structuring service for the LLM Training Platform.
"""

import os
import uuid
from typing import List, Dict, Any, Optional, Union
from loguru import logger
from sqlalchemy.orm import Session

from src.common.models.document import Document, DocumentStatus
from src.data_structuring.models.chunk import DocumentChunk
from src.data_structuring.chunking.chunking_service import ChunkingService, ArabicChunkingService
from src.data_structuring.embedding.embedding_service import EmbeddingService, ArabicEmbeddingService
from src.data_structuring.vector_store.vector_store import store_embeddings, delete_document_embeddings
from src.data_structuring.api.schemas import ChunkStrategy


class StructuringService:
    """Service for structuring document data."""
    
    def __init__(self, db: Session):
        """
        Initialize the structuring service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.chunking_service = ChunkingService()
        self.arabic_chunking_service = ArabicChunkingService()
        self.embedding_service = EmbeddingService()
        self.arabic_embedding_service = ArabicEmbeddingService()
    
    async def chunk_document(
        self,
        document_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunk_strategy: ChunkStrategy = ChunkStrategy.FIXED_SIZE,
    ) -> Dict[str, Any]:
        """
        Chunk a document into smaller pieces.
        
        Args:
            document_id: Document ID
            chunk_size: Size of each chunk in tokens/characters
            chunk_overlap: Overlap between chunks in tokens/characters
            chunk_strategy: Chunking strategy
            
        Returns:
            Dict[str, Any]: Result of the chunking operation
        """
        try:
            # Get document
            document = self.db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return {
                    "success": False,
                    "message": f"Document not found: {document_id}",
                    "error": "Document not found"
                }
            
            # Check if document is processed
            if document.status != DocumentStatus.PROCESSED:
                return {
                    "success": False,
                    "message": f"Document must be processed before chunking: {document_id}",
                    "error": "Document not processed"
                }
            
            # Get document text
            document_text = document.content
            
            if not document_text:
                return {
                    "success": False,
                    "message": f"Document has no content: {document_id}",
                    "error": "Document has no content"
                }
            
            # Delete existing chunks
            existing_chunks = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
            
            if existing_chunks:
                logger.info(f"Deleting {len(existing_chunks)} existing chunks for document {document_id}")
                
                # Delete from vector store
                chunk_ids = [chunk.id for chunk in existing_chunks]
                await delete_document_embeddings(document_id)
                
                # Delete from database
                for chunk in existing_chunks:
                    self.db.delete(chunk)
                
                self.db.commit()
            
            # Select chunking service based on document language
            is_arabic = document.language and document.language.lower() in ["ar", "ara", "arabic"]
            chunking_service = self.arabic_chunking_service if is_arabic else self.chunking_service
            
            # Chunk document
            chunks = chunking_service.chunk_text(
                text=document_text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                strategy=chunk_strategy
            )
            
            if not chunks:
                return {
                    "success": False,
                    "message": f"Failed to chunk document: {document_id}",
                    "error": "No chunks generated"
                }
            
            # Create chunks in database
            db_chunks = []
            
            for i, chunk_text in enumerate(chunks):
                # Create chunk
                chunk = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    text=chunk_text,
                    position=i,
                    page_numbers=document.page_map.get(i, []) if document.page_map else None,
                    metadata={
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap,
                        "chunk_strategy": chunk_strategy.value,
                        "language": document.language,
                        "position": i,
                        "total_chunks": len(chunks)
                    }
                )
                
                self.db.add(chunk)
                db_chunks.append(chunk)
            
            self.db.commit()
            
            # Generate embeddings
            embedding_service = self.arabic_embedding_service if is_arabic else self.embedding_service
            
            chunk_texts = [chunk.text for chunk in db_chunks]
            embeddings = embedding_service.generate_embeddings(chunk_texts)
            
            # Store embeddings in vector store
            chunk_ids = [chunk.id for chunk in db_chunks]
            document_ids = [document_id] * len(db_chunks)
            metadata_list = [
                {
                    "document_id": document_id,
                    "chunk_id": chunk.id,
                    "position": chunk.position,
                    "language": document.language,
                    "document_name": document.filename,
                    "document_type": document.file_type,
                    "page_numbers": chunk.page_numbers
                }
                for chunk in db_chunks
            ]
            
            embedding_ids = await store_embeddings(
                embeddings=embeddings,
                chunk_ids=chunk_ids,
                document_ids=document_ids,
                metadata_list=metadata_list
            )
            
            # Update chunks with embedding IDs
            for i, chunk in enumerate(db_chunks):
                chunk.embedding_id = embedding_ids[i]
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Document chunked successfully: {document_id}",
                "chunk_count": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error chunking document: {str(e)}")
            self.db.rollback()
            
            return {
                "success": False,
                "message": f"Error chunking document: {document_id}",
                "error": str(e)
            }
    
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List[Dict[str, Any]]: List of document chunks
        """
        try:
            # Get document
            document = self.db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                logger.error(f"Document not found: {document_id}")
                return []
            
            # Get chunks
            chunks = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.position).all()
            
            # Convert to response format
            result = []
            
            for chunk in chunks:
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
            logger.error(f"Error getting document chunks: {str(e)}")
            return []
