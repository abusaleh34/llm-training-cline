"""
Training manager for the Model Training service.
"""

import os
import asyncio
import threading
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid
from loguru import logger

from src.common.db.database import get_db
from src.common.config.settings import settings
from src.model_training.models.model import Model, TrainingJob
from src.model_training.api.schemas import ModelType, ModelStatus, TrainingType, TrainingStatus
from src.model_training.registry.model_registry import ModelRegistry


# Dictionary to store active training jobs
active_jobs = {}


async def stop_all_training_jobs():
    """Stop all active training jobs."""
    for job_id in list(active_jobs.keys()):
        await stop_training_job(job_id)
    
    logger.info("All training jobs stopped.")


async def stop_training_job(job_id: str):
    """
    Stop a training job.
    
    Args:
        job_id: Training job ID
    """
    if job_id in active_jobs:
        # Get job
        job_thread, stop_event = active_jobs[job_id]
        
        # Set stop event
        stop_event.set()
        
        # Wait for thread to finish
        if job_thread.is_alive():
            job_thread.join(timeout=30)
        
        # Remove from active jobs
        del active_jobs[job_id]
        
        logger.info(f"Training job stopped: {job_id}")
        
        # Update job status
        db = next(get_db())
        registry = ModelRegistry(db)
        await registry.update_training_job(
            job_id=job_id,
            status=TrainingStatus.CANCELLED,
            error_message="Training job cancelled by user."
        )


