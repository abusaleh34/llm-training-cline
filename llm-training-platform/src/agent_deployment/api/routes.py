"""
API routes for the Agent Deployment service.
"""

from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session
from loguru import logger

from src.common.db.database import get_db
from src.common.auth.auth_handler import get_current_user
from src.agent_deployment.api.schemas import (
    AgentConfigRequest,
    AgentResponse,
    AgentListResponse,
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    ConversationListResponse,
    RAGChatRequest,
    RAGChatResponse,
    AgentType,
    AgentStatus,
    ChatMessage,
    ErrorResponse,
)
from src.agent_deployment.models.agent import Agent, Conversation
from src.agent_deployment.service.agent_manager import (
    deploy_agent,
    stop_agent,
    create_conversation,
    add_message_to_conversation,
    generate_response,
    generate_rag_response,
    get_conversation,
)


router = APIRouter(
    prefix="/api/v1/agent-deployment",
    tags=["agent-deployment"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)


@router.post(
    "/agents",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
    description="Create a new agent from a model",
)
async def create_agent(
    agent_config: AgentConfigRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new agent."""
    try:
        # Determine agent type based on model ID
        # In a real implementation, this would query the model registry
        # to determine if the model is fine-tuned or RAG
        agent_type = AgentType.FINE_TUNED
        
        # Create agent in database
        agent = Agent(
            name=agent_config.name,
            model_id=agent_config.model_id,
            agent_type=agent_type,
            user_id=current_user["id"],
            description=agent_config.description,
            tags=agent_config.tags,
            config=agent_config.config,
            status=AgentStatus.CREATED,
        )
        
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        
        logger.info(f"Created agent: {agent.id}")
        
        # Deploy agent
        success = await deploy_agent(agent)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deploy agent: {agent.id}",
            )
        
        return agent
    
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating agent: {str(e)}",
        )


@router.get(
    "/agents",
    response_model=AgentListResponse,
    summary="List agents",
    description="List agents for the current user",
)
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of agents to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of agents to return"),
    agent_type: Optional[AgentType] = Query(None, description="Filter by agent type"),
    status: Optional[AgentStatus] = Query(None, description="Filter by agent status"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List agents."""
    try:
        # Build query
        query = db.query(Agent).filter(Agent.user_id == current_user["id"])
        
        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)
        
        if status:
            query = query.filter(Agent.status == status)
        
        if tag:
            query = query.filter(Agent.tags.contains([tag]))
        
        # Get total count
        total_count = await query.count()
        
        # Get agents
        agents = await query.order_by(Agent.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "agents": agents,
            "count": total_count,
        }
    
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing agents: {str(e)}",
        )


@router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    summary="Get agent",
    description="Get agent details",
)
async def get_agent(
    agent_id: str = Path(..., description="Agent ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get agent details."""
    try:
        # Get agent
        agent = await db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.user_id == current_user["id"],
        ).first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}",
            )
        
        return agent
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting agent: {str(e)}",
        )


@router.delete(
    "/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete agent",
    description="Delete an agent",
)
async def delete_agent(
    agent_id: str = Path(..., description="Agent ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete an agent."""
    try:
        # Get agent
        agent = await db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.user_id == current_user["id"],
        ).first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}",
            )
        
        # Stop agent if deployed
        await stop_agent(agent_id)
        
        # Delete agent
        await db.delete(agent)
        await db.commit()
        
        logger.info(f"Deleted agent: {agent_id}")
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error deleting agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting agent: {str(e)}",
        )


@router.post(
    "/agents/{agent_id}/deploy",
    response_model=AgentResponse,
    summary="Deploy agent",
    description="Deploy an agent",
)
async def deploy_agent_endpoint(
    agent_id: str = Path(..., description="Agent ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Deploy an agent."""
    try:
        # Get agent
        agent = await db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.user_id == current_user["id"],
        ).first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}",
            )
        
        # Deploy agent
        success = await deploy_agent(agent)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deploy agent: {agent_id}",
            )
        
        # Refresh agent
        await db.refresh(agent)
        
        return agent
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error deploying agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deploying agent: {str(e)}",
        )


