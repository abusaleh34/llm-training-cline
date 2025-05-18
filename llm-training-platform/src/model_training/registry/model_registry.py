"""
Model registry for the Model Training service.
"""

import uuid
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from loguru import logger

from src.model_training.models.model import Model, TrainingJob, RAGModel
from src.model_training.api.schemas import ModelType, ModelStatus, TrainingType, TrainingStatus


class ModelRegistry:
    """Registry for models and training jobs."""
    
    def __init__(self, db: Session):
        """
        Initialize the model registry.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_model(
        self,
        name: str,
        base_model: str,
        model_type: ModelType,
        user_id: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Model:
        """
        Create a new model.
        
        Args:
            name: Model name
            base_model: Base model name
            model_type: Model type
            user_id: User ID
            description: Model description
            tags: Model tags
            metadata: Model metadata
            
        Returns:
            Model: Created model
        """
        model = Model(
            name=name,
            base_model=base_model,
            model_type=model_type,
            user_id=user_id,
            description=description,
            tags=tags,
            metadata=metadata,
            status=ModelStatus.CREATED,
        )
        
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        
        logger.info(f"Created model: {model.id}")
        
        return model
    
    async def get_model(self, model_id: str) -> Optional[Model]:
        """
        Get a model by ID.
        
        Args:
            model_id: Model ID
            
        Returns:
            Optional[Model]: Model if found, None otherwise
        """
        return await self.db.query(Model).filter(Model.id == model_id).first()
    
    async def get_user_models(
        self,
        user_id: str,
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None,
        tag: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """
        Get models for a user.
        
        Args:
            user_id: User ID
            model_type: Filter by model type
            status: Filter by model status
            tag: Filter by tag
            skip: Number of models to skip
            limit: Maximum number of models to return
            
        Returns:
            List[Model]: List of models
        """
        query = self.db.query(Model).filter(Model.user_id == user_id)
        
        if model_type:
            query = query.filter(Model.model_type == model_type)
        
        if status:
            query = query.filter(Model.status == status)
        
        if tag:
            query = query.filter(Model.tags.contains([tag]))
        
        return await query.order_by(desc(Model.created_at)).offset(skip).limit(limit).all()
    
    async def update_model(
        self,
        model_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[ModelStatus] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Model]:
        """
        Update a model.
        
        Args:
            model_id: Model ID
            name: New name
            description: New description
            tags: New tags
            status: New status
            metadata: New metadata
            
        Returns:
            Optional[Model]: Updated model if found, None otherwise
        """
        model = await self.get_model(model_id)
        
        if not model:
            return None
        
        if name is not None:
            model.name = name
        
        if description is not None:
            model.description = description
        
        if tags is not None:
            model.tags = tags
        
        if status is not None:
            model.status = status
        
        if metadata is not None:
            model.metadata = metadata
        
        model.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(model)
        
        logger.info(f"Updated model: {model.id}")
        
        return model
    
    async def delete_model(self, model_id: str) -> bool:
        """
        Delete a model.
        
        Args:
            model_id: Model ID
            
        Returns:
            bool: True if deleted, False otherwise
        """
        model = await self.get_model(model_id)
        
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.commit()
        
        logger.info(f"Deleted model: {model_id}")
        
        return True
    
    async def create_training_job(
        self,
        model_id: str,
        training_type: TrainingType,
        dataset_id: str,
        hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[TrainingJob]:
        """
        Create a new training job.
        
        Args:
            model_id: Model ID
            training_type: Training type
            dataset_id: Dataset ID
            hyperparameters: Training hyperparameters
            
        Returns:
            Optional[TrainingJob]: Created training job if model found, None otherwise
        """
        model = await self.get_model(model_id)
        
        if not model:
            return None
        
        # Update model status
        model.status = ModelStatus.TRAINING
        
        # Create training job
        job = TrainingJob(
            model_id=model_id,
            training_type=training_type,
            dataset_id=dataset_id,
            hyperparameters=hyperparameters,
            status=TrainingStatus.PENDING,
            progress=0.0,
        )
        
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        
        logger.info(f"Created training job: {job.id} for model: {model_id}")
        
        return job
    
    async def get_training_job(self, job_id: str) -> Optional[TrainingJob]:
        """
        Get a training job by ID.
        
        Args:
            job_id: Training job ID
            
        Returns:
            Optional[TrainingJob]: Training job if found, None otherwise
        """
        return await self.db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    
    async def get_model_training_jobs(
        self,
        model_id: str,
        status: Optional[TrainingStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TrainingJob]:
        """
        Get training jobs for a model.
        
        Args:
            model_id: Model ID
            status: Filter by job status
            skip: Number of jobs to skip
            limit: Maximum number of jobs to return
            
        Returns:
            List[TrainingJob]: List of training jobs
        """
        query = self.db.query(TrainingJob).filter(TrainingJob.model_id == model_id)
        
        if status:
            query = query.filter(TrainingJob.status == status)
        
        return await query.order_by(desc(TrainingJob.created_at)).offset(skip).limit(limit).all()
    
    async def update_training_job(
        self,
        job_id: str,
        status: Optional[TrainingStatus] = None,
        progress: Optional[float] = None,
        metrics: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> Optional[TrainingJob]:
        """
        Update a training job.
        
        Args:
            job_id: Training job ID
            status: New status
            progress: New progress
            metrics: New metrics
            error_message: Error message if failed
            
        Returns:
            Optional[TrainingJob]: Updated training job if found, None otherwise
        """
        job = await self.get_training_job(job_id)
        
        if not job:
            return None
        
        if status is not None:
            job.status = status
            
            # Update model status if job is completed or failed
            if status == TrainingStatus.COMPLETED:
                model = await self.get_model(job.model_id)
                if model:
                    model.status = ModelStatus.READY
                    model.updated_at = datetime.utcnow()
            elif status == TrainingStatus.FAILED:
                model = await self.get_model(job.model_id)
                if model:
                    model.status = ModelStatus.FAILED
                    model.updated_at = datetime.utcnow()
        
        if progress is not None:
            job.progress = progress
        
        if metrics is not None:
            job.metrics = metrics
        
        if error_message is not None:
            job.error_message = error_message
        
        job.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(job)
        
        logger.info(f"Updated training job: {job.id}")
        
        return job
    
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
        # Create base model
        model = await self.create_model(
            name=name,
            base_model=base_model,
            model_type=ModelType.RAG,
            user_id=user_id,
            description=description,
            tags=tags,
            metadata={
                "dataset_id": dataset_id,
                "embedding_model": embedding_model,
            },
        )
        
        # Set default configurations if not provided
        if retrieval_config is None:
            retrieval_config = {
                "top_k": 5,
                "similarity_threshold": 0.7,
                "reranking_enabled": False,
            }
        
        if generation_config is None:
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 50,
                "max_tokens": 1024,
            }
        
        # Create RAG model
        rag_model = RAGModel(
            id=model.id,
            embedding_model=embedding_model,
            dataset_id=dataset_id,
            retrieval_config=retrieval_config,
            generation_config=generation_config,
        )
        
        self.db.add(rag_model)
        await self.db.commit()
        await self.db.refresh(rag_model)
        
        logger.info(f"Created RAG model: {rag_model.id}")
        
        # Update model status to ready
        await self.update_model(model.id, status=ModelStatus.READY)
        
        # Combine model and RAG model data
        result = model.to_dict()
        result["rag_config"] = rag_model.to_dict()
        
        return result
    
    async def get_rag_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a RAG model by ID.
        
        Args:
            model_id: Model ID
            
        Returns:
            Optional[Dict[str, Any]]: RAG model if found, None otherwise
        """
        model = await self.get_model(model_id)
        
        if not model or model.model_type != ModelType.RAG:
            return None
        
        rag_model = await self.db.query(RAGModel).filter(RAGModel.id == model_id).first()
        
        if not rag_model:
            return None
        
        # Combine model and RAG model data
        result = model.to_dict()
        result["rag_config"] = rag_model.to_dict()
        
        return result
    
    async def update_rag_model(
        self,
        model_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        retrieval_config: Optional[Dict[str, Any]] = None,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update a RAG model.
        
        Args:
            model_id: Model ID
            name: New name
            description: New description
            tags: New tags
            retrieval_config: New retrieval configuration
            generation_config: New generation configuration
            
        Returns:
            Optional[Dict[str, Any]]: Updated RAG model if found, None otherwise
        """
        model = await self.get_model(model_id)
        
        if not model or model.model_type != ModelType.RAG:
            return None
        
        rag_model = await self.db.query(RAGModel).filter(RAGModel.id == model_id).first()
        
        if not rag_model:
            return None
        
        # Update base model
        if name is not None or description is not None or tags is not None:
            await self.update_model(
                model_id=model_id,
                name=name,
                description=description,
                tags=tags,
            )
            model = await self.get_model(model_id)
        
        # Update RAG model
        if retrieval_config is not None:
            rag_model.retrieval_config = retrieval_config
        
        if generation_config is not None:
            rag_model.generation_config = generation_config
        
        rag_model.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(rag_model)
        
        logger.info(f"Updated RAG model: {rag_model.id}")
        
        # Combine model and RAG model data
        result = model.to_dict()
        result["rag_config"] = rag_model.to_dict()
        
        return result
