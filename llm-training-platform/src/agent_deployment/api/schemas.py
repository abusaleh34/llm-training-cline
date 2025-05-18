"""
API schemas for the Agent Deployment service.
"""

from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator


class AgentType(str, Enum):
    """Agent type enum."""
    
    FINE_TUNED = "fine_tuned"
    RAG = "rag"


class AgentStatus(str, Enum):
    """Agent status enum."""
    
    CREATED = "created"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    STOPPED = "stopped"


class ErrorResponse(BaseModel):
    """Error response model."""
    
    detail: str


class AgentConfigRequest(BaseModel):
    """Agent configuration request model."""
    
    name: str = Field(..., description="Name of the agent")
    model_id: str = Field(..., description="ID of the model to use")
    description: Optional[str] = Field(None, description="Agent description")
    tags: Optional[List[str]] = Field(None, description="Agent tags")
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Agent configuration",
        example={
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 50,
            "max_tokens": 1024,
            "system_prompt": "You are a helpful AI assistant that answers questions based on the provided documents."
        },
    )


class AgentResponse(BaseModel):
    """Agent response model."""
    
    id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent name")
    model_id: str = Field(..., description="Model ID")
    agent_type: AgentType = Field(..., description="Agent type")
    status: AgentStatus = Field(..., description="Agent status")
    user_id: str = Field(..., description="User ID")
    description: Optional[str] = Field(None, description="Agent description")
    tags: Optional[List[str]] = Field(None, description="Agent tags")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Agent metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        orm_mode = True


class AgentListResponse(BaseModel):
    """Agent list response model."""
    
    agents: List[AgentResponse] = Field(..., description="List of agents")
    count: int = Field(..., description="Total count of agents")


class ChatMessage(BaseModel):
    """Chat message model."""
    
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")


class ChatRequest(BaseModel):
    """Chat request model."""
    
    agent_id: str = Field(..., description="Agent ID")
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for continuing a conversation")
    generation_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Generation configuration (overrides agent defaults)",
        example={
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 1024,
        },
    )


class ChatResponse(BaseModel):
    """Chat response model."""
    
    agent_id: str = Field(..., description="Agent ID")
    conversation_id: str = Field(..., description="Conversation ID")
    message: ChatMessage = Field(..., description="Assistant message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")


class ConversationResponse(BaseModel):
    """Conversation response model."""
    
    id: str = Field(..., description="Conversation ID")
    agent_id: str = Field(..., description="Agent ID")
    user_id: str = Field(..., description="User ID")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        orm_mode = True


class ConversationListResponse(BaseModel):
    """Conversation list response model."""
    
    conversations: List[ConversationResponse] = Field(..., description="List of conversations")
    count: int = Field(..., description="Total count of conversations")


class RetrievedContext(BaseModel):
    """Retrieved context model."""
    
    text: str = Field(..., description="Context text")
    document_id: str = Field(..., description="Document ID")
    document_name: str = Field(..., description="Document name")
    chunk_id: str = Field(..., description="Chunk ID")
    score: float = Field(..., description="Retrieval score")
    page_numbers: Optional[List[int]] = Field(None, description="Page numbers")


class RAGChatRequest(BaseModel):
    """RAG chat request model."""
    
    agent_id: str = Field(..., description="Agent ID")
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for continuing a conversation")
    retrieval_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Retrieval configuration (overrides agent defaults)",
        example={
            "top_k": 5,
            "similarity_threshold": 0.7,
        },
    )
    generation_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Generation configuration (overrides agent defaults)",
        example={
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 1024,
        },
    )


class RAGChatResponse(BaseModel):
    """RAG chat response model."""
    
    agent_id: str = Field(..., description="Agent ID")
    conversation_id: str = Field(..., description="Conversation ID")
    message: ChatMessage = Field(..., description="Assistant message")
    contexts: List[RetrievedContext] = Field(..., description="Retrieved contexts")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")