class TrainingManager:
    """Manager for training jobs."""
    
    def __init__(self, db):
        """
        Initialize the training manager.
        
        Args:
            db: Database session
        """
        self.db = db
        self.registry = ModelRegistry(db)
    
    async def start_training_job(self, job_id: str) -> bool:
        """
        Start a training job.
        
        Args:
            job_id: Training job ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get training job
            job = await self.registry.get_training_job(job_id)
            
            if not job:
                logger.warning(f"Training job not found: {job_id}")
                return False
            
            # Check if job is already running
            if job.status == TrainingStatus.RUNNING:
                logger.warning(f"Training job already running: {job_id}")
                return False
            
            # Get model
            model = await self.registry.get_model(job.model_id)
            
            if not model:
                logger.warning(f"Model not found: {job.model_id}")
                return False
            
            # Update job status
            await self.registry.update_training_job(
                job_id=job_id,
                status=TrainingStatus.PREPARING,
                progress=0.0
            )
            
            # Create stop event
            stop_event = threading.Event()
            
            # Create and start training thread
            if job.training_type == TrainingType.LORA:
                training_thread = threading.Thread(
                    target=self._run_lora_training,
                    args=(job_id, model.id, job.dataset_id, job.hyperparameters, stop_event)
                )
            elif job.training_type == TrainingType.QLORA:
                training_thread = threading.Thread(
                    target=self._run_qlora_training,
                    args=(job_id, model.id, job.dataset_id, job.hyperparameters, stop_event)
                )
            elif job.training_type == TrainingType.PEFT:
                training_thread = threading.Thread(
                    target=self._run_peft_training,
                    args=(job_id, model.id, job.dataset_id, job.hyperparameters, stop_event)
                )
            elif job.training_type == TrainingType.FULL_FINE_TUNING:
                training_thread = threading.Thread(
                    target=self._run_full_fine_tuning,
                    args=(job_id, model.id, job.dataset_id, job.hyperparameters, stop_event)
                )
            else:
                logger.error(f"Unsupported training type: {job.training_type}")
                await self.registry.update_training_job(
                    job_id=job_id,
                    status=TrainingStatus.FAILED,
                    error_message=f"Unsupported training type: {job.training_type}"
                )
                return False
            
            # Start thread
            training_thread.start()
            
            # Add to active jobs
            active_jobs[job_id] = (training_thread, stop_event)
            
            logger.info(f"Training job started: {job_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting training job: {str(e)}")
            
            # Update job status
            await self.registry.update_training_job(
                job_id=job_id,
                status=TrainingStatus.FAILED,
                error_message=f"Error starting training job: {str(e)}"
            )
            
            return False
    
    def _run_lora_training(self, job_id: str, model_id: str, dataset_id: str, hyperparameters: Dict[str, Any], stop_event: threading.Event):
        """
        Run LoRA training in a separate thread.
        
        Args:
            job_id: Training job ID
            model_id: Model ID
            dataset_id: Dataset ID
            hyperparameters: Training hyperparameters
            stop_event: Event to signal training should stop
        """
        try:
            # Get database session for this thread
            db = next(get_db())
            registry = ModelRegistry(db)
            
            # Update job status
            asyncio.run(registry.update_training_job(
                job_id=job_id,
                status=TrainingStatus.RUNNING,
                progress=0.0
            ))
            
            # Get model
            model = asyncio.run(registry.get_model(model_id))
            
            if not model:
                logger.error(f"Model not found: {model_id}")
                asyncio.run(registry.update_training_job(
                    job_id=job_id,
                    status=TrainingStatus.FAILED,
                    error_message=f"Model not found: {model_id}"
                ))
                return
            
            # Simulate training progress
            total_steps = 100
            for step in range(total_steps + 1):
                if stop_event.is_set():
                    logger.info(f"Training job stopped: {job_id}")
                    return
                
                # Update progress
                progress = step / total_steps * 100
                metrics = {
                    "loss": 1.0 - (progress / 100) * 0.9,
                    "learning_rate": hyperparameters.get("learning_rate", 5e-5),
                    "step": step,
                    "total_steps": total_steps
                }
                
                asyncio.run(registry.update_training_job(
                    job_id=job_id,
                    progress=progress,
                    metrics=metrics
                ))
                
                # Simulate training step
                time.sleep(0.1)
            
            # Update job status
            asyncio.run(registry.update_training_job(
                job_id=job_id,
                status=TrainingStatus.COMPLETED,
                progress=100.0
            ))
            
            # Remove from active jobs
            if job_id in active_jobs:
                del active_jobs[job_id]
            
            logger.info(f"Training job completed: {job_id}")
            
        except Exception as e:
            logger.error(f"Error in training job: {str(e)}")
            
            # Update job status
            try:
                asyncio.run(registry.update_training_job(
                    job_id=job_id,
                    status=TrainingStatus.FAILED,
                    error_message=f"Error in training job: {str(e)}"
                ))
            except Exception as update_error:
                logger.error(f"Error updating training job status: {str(update_error)}")
            
            # Remove from active jobs
            if job_id in active_jobs:
                del active_jobs[job_id]
    
    def _run_qlora_training(self, job_id: str, model_id: str, dataset_id: str, hyperparameters: Dict[str, Any], stop_event: threading.Event):
        """
        Run QLoRA training in a separate thread.
        
        Args:
            job_id: Training job ID
            model_id: Model ID
            dataset_id: Dataset ID
            hyperparameters: Training hyperparameters
            stop_event: Event to signal training should stop
        """
        # Similar to LoRA training but with QLoRA-specific logic
        # For now, we'll just call the LoRA training method as a placeholder
        self._run_lora_training(job_id, model_id, dataset_id, hyperparameters, stop_event)
    
    def _run_peft_training(self, job_id: str, model_id: str, dataset_id: str, hyperparameters: Dict[str, Any], stop_event: threading.Event):
        """
        Run PEFT training in a separate thread.
        
        Args:
            job_id: Training job ID
            model_id: Model ID
            dataset_id: Dataset ID
            hyperparameters: Training hyperparameters
            stop_event: Event to signal training should stop
        """
        # Similar to LoRA training but with PEFT-specific logic
        # For now, we'll just call the LoRA training method as a placeholder
        self._run_lora_training(job_id, model_id, dataset_id, hyperparameters, stop_event)
    
    def _run_full_fine_tuning(self, job_id: str, model_id: str, dataset_id: str, hyperparameters: Dict[str, Any], stop_event: threading.Event):
        """
        Run full fine-tuning in a separate thread.
        
        Args:
            job_id: Training job ID
            model_id: Model ID
            dataset_id: Dataset ID
            hyperparameters: Training hyperparameters
            stop_event: Event to signal training should stop
        """
        # Similar to LoRA training but with full fine-tuning-specific logic
        # For now, we'll just call the LoRA training method as a placeholder
        self._run_lora_training(job_id, model_id, dataset_id, hyperparameters, stop_event)
