"""
Agent manager for the Agent Deployment service.
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import json
from loguru import logger

from src.common.config.settings import settings
from src.agent_deployment.models.agent import Agent, Conversation
from src.agent_deployment.api.schemas import AgentType, AgentStatus, ChatMessage


# In-memory store for deployed agents
# Maps agent_id to agent runtime information
deployed_agents = {}


async def deploy_agent(agent: Agent) -> bool:
    """
    Deploy an agent.
    
    Args:
        agent: Agent to deploy
        
    Returns:
        bool: True if deployed successfully, False otherwise
    """
    try:
        # Check if agent is already deployed
        if agent.id in deployed_agents:
            logger.info(f"Agent {agent.id} is already deployed")
            return True
        
        # Check if we've reached the maximum number of deployed agents
        if len(deployed_agents) >= settings.MAX_DEPLOYED_AGENTS:
            logger.error(f"Maximum number of deployed agents reached: {settings.MAX_DEPLOYED_AGENTS}")
            return False
        
        # Update agent status to deploying
        agent.status = AgentStatus.DEPLOYING
        
        # Load model based on agent type
        if agent.agent_type == AgentType.FINE_TUNED:
            # Load fine-tuned model
            model_info = await load_fine_tuned_model(agent.model_id)
        elif agent.agent_type == AgentType.RAG:
            # Load RAG model
            model_info = await load_rag_model(agent.model_id)
        else:
            logger.error(f"Unknown agent type: {agent.agent_type}")
            return False
        
        # Store agent runtime information
        deployed_agents[agent.id] = {
            "agent": agent,
            "model_info": model_info,
            "last_used": datetime.utcnow(),
            "active_conversations": {},
        }
        
        # Update agent status to deployed
        agent.status = AgentStatus.DEPLOYED
        
        logger.info(f"Agent {agent.id} deployed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error deploying agent {agent.id}: {str(e)}")
        agent.status = AgentStatus.FAILED
        return False


async def stop_agent(agent_id: str) -> bool:
    """
    Stop a deployed agent.
    
    Args:
        agent_id: Agent ID
        
    Returns:
        bool: True if stopped successfully, False otherwise
    """
    try:
        # Check if agent is deployed
        if agent_id not in deployed_agents:
            logger.info(f"Agent {agent_id} is not deployed")
            return True
        
        # Get agent runtime information
        agent_runtime = deployed_agents[agent_id]
        agent = agent_runtime["agent"]
        
        # Update agent status to stopped
        agent.status = AgentStatus.STOPPED
        
        # Remove agent from deployed agents
        del deployed_agents[agent_id]
        
        logger.info(f"Agent {agent_id} stopped successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error stopping agent {agent_id}: {str(e)}")
        return False


async def stop_all_agents() -> None:
    """Stop all deployed agents."""
    logger.info(f"Stopping all deployed agents ({len(deployed_agents)})")
    
    for agent_id in list(deployed_agents.keys()):
        await stop_agent(agent_id)


async def load_fine_tuned_model(model_id: str) -> Dict[str, Any]:
    """
    Load a fine-tuned model.
    
    Args:
        model_id: Model ID
        
    Returns:
        Dict[str, Any]: Model information
    """
    # In a real implementation, this would load the model from the model registry
    # and initialize the model for inference
    
    # For now, we'll just return a placeholder
    return {
        "model_id": model_id,
        "model_type": "fine_tuned",
        "loaded_at": datetime.utcnow(),
    }


async def load_rag_model(model_id: str) -> Dict[str, Any]:
    """
    Load a RAG model.
    
    Args:
        model_id: Model ID
        
    Returns:
        Dict[str, Any]: Model information
    """
    # In a real implementation, this would load the model from the model registry,
    # initialize the model for inference, and set up the retrieval system
    
    # For now, we'll just return a placeholder
    return {
        "model_id": model_id,
        "model_type": "rag",
        "loaded_at": datetime.utcnow(),
    }


async def get_agent_status(agent_id: str) -> Optional[str]:
    """
    Get the status of an agent.
    
    Args:
        agent_id: Agent ID
        
    Returns:
        Optional[str]: Agent status if found, None otherwise
    """
    if agent_id in deployed_agents:
        return deployed_agents[agent_id]["agent"].status
    
    return None


async def update_agent_last_used(agent_id: str) -> None:
    """
    Update the last used timestamp for an agent.
    
    Args:
        agent_id: Agent ID
    """
    if agent_id in deployed_agents:
        deployed_agents[agent_id]["last_used"] = datetime.utcnow()


async def create_conversation(
    agent_id: str,
    user_id: str,
    system_message: Optional[str] = None,
) -> Optional[str]:
    """
    Create a new conversation with an agent.
    
    Args:
        agent_id: Agent ID
        user_id: User ID
        system_message: Optional system message to start the conversation
        
    Returns:
        Optional[str]: Conversation ID if created, None otherwise
    """
    try:
        # Check if agent is deployed
        if agent_id not in deployed_agents:
            logger.error(f"Agent {agent_id} is not deployed")
            return None
        
        # Generate conversation ID
        conversation_id = str(uuid.uuid4())
        
        # Initialize messages list
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message,
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        # Create conversation in memory
        deployed_agents[agent_id]["active_conversations"][conversation_id] = {
            "messages": messages,
            "last_updated": datetime.utcnow(),
        }
        
        # Create conversation in database
        conversation = Conversation(
            id=conversation_id,
            agent_id=agent_id,
            user_id=user_id,
            messages=messages,
        )
        
        logger.info(f"Created conversation {conversation_id} for agent {agent_id}")
        
        return conversation_id
    
    except Exception as e:
        logger.error(f"Error creating conversation for agent {agent_id}: {str(e)}")
        return None


async def get_conversation(
    agent_id: str,
    conversation_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Get a conversation.
    
    Args:
        agent_id: Agent ID
        conversation_id: Conversation ID
        
    Returns:
        Optional[Dict[str, Any]]: Conversation if found, None otherwise
    """
    try:
        # Check if agent is deployed
        if agent_id not in deployed_agents:
            logger.error(f"Agent {agent_id} is not deployed")
            return None
        
        # Check if conversation exists
        if conversation_id not in deployed_agents[agent_id]["active_conversations"]:
            logger.error(f"Conversation {conversation_id} not found for agent {agent_id}")
            return None
        
        return deployed_agents[agent_id]["active_conversations"][conversation_id]
    
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id} for agent {agent_id}: {str(e)}")
        return None


