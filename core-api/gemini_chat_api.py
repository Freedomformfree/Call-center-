"""
Gemini Chat API - REST endpoints for Gemini AI chat functionality.

This module provides REST API endpoints for the Gemini chat service,
including session management, message handling, and tool action execution.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from uuid import UUID
import structlog

from gemini_chat_service import gemini_chat_service, GeminiChatResponse
from gemini_response_parser import gemini_response_parser, ParsedResponse
from ai_tools_service import get_ai_tools_service, AIToolsService
from auth import get_current_user
from models import User

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/gemini-chat", tags=["Gemini Chat"])


# Request/Response Models
class StartChatSessionRequest(BaseModel):
    """Request model for starting a chat session."""
    context: str = Field(default="ai_tools_manager", description="Chat context type")


class StartChatSessionResponse(BaseModel):
    """Response model for starting a chat session."""
    success: bool
    session_id: str
    context: str
    message: str


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""
    session_id: str = Field(..., description="Chat session ID")
    message: str = Field(..., description="User message")
    auto_execute_tools: bool = Field(default=False, description="Automatically execute detected tool actions")


class SendMessageResponse(BaseModel):
    """Response model for sending a message."""
    success: bool
    response: str
    tool_actions: List[Dict[str, Any]]
    executed_actions: List[Dict[str, Any]]
    confidence: float
    processing_time: float
    suggestions: List[str]
    metadata: Dict[str, Any]


class ChatHistoryResponse(BaseModel):
    """Response model for chat history."""
    success: bool
    history: List[Dict[str, Any]]
    message_count: int
    session_id: str


class ParseResponseRequest(BaseModel):
    """Request model for parsing a response."""
    text: str = Field(..., description="Text to parse")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context")


class ParseResponseResponse(BaseModel):
    """Response model for parsed response."""
    success: bool
    parsed_response: Dict[str, Any]
    processing_time: float


# API Endpoints
@router.post("/start-session", response_model=StartChatSessionResponse)
async def start_chat_session(
    request: StartChatSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Start a new Gemini chat session.
    
    Creates a new chat session with the specified context for the current user.
    The session will be initialized with appropriate system prompts based on the context.
    """
    try:
        # Initialize the service if not already done
        if not await gemini_chat_service.initialize():
            raise HTTPException(status_code=503, detail="Gemini chat service not available")
        
        session_id = await gemini_chat_service.start_chat_session(
            user_id=current_user.id,
            context=request.context
        )
        
        logger.info("Started chat session", 
                   user_id=str(current_user.id), 
                   session_id=session_id, 
                   context=request.context)
        
        return StartChatSessionResponse(
            success=True,
            session_id=session_id,
            context=request.context,
            message=f"Chat session started with {request.context} context"
        )
        
    except Exception as e:
        logger.error("Failed to start chat session", error=str(e), user_id=str(current_user.id))
        raise HTTPException(status_code=500, detail=f"Failed to start chat session: {str(e)}")


