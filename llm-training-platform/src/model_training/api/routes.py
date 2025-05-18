"""
API routes for the Model Training service.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path, Body
from sqlalchemy.orm import Session
from loguru import logger

from src.common.db.database import get_db
from src.common.auth.auth_handler import get_current_user
from src.model_training.api.schemas import (
    ModelType, ModelStatus, TrainingType, TrainingStatus,
    TrainingConfigRequest, RAGConfigRequest,
    ModelResponse, ModelListResponse,
    TrainingJobResponse, TrainingJobListResponse,
    InferenceRequest, InferenceResponse,
    RAGInferenceRequest, RAGInferenceResponse,
    ErrorResponse
)
from src.model_training.registry.model_registry import ModelRegistry
from src.model_training.training.training_manager import TrainingManager
from src.model_training.rag.rag_service import RAGService


router = APIRouter(prefix="/api/v1/model-training", tags=["model-training"])


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    skip: int = Query(0, description="Number of models to skip"),
    limit: int = Query(100, description="Maximum number of models to return"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    model_type: Optional[ModelType] = Query(None, description="Filter by model type"),
    status: Optional[ModelStatus] = Query(None, description="Filter by model status"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List models with optional filtering.
    """
    try:
        registry = ModelRegistry(db)
        
        # For now, just get all models for the user
        # TODO: Implement filtering
        models = await registry.get_user_models(current_user["id"])
        
        # Convert to response models
        model_responses = [ModelResponse(**model.to_dict()) for model in models]
        
        return ModelListResponse(
            models=model_responses,
            count=len(model_responses)
        )
        
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing models: {str(e)}")


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str = Path(..., description="Model ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a model by ID.
    """
    try:
        registry = ModelRegistry(db)
        model = await registry.get_model(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
        
        # Check if user has access to the model
        if model.user_id != current_user["id"] and not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="You don't have access to this model")
        
        return ModelResponse(**model.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting model: {str(e)}")


@router.delete("/models/{model_id}", response_model=Dict[str, Any])
async def delete_model(
    model_id: str = Path(..., description="Model ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a model.
    """
    try:
        registry = ModelRegistry(db)
        model = await registry.get_model(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
        
        # Check if user has access to the model
        if model.user_id != current_user["id"] and not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="You don't have access to this model")
        
        # Delete model
        success = await registry.delete_model(model_id)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to delete model: {model_id}")
        
        return {"message": f"Model deleted: {model_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting model: {str(e)}")


@router.post("/models/fine-tune", response_model=ModelResponse)
async def create_fine_tuning_model(
    config: TrainingConfigRequest = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new fine-tuning model and start training.
    """
    try:
        registry = ModelRegistry(db)
        
        # Create model
        model = await registry.create_model(
            name=config.model_name,
            base_model=config.base_model,
            model_type=ModelType.FINE_TUNED,
            user_id=current_user["id"],
            description=config.description,
            tags=config.tags,
            metadata={
                "training_type": config.training_type,
                "dataset_id": config.dataset_id,
            }
        )
        
        # Create training job
        training_job = await registry.create_training_job(
            model_id=model.id,
            training_type=config.training_type,
            dataset_id=config.dataset_id,
            hyperparameters=config.hyperparameters,
        )
        
        if not training_job:
            raise HTTPException(status_code=500, detail="Failed to create training job")
        
        # Start training job in background
        training_manager = TrainingManager(db)
        background_tasks.add_task(training_manager.start_training_job, training_job.id)
        
        return ModelResponse(**model.to_dict())
        
    except Exception as e:
        logger.error(f"Error creating fine-tuning model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating fine-tuning model: {str(e)}")


@router.post("/models/rag", response_model=ModelResponse)
async def create_rag_model(
    config: RAGConfigRequest = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new RAG model.
    """
    try:
        rag_service = RAGService(db)
        
        # Create RAG model
        rag_model = await rag_service.create_rag_model(
            name=config.model_name,
            base_model=config.base_model,
            embedding_model=config.embedding_model,
            dataset_id=config.dataset_id,
            user_id=current_user["id"],
            description=config.description,
            tags=config.tags,
            retrieval_config=config.retrieval_config,
            generation_config=config.generation_config,
        )
        
        return ModelResponse(**rag_model)
        
    except Exception as e:
        logger.error(f"Error creating RAG model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating RAG model: {str(e)}")


@router.get("/training-jobs", response_model=TrainingJobListResponse)
async def list_training_jobs(
    skip: int = Query(0, description="Number of jobs to skip"),
    limit: int = Query(100, description="Maximum number of jobs to return"),
    model_id: Optional[str] = Query(None, description="Filter by model ID"),
    status: Optional[TrainingStatus] = Query(None, description="Filter by job status"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List training jobs with optional filtering.
    """
    try:
        registry = ModelRegistry(db)
        
        if model_id:
            # Get model to check access
            model = await registry.get_model(model_id)
            
            if not model:
                raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
            
            # Check if user has access to the model
            if model.user_id != current_user["id"] and not current_user.get("is_admin", False):
                raise HTTPException(status_code=403, detail="You don't have access to this model")
            
            # Get training jobs for the model
            jobs = await registry.get_model_training_jobs(model_id)
        else:
            # TODO: Implement getting all training jobs for the user
            # For now, return an empty list
            jobs = []
        
        # Convert to response models
        job_responses = [TrainingJobResponse(**job.to_dict()) for job in jobs]
        
        return TrainingJobListResponse(
            jobs=job_responses,
            count=len(job_responses)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing training jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing training jobs: {str(e)}")


@router.get("/training-jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job(
    job_id: str = Path(..., description="Training job ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a training job by ID.
    """
    try:
        registry = ModelRegistry(db)
        job = await registry.get_training_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Training job not found: {job_id}")
        
        # Get model to check access
        model = await registry.get_model(job.model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {job.model_id}")
        
        # Check if user has access to the model
        if model.user_id != current_user["id"] and not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="You don't have access to this training job")
        
        return TrainingJobResponse(**job.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting training job: {str(e)}")


@router.post("/training-jobs/{job_id}/cancel", response_model=Dict[str, Any])
async def cancel_training_job(
    job_id: str = Path(..., description="Training job ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel a training job.
    """
    try:
        from src.model_training.training.training_manager import stop_training_job
        
        registry = ModelRegistry(db)
        job = await registry.get_training_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Training job not found: {job_id}")
        
        # Get model to check access
        model = await registry.get_model(job.model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {job.model_id}")
        
        # Check if user has access to the model
        if model.user_id != current_user["id"] and not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="You don't have access to this training job")
        
        # Check if job is running
        if job.status not in [TrainingStatus.PENDING, TrainingStatus.PREPARING, TrainingStatus.RUNNING]:
            raise HTTPException(status_code=400, detail=f"Training job is not running: {job_id}")
        
        # Cancel job
        await stop_training_job(job_id)
        
        return {"message": f"Training job cancelled: {job_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling training job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cancelling training job: {str(e)}")


@router.post("/inference", response_model=InferenceResponse)
async def run_inference(
    request: InferenceRequest = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run inference with a model.
    """
    try:
        registry = ModelRegistry(db)
        model = await registry.get_model(request.model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {request.model_id}")
        
        # Check if user has access to the model
        if model.user_id != current_user["id"] and not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="You don't have access to this model")
        
        # Check if model is ready
        if model.status != ModelStatus.READY:
            raise HTTPException(status_code=400, detail=f"Model is not ready: {request.model_id}")
        
        # TODO: Implement actual inference
        # For now, return a placeholder response
        
        # Use provided generation config or default
        generation_config = request.generation_config or {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 50,
            "max_tokens": 1024
        }
        
        return InferenceResponse(
            model_id=request.model_id,
            generated_text=f"This is a simulated response for the prompt: {request.prompt[:100]}...",
            prompt=request.prompt,
            generation_config=generation_config,
            metadata={
                "generation_time_ms": 1234,
                "token_count": 156
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running inference: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running inference: {str(e)}")


@router.post("/rag/inference", response_model=RAGInferenceResponse)
async def run_rag_inference(
    request: RAGInferenceRequest = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run RAG inference with a model.
    """
    try:
        registry = ModelRegistry(db)
        model = await registry.get_model(request.model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {request.model_id}")
        
        # Check if user has access to the model
        if model.user_id != current_user["id"] and not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="You don't have access to this model")
        
        # Check if model is a RAG model
        if model.model_type != ModelType.RAG:
            raise HTTPException(status_code=400, detail=f"Model is not a RAG model: {request.model_id}")
        
        # Check if model is ready
        if model.status != ModelStatus.READY:
            raise HTTPException(status_code=400, detail=f"Model is not ready: {request.model_id}")
        
        # Run RAG inference
        rag_service = RAGService(db)
        answer, contexts = await rag_service.query(
            model_id=request.model_id,
            query=request.query,
            retrieval_config=request.retrieval_config,
            generation_config=request.generation_config,
        )
        
        # Get RAG model config
        rag_model = await rag_service.get_rag_model(request.model_id)
        
        # Use provided configs or defaults from the model
        retrieval_config = request.retrieval_config or rag_model["rag_config"]["retrieval_config"]
        generation_config = request.generation_config or rag_model["rag_config"]["generation_config"]
        
        return RAGInferenceResponse(
            model_id=request.model_id,
            query=request.query,
            answer=answer,
            contexts=contexts,
            retrieval_config=retrieval_config,
            generation_config=generation_config,
            metadata={
                "retrieval_time_ms": 123,
                "generation_time_ms": 456,
                "total_time_ms": 579
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running RAG inference: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running RAG inference: {str(e)}")