async def add_message_to_conversation(
    agent_id: str,
    conversation_id: str,
    message: ChatMessage,
) -> bool:
    """
    Add a message to a conversation.
    
    Args:
        agent_id: Agent ID
        conversation_id: Conversation ID
        message: Message to add
        
    Returns:
        bool: True if added successfully, False otherwise
    """
    try:
        # Check if agent is deployed
        if agent_id not in deployed_agents:
            logger.error(f"Agent {agent_id} is not deployed")
            return False
        
        # Check if conversation exists
        if conversation_id not in deployed_agents[agent_id]["active_conversations"]:
            logger.error(f"Conversation {conversation_id} not found for agent {agent_id}")
            return False
        
        # Add message to conversation
        deployed_agents[agent_id]["active_conversations"][conversation_id]["messages"].append(
            message.dict()
        )
        
        # Update last updated timestamp
        deployed_agents[agent_id]["active_conversations"][conversation_id]["last_updated"] = datetime.utcnow()
        
        # Update agent last used timestamp
        await update_agent_last_used(agent_id)
        
        return True
    
    except Exception as e:
        logger.error(f"Error adding message to conversation {conversation_id} for agent {agent_id}: {str(e)}")
        return False


async def generate_response(
    agent_id: str,
    conversation_id: str,
    generation_config: Optional[Dict[str, Any]] = None,
) -> Optional[ChatMessage]:
    """
    Generate a response from an agent.
    
    Args:
        agent_id: Agent ID
        conversation_id: Conversation ID
        generation_config: Generation configuration
        
    Returns:
        Optional[ChatMessage]: Generated response if successful, None otherwise
    """
    try:
        # Check if agent is deployed
        if agent_id not in deployed_agents:
            logger.error(f"Agent {agent_id} is not deployed")
            return None
        
        # Check if conversation exists
        if conversation_id not in deployed_agents[agent_id]["active_conversations"]:
            logger.error(f"Conversation {conversation_id} not found for agent {agent_id}")
            return None
        
        # Get agent runtime information
        agent_runtime = deployed_agents[agent_id]
        agent = agent_runtime["agent"]
        model_info = agent_runtime["model_info"]
        
        # Get conversation messages
        conversation = agent_runtime["active_conversations"][conversation_id]
        messages = conversation["messages"]
        
        # Merge agent config with generation config
        config = agent.config or {}
        if generation_config:
            config.update(generation_config)
        
        # In a real implementation, this would call the model to generate a response
        # For now, we'll just return a placeholder response
        response_content = f"This is a placeholder response from agent {agent.name} (ID: {agent.id})"
        
        # Create response message
        response = ChatMessage(
            role="assistant",
            content=response_content,
            timestamp=datetime.utcnow(),
        )
        
        # Add response to conversation
        await add_message_to_conversation(agent_id, conversation_id, response)
        
        # Update agent last used timestamp
        await update_agent_last_used(agent_id)
        
        return response
    
    except Exception as e:
        logger.error(f"Error generating response for conversation {conversation_id} from agent {agent_id}: {str(e)}")
        return None


