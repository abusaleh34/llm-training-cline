# Agent Deployment Service

This service is responsible for deploying and managing AI agents for interactive use. It's part of the LLM Training Platform, which allows organizations to train and deploy AI agents using their own data.

## Features

### Agent Management

- Deploy AI agents based on fine-tuned models or RAG systems
- Manage agent lifecycle (create, deploy, stop, delete)
- Configure agent parameters (temperature, top-p, etc.)
- Tag and organize agents

### Conversation Interface

- Interactive chat interface with deployed agents
- Support for both fine-tuned and RAG-based agents
- Conversation history management
- Source citation for RAG responses

### Offline Operation

- Works completely offline with no dependency on external services
- Uses locally trained models and locally stored data
- Secure and privacy-focused

## Architecture

The service is organized into several components:

- **API**: FastAPI endpoints for agent management and chat interface
- **Models**: Database models for agents and conversations
- **Service**: Agent deployment and management logic

## API Endpoints

### Agents

- `POST /api/v1/agent-deployment/agents`: Create a new agent
- `GET /api/v1/agent-deployment/agents`: List agents
- `GET /api/v1/agent-deployment/agents/{agent_id}`: Get agent details
- `DELETE /api/v1/agent-deployment/agents/{agent_id}`: Delete an agent
- `POST /api/v1/agent-deployment/agents/{agent_id}/deploy`: Deploy an agent
- `POST /api/v1/agent-deployment/agents/{agent_id}/stop`: Stop a deployed agent

### Chat

- `POST /api/v1/agent-deployment/chat`: Chat with a fine-tuned agent
- `POST /api/v1/agent-deployment/rag-chat`: Chat with a RAG agent

### Conversations

- `GET /api/v1/agent-deployment/conversations`: List conversations
- `GET /api/v1/agent-deployment/conversations/{conversation_id}`: Get conversation details
- `DELETE /api/v1/agent-deployment/conversations/{conversation_id}`: Delete a conversation

## Agent Types

### Fine-tuned Agent

Fine-tuned agents use models that have been fine-tuned on specific data. They provide responses based on the patterns learned during training.

### RAG Agent

RAG (Retrieval-Augmented Generation) agents combine a language model with a retrieval system. They retrieve relevant documents from a vector store and use them to generate contextually informed responses.

## Configuration

The service can be configured through environment variables:

- `MODEL_STORAGE_PATH`: Path to store model files
- `MAX_DEPLOYED_AGENTS`: Maximum number of concurrently deployed agents
- `AGENT_TIMEOUT_SECONDS`: Timeout for inactive agents

## Deployment

The service is containerized and can be deployed using Docker:

```bash
docker build -t llm-platform/agent-deployment -f deployment/docker/Dockerfile.agent_deployment .
docker run -p 8004:8004 llm-platform/agent-deployment
```

Or using docker-compose:

```bash
docker-compose up agent-deployment
```

## Security

- All agents and conversations are user-scoped
- Authentication required for all endpoints
- No external API calls or dependencies
- All data remains on-premise
