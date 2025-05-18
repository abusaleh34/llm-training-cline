# Model Training Service

This service is responsible for training and fine-tuning language models, as well as setting up Retrieval-Augmented Generation (RAG) systems. It's part of the LLM Training Platform, which allows organizations to train and deploy AI agents using their own data.

## Features

### Fine-tuning

- Support for multiple fine-tuning techniques:
  - Full fine-tuning
  - LoRA (Low-Rank Adaptation)
  - QLoRA (Quantized Low-Rank Adaptation)
  - PEFT (Parameter-Efficient Fine-Tuning)
- Training job management with progress tracking
- Model versioning and storage

### RAG (Retrieval-Augmented Generation)

- Integration with vector stores for efficient retrieval
- Support for various embedding models, including Arabic-optimized ones
- Configurable retrieval parameters (top-k, similarity threshold, etc.)
- Context-aware generation with retrieved documents

## Architecture

The service is organized into several components:

- **API**: FastAPI endpoints for model management and inference
- **Registry**: Model and training job management
- **Training**: Training job execution and monitoring
- **RAG**: Retrieval-augmented generation setup and execution

## API Endpoints

### Models

- `GET /api/v1/model-training/models`: List models
- `GET /api/v1/model-training/models/{model_id}`: Get model details
- `DELETE /api/v1/model-training/models/{model_id}`: Delete a model
- `POST /api/v1/model-training/models/fine-tune`: Create a fine-tuning model
- `POST /api/v1/model-training/models/rag`: Create a RAG model

### Training Jobs

- `GET /api/v1/model-training/training-jobs`: List training jobs
- `GET /api/v1/model-training/training-jobs/{job_id}`: Get training job details
- `POST /api/v1/model-training/training-jobs/{job_id}/cancel`: Cancel a training job

### Inference

- `POST /api/v1/model-training/inference`: Run inference with a fine-tuned model
- `POST /api/v1/model-training/rag/inference`: Run RAG inference

## Supported Models

### Base Models

- Mistral (7B, 13B)
- LLaMA (7B, 13B, 70B)
- Falcon (7B, 40B)
- Other open-source LLMs

### Embedding Models

- BAAI/BGE (multilingual)
- CAMeL (Arabic-optimized)
- AraBERT (Arabic-optimized)
- Sentence Transformers (multilingual)

## Configuration

The service can be configured through environment variables:

- `MODEL_STORAGE_PATH`: Path to store model files
- `MODEL_CACHE_PATH`: Path for model cache
- `MAX_TRAINING_JOBS`: Maximum number of concurrent training jobs
- `DEFAULT_BATCH_SIZE`: Default batch size for training
- `DEFAULT_LEARNING_RATE`: Default learning rate for training

## Deployment

The service is containerized and can be deployed using Docker:

```bash
docker build -t llm-platform/model-training -f deployment/docker/Dockerfile.model_training .
docker run -p 8003:8003 llm-platform/model-training
```

Or using docker-compose:

```bash
docker-compose up model-training
```