async def generate_rag_response(
    agent_id: str,
    conversation_id: str,
    retrieval_config: Optional[Dict[str, Any]] = None,
    generation_config: Optional[Dict[str, Any]] = None,
) -> Optional[Tuple[ChatMessage, List[Dict[str, Any]]]]:
    """
    Generate a response from a RAG agent.
    
    Args:
        agent_id: Agent ID
        conversation_id: Conversation ID
        retrieval_config: Retrieval configuration
        generation_config: Generation configuration
        
    Returns:
        Optional[Tuple[ChatMessage, List[Dict[str, Any]]]]: Generated response and retrieved contexts if successful, None otherwise
    """
    try:
        # Check if agent is deployed
        if agent_id not in deployed_agents:
            logger.error(f"Agent {agent_id} is not deployed")
            return None
        
        # Check if conversation exists
        if conversation_id not in deployed_agents[agent_id]["active_conversations"]:
            logger.error(f"Conversation {conversation_id} not found for agent {agent_id}")
            return None
        
        # Get agent runtime information
        agent_runtime = deployed_agents[agent_id]
        agent = agent_runtime["agent"]
        model_info = agent_runtime["model_info"]
        
        # Check if agent is a RAG agent
        if agent.agent_type != AgentType.RAG:
            logger.error(f"Agent {agent_id} is not a RAG agent")
            return None
        
        # Get conversation messages
        conversation = agent_runtime["active_conversations"][conversation_id]
        messages = conversation["messages"]
        
        # Merge agent config with retrieval and generation configs
        config = agent.config or {}
        if retrieval_config:
            config.update({"retrieval": retrieval_config})
        if generation_config:
            config.update({"generation": generation_config})
        
        # In a real implementation, this would:
        # 1. Retrieve relevant contexts from the vector store
        # 2. Call the model to generate a response based on the contexts
        
        # For now, we'll just return placeholder data
        response_content = f"This is a placeholder RAG response from agent {agent.name} (ID: {agent.id})"
        
        # Create response message
        response = ChatMessage(
            role="assistant",
            content=response_content,
            timestamp=datetime.utcnow(),
        )
        
        # Add response to conversation
        await add_message_to_conversation(agent_id, conversation_id, response)
        
        # Update agent last used timestamp
        await update_agent_last_used(agent_id)
        
        # Create placeholder retrieved contexts
        contexts = [
            {
                "text": "This is a placeholder retrieved context.",
                "document_id": str(uuid.uuid4()),
                "document_name": "Sample Document",
                "chunk_id": str(uuid.uuid4()),
                "score": 0.95,
                "page_numbers": [1],
            }
        ]
        
        return response, contexts
    
    except Exception as e:
        logger.error(f"Error generating RAG response for conversation {conversation_id} from agent {agent_id}: {str(e)}")
        return None


async def cleanup_inactive_agents() -> None:
    """Cleanup inactive agents."""
    try:
        now = datetime.utcnow()
        timeout_seconds = settings.AGENT_TIMEOUT_SECONDS
        
        for agent_id in list(deployed_agents.keys()):
            agent_runtime = deployed_agents[agent_id]
            last_used = agent_runtime["last_used"]
            
            # Check if agent has been inactive for too long
            if (now - last_used).total_seconds() > timeout_seconds:
                logger.info(f"Stopping inactive agent {agent_id} (last used: {last_used})")
                await stop_agent(agent_id)
    
    except Exception as e:
        logger.error(f"Error cleaning up inactive agents: {str(e)}")