@router.post("/send-message", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    ai_tools_service: AIToolsService = Depends(get_ai_tools_service)
):
    """
    Send a message to a Gemini chat session.
    
    Sends a user message to the specified chat session and returns the AI response.
    Optionally executes detected tool actions automatically.
    """
    try:
        # Send message to Gemini
        response = await gemini_chat_service.send_message(
            session_id=request.session_id,
            user_message=request.message,
            user_id=current_user.id
        )
        
        executed_actions = []
        
        # Auto-execute tool actions if requested
        if request.auto_execute_tools and response.tool_actions:
            for tool_action in response.tool_actions:
                try:
                    # Execute the tool action
                    execution_result = await ai_tools_service.execute_tool_action(
                        user_id=current_user.id,
                        tool_name=tool_action.tool_name,
                        action=tool_action.action,
                        parameters=tool_action.parameters
                    )
                    
                    executed_actions.append({
                        "tool_name": tool_action.tool_name,
                        "action": tool_action.action,
                        "parameters": tool_action.parameters,
                        "result": execution_result,
                        "confidence": tool_action.confidence
                    })
                    
                except Exception as e:
                    logger.error("Failed to execute tool action", 
                               error=str(e), 
                               tool_name=tool_action.tool_name,
                               action=tool_action.action)
                    
                    executed_actions.append({
                        "tool_name": tool_action.tool_name,
                        "action": tool_action.action,
                        "parameters": tool_action.parameters,
                        "result": {"success": False, "error": str(e)},
                        "confidence": tool_action.confidence
                    })
        
        # Parse the response for additional insights
        parsed_response = await gemini_response_parser.parse_response(
            response.text,
            context={"user_id": str(current_user.id), "session_id": request.session_id}
        )
        
        logger.info("Processed chat message", 
                   user_id=str(current_user.id),
                   session_id=request.session_id,
                   tool_actions_count=len(response.tool_actions),
                   executed_actions_count=len(executed_actions),
                   confidence=response.confidence)
        
        return SendMessageResponse(
            success=True,
            response=response.text,
            tool_actions=[action.__dict__ for action in response.tool_actions],
            executed_actions=executed_actions,
            confidence=response.confidence,
            processing_time=response.processing_time,
            suggestions=parsed_response.suggestions,
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error("Failed to send message", 
                    error=str(e), 
                    user_id=str(current_user.id),
                    session_id=request.session_id)
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get chat history for a session.
    
    Retrieves the complete chat history for the specified session,
    excluding system messages.
    """
    try:
        history = await gemini_chat_service.get_session_history(session_id)
        
        logger.info("Retrieved chat history", 
                   user_id=str(current_user.id),
                   session_id=session_id,
                   message_count=len(history))
        
        return ChatHistoryResponse(
            success=True,
            history=history,
            message_count=len(history),
            session_id=session_id
        )
        
    except Exception as e:
        logger.error("Failed to get chat history", 
                    error=str(e), 
                    user_id=str(current_user.id),
                    session_id=session_id)
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Clear a chat session.
    
    Removes all messages and data associated with the specified chat session.
    """
    try:
        success = await gemini_chat_service.clear_session(session_id)
        
        if success:
            logger.info("Cleared chat session", 
                       user_id=str(current_user.id),
                       session_id=session_id)
            
            return {"success": True, "message": "Chat session cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to clear chat session", 
                    error=str(e), 
                    user_id=str(current_user.id),
                    session_id=session_id)
        raise HTTPException(status_code=500, detail=f"Failed to clear chat session: {str(e)}")


@router.get("/sessions")
async def get_active_sessions(
    current_user: User = Depends(get_current_user)
):
    """
    Get active chat sessions.
    
    Returns a list of all active chat session IDs for monitoring purposes.
    """
    try:
        sessions = await gemini_chat_service.get_active_sessions()
        
        logger.info("Retrieved active sessions", 
                   user_id=str(current_user.id),
                   session_count=len(sessions))
        
        return {
            "success": True,
            "sessions": sessions,
            "session_count": len(sessions)
        }
        
    except Exception as e:
        logger.error("Failed to get active sessions", 
                    error=str(e), 
                    user_id=str(current_user.id))
        raise HTTPException(status_code=500, detail=f"Failed to get active sessions: {str(e)}")


@router.post("/parse-response", response_model=ParseResponseResponse)
async def parse_response(
    request: ParseResponseRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Parse a text response using Gemini response parser.
    
    Analyzes the provided text and extracts structured information including
    intents, tool actions, workflows, and entities.
    """
    try:
        parsed_response = await gemini_response_parser.parse_response(
            request.text,
            context=request.context
        )
        
        logger.info("Parsed response", 
                   user_id=str(current_user.id),
                   text_length=len(request.text),
                   intent_type=parsed_response.intent.intent_type.value,
                   tool_actions_count=len(parsed_response.tool_actions),
                   confidence=parsed_response.confidence)
        
        return ParseResponseResponse(
            success=True,
            parsed_response={
                "intent": {
                    "type": parsed_response.intent.intent_type.value,
                    "confidence": parsed_response.intent.confidence,
                    "entities": parsed_response.intent.entities,
                    "context": parsed_response.intent.context
                },
                "tool_actions": [action.__dict__ for action in parsed_response.tool_actions],
                "workflows": [workflow.__dict__ for workflow in parsed_response.workflows],
                "extracted_data": parsed_response.extracted_data,
                "suggestions": parsed_response.suggestions,
                "confidence": parsed_response.confidence
            },
            processing_time=parsed_response.parsing_metadata.get("parsing_time", 0.0)
        )
        
    except Exception as e:
        logger.error("Failed to parse response", 
                    error=str(e), 
                    user_id=str(current_user.id))
        raise HTTPException(status_code=500, detail=f"Failed to parse response: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Gemini chat service.
    
    Verifies that the Gemini chat service is properly initialized and operational.
    """
    try:
        is_initialized = await gemini_chat_service.initialize()
        
        return {
            "success": True,
            "service": "gemini_chat",
            "status": "healthy" if is_initialized else "unhealthy",
            "initialized": is_initialized
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "success": False,
            "service": "gemini_chat",
            "status": "unhealthy",
            "error": str(e)
        }