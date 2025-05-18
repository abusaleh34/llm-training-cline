"""
RAG (Retrieval-Augmented Generation) service for the Model Training module.
"""

import os
from typing import List, Dict, Any, Optional, Union, Tuple
from loguru import logger

from src.common.db.database import get_db
from src.common.config.settings import settings
from src.model_training.models.model import Model, RAGModel
from src.model_training.api.schemas import ModelType, ModelStatus, RetrievedContext
from src.model_training.registry.model_registry import ModelRegistry
from src.data_structuring.vector_store.vector_store import VectorStore
from src.data_structuring.service.dataset_service import DatasetService


class RAGService:
    """Service for RAG operations."""
    
    def __init__(self, db):
        """
        Initialize the RAG service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.registry = ModelRegistry(db)
        self.vector_store = VectorStore(db)
        self.dataset_service = DatasetService(db)
    
    async def create_rag_model(
        self,
        name: str,
        base_model: str,
        embedding_model: str,
        dataset_id: str,
        user_id: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        retrieval_config: Optional[Dict[str, Any]] = None,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new RAG model.
        
        Args:
            name: Model name
            base_model: Base model name
            embedding_model: Embedding model name
            dataset_id: Dataset ID
            user_id: User ID
            description: Model description
            tags: Model tags
            retrieval_config: Retrieval configuration
            generation_config: Generation configuration
            
        Returns:
            Dict[str, Any]: Created RAG model
        """
        # Validate dataset exists
        dataset = await self.dataset_service.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")
        
        # Create RAG model
        rag_model = await self.registry.create_rag_model(
            name=name,
            base_model=base_model,
            embedding_model=embedding_model,
            dataset_id=dataset_id,
            user_id=user_id,
            description=description,
            tags=tags,
            retrieval_config=retrieval_config,
            generation_config=generation_config,
        )
        
        return rag_model
    
    async def get_rag_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a RAG model by ID.
        
        Args:
            model_id: Model ID
            
        Returns:
            Optional[Dict[str, Any]]: RAG model if found, None otherwise
        """
        return await self.registry.get_rag_model(model_id)
    
    async def retrieve(
        self,
        model_id: str,
        query: str,
        retrieval_config: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedContext]:
        """
        Retrieve relevant contexts for a query using a RAG model.
        
        Args:
            model_id: RAG model ID
            query: User query
            retrieval_config: Retrieval configuration (overrides model defaults)
            
        Returns:
            List[RetrievedContext]: Retrieved contexts
        """
        # Get RAG model
        rag_model_data = await self.get_rag_model(model_id)
        
        if not rag_model_data:
            raise ValueError(f"RAG model not found: {model_id}")
        
        # Get dataset ID
        dataset_id = rag_model_data["rag_config"]["dataset_id"]
        
        # Get embedding model
        embedding_model = rag_model_data["rag_config"]["embedding_model"]
        
        # Merge retrieval configurations
        model_retrieval_config = rag_model_data["rag_config"]["retrieval_config"]
        effective_retrieval_config = {**model_retrieval_config, **(retrieval_config or {})}
        
        # Get top_k and similarity threshold
        top_k = effective_retrieval_config.get("top_k", 5)
        similarity_threshold = effective_retrieval_config.get("similarity_threshold", 0.7)
        
        # Retrieve similar chunks
        similar_chunks = await self.vector_store.search(
            query=query,
            dataset_id=dataset_id,
            embedding_model=embedding_model,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )
        
        # Convert to RetrievedContext objects
        contexts = []
        for chunk in similar_chunks:
            # Get document details
            document = await self.dataset_service.get_document(chunk["document_id"])
            
            context = RetrievedContext(
                text=chunk["text"],
                document_id=chunk["document_id"],
                document_name=document["name"] if document else "Unknown",
                chunk_id=chunk["id"],
                score=chunk["score"],
                page_numbers=chunk.get("metadata", {}).get("page_numbers"),
            )
            
            contexts.append(context)
        
        return contexts
    
    async def generate(
        self,
        model_id: str,
        query: str,
        contexts: List[RetrievedContext],
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a response for a query using a RAG model and retrieved contexts.
        
        Args:
            model_id: RAG model ID
            query: User query
            contexts: Retrieved contexts
            generation_config: Generation configuration (overrides model defaults)
            
        Returns:
            str: Generated response
        """
        # Get RAG model
        rag_model_data = await self.get_rag_model(model_id)
        
        if not rag_model_data:
            raise ValueError(f"RAG model not found: {model_id}")
        
        # Get base model
        base_model = rag_model_data["base_model"]
        
        # Merge generation configurations
        model_generation_config = rag_model_data["rag_config"]["generation_config"]
        effective_generation_config = {**model_generation_config, **(generation_config or {})}
        
        # Prepare prompt with contexts
        prompt = self._prepare_rag_prompt(query, contexts)
        
        # TODO: Implement actual generation with the base model
        # For now, we'll return a placeholder response
        response = f"This is a simulated RAG response for the query: {query}\n\n"
        response += "Based on the retrieved contexts:\n"
        
        for i, context in enumerate(contexts):
            response += f"- Context {i+1} (score: {context.score:.2f}): {context.text[:100]}...\n"
        
        return response
    
    async def query(
        self,
        model_id: str,
        query: str,
        retrieval_config: Optional[Dict[str, Any]] = None,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, List[RetrievedContext]]:
        """
        Perform a complete RAG query (retrieve + generate).
        
        Args:
            model_id: RAG model ID
            query: User query
            retrieval_config: Retrieval configuration (overrides model defaults)
            generation_config: Generation configuration (overrides model defaults)
            
        Returns:
            Tuple[str, List[RetrievedContext]]: Generated response and retrieved contexts
        """
        # Retrieve contexts
        contexts = await self.retrieve(model_id, query, retrieval_config)
        
        # Generate response
        response = await self.generate(model_id, query, contexts, generation_config)
        
        return response, contexts
    
    def _prepare_rag_prompt(self, query: str, contexts: List[RetrievedContext]) -> str:
        """
        Prepare a prompt for RAG generation.
        
        Args:
            query: User query
            contexts: Retrieved contexts
            
        Returns:
            str: Prepared prompt
        """
        prompt = "You are an AI assistant that answers questions based on the provided context.\n\n"
        prompt += "Context information:\n"
        
        for i, context in enumerate(contexts):
            prompt += f"[{i+1}] {context.text}\n\n"
        
        prompt += f"Question: {query}\n\n"
        prompt += "Answer the question based on the context provided. If the answer cannot be determined from the context, say so."
        
        return prompt
