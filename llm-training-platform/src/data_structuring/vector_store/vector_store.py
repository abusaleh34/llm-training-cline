"""
Vector store module for the LLM Training Platform.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, Union
import numpy as np
from loguru import logger

from pymilvus import (
    connections,
    utility,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
)

from src.common.config.settings import settings


# Global connection state
_is_connected = False


async def init_vector_store():
    """Initialize connection to the vector store."""
    global _is_connected
    
    if _is_connected:
        logger.info("Vector store already initialized.")
        return
    
    try:
        # Connect to Milvus
        connections.connect(
            alias="default",
            host=settings.vector_db.host,
            port=settings.vector_db.port,
            user=settings.vector_db.user,
            password=settings.vector_db.password,
        )
        
        logger.info(f"Connected to Milvus at {settings.vector_db.host}:{settings.vector_db.port}")
        
        # Create collections if they don't exist
        await create_collections()
        
        _is_connected = True
        logger.info("Vector store initialized successfully.")
        
    except Exception as e:
        logger.error(f"Error initializing vector store: {str(e)}")
        raise


async def create_collections():
    """Create collections in the vector store if they don't exist."""
    try:
        # Create document chunks collection
        if not utility.has_collection("document_chunks"):
            logger.info("Creating document_chunks collection...")
            
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
                FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.vector_db.embedding_dim),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]
            
            schema = CollectionSchema(fields=fields, description="Document chunks embeddings")
            collection = Collection(name="document_chunks", schema=schema)
            
            # Create index
            index_params = {
                "metric_type": "COSINE",
                "index_type": "HNSW",
                "params": {"M": 8, "efConstruction": 64},
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            logger.info("Created document_chunks collection and index.")
        
    except Exception as e:
        logger.error(f"Error creating collections: {str(e)}")
        raise


async def store_embeddings(
    embeddings: List[np.ndarray],
    chunk_ids: List[str],
    document_ids: List[str],
    metadata_list: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """
    Store embeddings in the vector store.
    
    Args:
        embeddings: List of embeddings as numpy arrays
        chunk_ids: List of chunk IDs
        document_ids: List of document IDs
        metadata_list: List of metadata dictionaries
        
    Returns:
        List[str]: List of embedding IDs in the vector store
    """
    try:
        if not _is_connected:
            await init_vector_store()
        
        # Prepare data
        data = []
        ids = []
        
        for i, (embedding, chunk_id, document_id) in enumerate(zip(embeddings, chunk_ids, document_ids)):
            # Generate ID for the embedding
            embedding_id = f"{chunk_id}"
            ids.append(embedding_id)
            
            # Prepare metadata
            metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else {}
            
            # Add data
            data.append({
                "id": embedding_id,
                "document_id": document_id,
                "chunk_id": chunk_id,
                "embedding": embedding.tolist(),
                "metadata": metadata,
            })
        
        # Get collection
        collection = Collection("document_chunks")
        
        # Insert data
        collection.insert(data)
        
        # Flush to ensure data is persisted
        collection.flush()
        
        logger.info(f"Stored {len(embeddings)} embeddings in the vector store.")
        
        return ids
        
    except Exception as e:
        logger.error(f"Error storing embeddings: {str(e)}")
        raise


async def search_similar(
    query_embedding: np.ndarray,
    limit: int = 10,
    filter_expr: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search for similar embeddings in the vector store.
    
    Args:
        query_embedding: Query embedding as numpy array
        limit: Maximum number of results to return
        filter_expr: Filter expression for the search
        
    Returns:
        List[Dict[str, Any]]: List of search results
    """
    try:
        if not _is_connected:
            await init_vector_store()
        
        # Get collection
        collection = Collection("document_chunks")
        collection.load()
        
        # Prepare search parameters
        search_params = {
            "metric_type": "COSINE",
            "params": {"ef": 64},
        }
        
        # Execute search
        results = collection.search(
            data=[query_embedding.tolist()],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            expr=filter_expr,
            output_fields=["document_id", "chunk_id", "metadata"],
        )
        
        # Format results
        formatted_results = []
        
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "id": hit.id,
                    "document_id": hit.entity.get("document_id"),
                    "chunk_id": hit.entity.get("chunk_id"),
                    "metadata": hit.entity.get("metadata"),
                    "score": hit.score,
                })
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error searching similar embeddings: {str(e)}")
        raise


async def delete_embeddings(chunk_ids: List[str]) -> bool:
    """
    Delete embeddings from the vector store.
    
    Args:
        chunk_ids: List of chunk IDs to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not _is_connected:
            await init_vector_store()
        
        # Get collection
        collection = Collection("document_chunks")
        
        # Prepare expression
        expr = f"chunk_id in {chunk_ids}"
        
        # Delete data
        collection.delete(expr)
        
        logger.info(f"Deleted embeddings for {len(chunk_ids)} chunks from the vector store.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error deleting embeddings: {str(e)}")
        return False


async def delete_document_embeddings(document_id: str) -> bool:
    """
    Delete all embeddings for a document from the vector store.
    
    Args:
        document_id: Document ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not _is_connected:
            await init_vector_store()
        
        # Get collection
        collection = Collection("document_chunks")
        
        # Prepare expression
        expr = f'document_id == "{document_id}"'
        
        # Delete data
        collection.delete(expr)
        
        logger.info(f"Deleted all embeddings for document {document_id} from the vector store.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error deleting document embeddings: {str(e)}")
        return False


async def close_connection():
    """Close connection to the vector store."""
    global _is_connected
    
    if _is_connected:
        try:
            connections.disconnect("default")
            _is_connected = False
            logger.info("Disconnected from vector store.")
        except Exception as e:
            logger.error(f"Error disconnecting from vector store: {str(e)}")