@router.post(
    "/agents/{agent_id}/stop",
    response_model=AgentResponse,
    summary="Stop agent",
    description="Stop a deployed agent",
)
async def stop_agent_endpoint(
    agent_id: str = Path(..., description="Agent ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Stop a deployed agent."""
    try:
        # Get agent
        agent = await db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.user_id == current_user["id"],
        ).first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}",
            )
        
        # Stop agent
        success = await stop_agent(agent_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to stop agent: {agent_id}",
            )
        
        # Refresh agent
        await db.refresh(agent)
        
        return agent
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error stopping agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping agent: {str(e)}",
        )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with an agent",
    description="Send a message to an agent and get a response",
)
async def chat(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Chat with an agent."""
    try:
        # Get agent
        agent = await db.query(Agent).filter(
            Agent.id == chat_request.agent_id,
            Agent.user_id == current_user["id"],
        ).first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {chat_request.agent_id}",
            )
        
        # Check if agent is deployed
        if agent.status != AgentStatus.DEPLOYED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent is not deployed: {chat_request.agent_id}",
            )
        
        # Get or create conversation
        conversation_id = chat_request.conversation_id
        
        if not conversation_id:
            # Create new conversation
            conversation_id = await create_conversation(
                agent_id=agent.id,
                user_id=current_user["id"],
            )
            
            if not conversation_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create conversation for agent: {agent.id}",
                )
        else:
            # Check if conversation exists
            conversation = await db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.agent_id == agent.id,
                Conversation.user_id == current_user["id"],
            ).first()
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation not found: {conversation_id}",
                )
        
        # Create user message
        user_message = ChatMessage(
            role="user",
            content=chat_request.message,
            timestamp=datetime.utcnow(),
        )
        
        # Add user message to conversation
        success = await add_message_to_conversation(
            agent_id=agent.id,
            conversation_id=conversation_id,
            message=user_message,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add message to conversation: {conversation_id}",
            )
        
        # Generate response
        response = await generate_response(
            agent_id=agent.id,
            conversation_id=conversation_id,
            generation_config=chat_request.generation_config,
        )
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate response for conversation: {conversation_id}",
            )
        
        # Return response
        return {
            "agent_id": agent.id,
            "conversation_id": conversation_id,
            "message": response,
            "metadata": None,
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error chatting with agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error chatting with agent: {str(e)}",
        )


@router.post(
    "/rag-chat",
    response_model=RAGChatResponse,
    summary="Chat with a RAG agent",
    description="Send a message to a RAG agent and get a response with retrieved contexts",
)
async def rag_chat(
    chat_request: RAGChatRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Chat with a RAG agent."""
    try:
        # Get agent
        agent = await db.query(Agent).filter(
            Agent.id == chat_request.agent_id,
            Agent.user_id == current_user["id"],
        ).first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {chat_request.agent_id}",
            )
        
        # Check if agent is deployed
        if agent.status != AgentStatus.DEPLOYED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent is not deployed: {chat_request.agent_id}",
            )
        
        # Check if agent is a RAG agent
        if agent.agent_type != AgentType.RAG:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent is not a RAG agent: {chat_request.agent_id}",
            )
        
        # Get or create conversation
        conversation_id = chat_request.conversation_id
        
        if not conversation_id:
            # Create new conversation
            conversation_id = await create_conversation(
                agent_id=agent.id,
                user_id=current_user["id"],
            )
            
            if not conversation_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create conversation for agent: {agent.id}",
                )
        else:
            # Check if conversation exists
            conversation = await db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.agent_id == agent.id,
                Conversation.user_id == current_user["id"],
            ).first()
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation not found: {conversation_id}",
                )
        
        # Create user message
        user_message = ChatMessage(
            role="user",
            content=chat_request.message,
            timestamp=datetime.utcnow(),
        )
        
        # Add user message to conversation
        success = await add_message_to_conversation(
            agent_id=agent.id,
            conversation_id=conversation_id,
            message=user_message,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add message to conversation: {conversation_id}",
            )
        
        # Generate RAG response
        result = await generate_rag_response(
            agent_id=agent.id,
            conversation_id=conversation_id,
            retrieval_config=chat_request.retrieval_config,
            generation_config=chat_request.generation_config,
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate RAG response for conversation: {conversation_id}",
            )
        
        response, contexts = result
        
        # Return response
        return {
            "agent_id": agent.id,
            "conversation_id": conversation_id,
            "message": response,
            "contexts": contexts,
            "metadata": None,
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error chatting with RAG agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error chatting with RAG agent: {str(e)}",
        )


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List conversations",
    description="List conversations for the current user",
)
async def list_conversations(
    skip: int = Query(0, ge=0, description="Number of conversations to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of conversations to return"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List conversations."""
    try:
        # Build query
        query = db.query(Conversation).filter(Conversation.user_id == current_user["id"])
        
        if agent_id:
            query = query.filter(Conversation.agent_id == agent_id)
        
        # Get total count
        total_count = await query.count()
        
        # Get conversations
        conversations = await query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "conversations": conversations,
            "count": total_count,
        }
    
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing conversations: {str(e)}",
        )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation",
    description="Get conversation details",
)
async def get_conversation_endpoint(
    conversation_id: str = Path(..., description="Conversation ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get conversation details."""
    try:
        # Get conversation
        conversation = await db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user["id"],
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation not found: {conversation_id}",
            )
        
        return conversation
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting conversation: {str(e)}",
        )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
    description="Delete a conversation",
)
async def delete_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete a conversation."""
    try:
        # Get conversation
        conversation = await db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user["id"],
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation not found: {conversation_id}",
            )
        
        # Delete conversation
        await db.delete(conversation)
        await db.commit()
        
        logger.info(f"Deleted conversation: {conversation_id}")
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting conversation: {str(e)}",
        )
