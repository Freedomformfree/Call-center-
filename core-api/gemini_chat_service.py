"""
Gemini Chat Service - Specialized chat interface for AI agent tools management.

This service provides a specialized Gemini AI chat interface designed specifically
for managing AI agent tools, creating workflows, and automating business processes.
It includes intelligent parsing of user requests and automatic tool execution.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from uuid import UUID, uuid4
from dataclasses import dataclass
from enum import Enum

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import structlog
from sqlmodel import Session, select

from database import get_db_manager
from models import User, AIToolConfig, ConversationContext
from config import get_api_keys

logger = structlog.get_logger(__name__)


class ChatRole(Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """Chat message data structure."""
    id: str
    role: ChatRole
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class ToolAction:
    """Parsed tool action from user message."""
    tool_name: str
    action: str
    parameters: Dict[str, Any]
    confidence: float


@dataclass
class GeminiChatResponse:
    """Gemini chat response with parsed actions."""
    text: str
    tool_actions: List[ToolAction]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]


class GeminiChatService:
    """
    Specialized Gemini chat service for AI agent tools management.
    
    This service provides an intelligent chat interface that can:
    - Understand natural language requests for tool operations
    - Parse and execute tool actions automatically
    - Manage conversation context and history
    - Provide specialized prompts for different tool categories
    """
    
    def __init__(self):
        """Initialize the Gemini chat service."""
        self.db_manager = get_db_manager()
        self.engine = self.db_manager.engine
        
        # Gemini configuration
        api_keys = get_api_keys()
        self.api_key = api_keys.gemini_api_key
        self.model_name = "gemini-1.5-pro"
        self.temperature = 0.7
        self.max_tokens = 2048
        
        # Chat sessions
        self.chat_sessions: Dict[str, List[ChatMessage]] = {}
        self.active_models: Dict[str, Any] = {}
        
        # System prompts for different contexts
        self.system_prompts = self._initialize_system_prompts()
        
        # Tool action patterns
        self.tool_patterns = self._initialize_tool_patterns()
        
        # Safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the Gemini chat service.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if not self.api_key:
                logger.error("Gemini API key not configured")
                return False
            
            # Configure Gemini API
            genai.configure(api_key=self.api_key)
            
            # Test API connectivity
            test_model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings=self.safety_settings
            )
            
            test_response = test_model.generate_content("Hello, this is a test.")
            if not test_response:
                raise Exception("API test failed")
            
            logger.info("Gemini chat service initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Gemini chat service", error=str(e))
            return False
    
    def _initialize_system_prompts(self) -> Dict[str, str]:
        """Initialize system prompts for different contexts."""
        return {
            "ai_tools_manager": """You are an AI Tools Manager assistant specialized in helping users manage, configure, and automate their business tools. Your primary responsibilities include:

1. **Tool Management**: Help users configure, connect, and manage various AI tools like Gmail, Calendar, Slack, Trello, WhatsApp, etc.

2. **Workflow Creation**: Assist in creating automated workflows that connect multiple tools together.

3. **Action Parsing**: When users request actions, parse their intent and suggest specific tool operations.

4. **Configuration Guidance**: Provide step-by-step guidance for setting up API keys and tool configurations.

5. **Automation Suggestions**: Proactively suggest automation opportunities based on user needs.

**Response Format Guidelines**:
- Always be helpful and provide clear, actionable responses
- When suggesting tool actions, format them clearly
- Provide examples when explaining complex concepts
- Ask clarifying questions when user intent is unclear
- Be proactive in suggesting related tools or workflows

**Tool Action Format**:
When you identify that a user wants to perform a specific tool action, include it in your response using this format:
```json
{
  "tool_actions": [
    {
      "tool_name": "gmail",
      "action": "send_email",
      "parameters": {
        "to": "example@email.com",
        "subject": "Subject",
        "body": "Email content"
      },
      "confidence": 0.9
    }
  ]
}
```

**Available Tools**: Gmail, Google Calendar, Google Drive, Slack, Trello, WhatsApp Business, Telegram, Zoom, Microsoft Graph, Click Payments, HubSpot, Salesforce

Remember: You are focused on practical tool management and automation. Always prioritize user productivity and business efficiency.""",

            "workflow_builder": """You are a Workflow Builder assistant specialized in creating automated business processes. Your expertise includes:

1. **Process Analysis**: Understanding business processes and identifying automation opportunities
2. **Tool Integration**: Connecting different tools to create seamless workflows
3. **Trigger Configuration**: Setting up triggers that start automated processes
4. **Conditional Logic**: Implementing if-then logic in workflows
5. **Error Handling**: Building robust workflows with proper error handling

Focus on creating practical, efficient workflows that save time and reduce manual work.""",

            "troubleshooter": """You are a Technical Troubleshooter for AI tools and integrations. Your role includes:

1. **Diagnostic Analysis**: Identifying issues with tool configurations and connections
2. **Solution Guidance**: Providing step-by-step troubleshooting instructions
3. **API Debugging**: Helping resolve API connection and authentication issues
4. **Performance Optimization**: Suggesting improvements for tool performance
5. **Best Practices**: Recommending security and efficiency best practices

Always provide clear, technical solutions while being accessible to non-technical users."""
        }
    
    def _initialize_tool_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize patterns for recognizing tool actions in user messages."""
        return {
            "gmail": [
                {
                    "pattern": r"send.*email|email.*to|compose.*email",
                    "action": "send_email",
                    "required_params": ["to", "subject", "body"]
                },
                {
                    "pattern": r"read.*email|check.*email|get.*email",
                    "action": "read_emails",
                    "required_params": []
                }
            ],
            "calendar": [
                {
                    "pattern": r"create.*event|schedule.*meeting|book.*appointment",
                    "action": "create_event",
                    "required_params": ["title", "start_time", "end_time"]
                },
                {
                    "pattern": r"check.*calendar|view.*events|list.*meetings",
                    "action": "list_events",
                    "required_params": []
                }
            ],
            "slack": [
                {
                    "pattern": r"send.*slack|message.*slack|post.*slack",
                    "action": "send_message",
                    "required_params": ["channel", "text"]
                }
            ],
            "whatsapp": [
                {
                    "pattern": r"send.*whatsapp|whatsapp.*message",
                    "action": "send_message",
                    "required_params": ["phone", "message"]
                }
            ]
        }
    
    async def start_chat_session(self, user_id: UUID, context: str = "ai_tools_manager") -> str:
        """
        Start a new chat session for a user.
        
        Args:
            user_id: User identifier
            context: Chat context (ai_tools_manager, workflow_builder, troubleshooter)
            
        Returns:
            str: Session ID
        """
        session_id = str(uuid4())
        
        # Initialize session with system message
        system_prompt = self.system_prompts.get(context, self.system_prompts["ai_tools_manager"])
        
        self.chat_sessions[session_id] = [
            ChatMessage(
                id=str(uuid4()),
                role=ChatRole.SYSTEM,
                content=system_prompt,
                timestamp=datetime.utcnow(),
                metadata={"user_id": str(user_id), "context": context}
            )
        ]
        
        # Create Gemini model for this session
        tools = self._get_function_declarations()
        tool_config = genai.types.ToolConfig(
            function_calling_config=genai.types.FunctionCallingConfig(
                mode=genai.types.FunctionCallingConfig.Mode.AUTO,
                allowed_function_names=[tool.name for tool in tools]
            )
        )
        self.active_models[session_id] = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self.safety_settings,
            system_instruction=system_prompt,
            tools=tools,
            tool_config=tool_config
        )
        
        logger.info("Started chat session", session_id=session_id, user_id=str(user_id), context=context)
        
        return session_id
    
    async def send_message(self, session_id: str, user_message: str, user_id: UUID) -> GeminiChatResponse:
        """
        Send a message to the chat session and get AI response.
        
        Args:
            session_id: Chat session ID
            user_message: User's message
            user_id: User identifier
            
        Returns:
            GeminiChatResponse: AI response with parsed actions
        """
        start_time = time.time()
        
        try:
            if session_id not in self.chat_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            # Add user message to session
            user_msg = ChatMessage(
                id=str(uuid4()),
                role=ChatRole.USER,
                content=user_message,
                timestamp=datetime.utcnow(),
                metadata={"user_id": str(user_id)}
            )
            self.chat_sessions[session_id].append(user_msg)
            
            # Get conversation history for context
            conversation_history = self._build_conversation_history(session_id)
            
            # Generate response using Gemini
            model = self.active_models[session_id]
            response = model.generate_content(
                conversation_history,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            
            if not response:
                raise Exception("Empty response from Gemini")

            response_text = ""
            tool_actions = []

            # Check for function calls
            function_call_response = None
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                logger.info("Function call requested by model",
                            function_name=function_call.name,
                            args=dict(function_call.args))
                # TODO: Execute the function and send the result back to the model
                # For now, just return a generic message and populate tool_actions
                response_text = f"Function call {function_call.name} received. Executing..."
                tool_actions = [ToolAction(
                    tool_name=function_call.name.split("_")[0], # Extract tool name
                    action=function_call.name.split("_")[1] if "_" in function_call.name else function_call.name, # Extract action
                    parameters=dict(function_call.args),
                    confidence=1.0 # Confidence is high as it's a direct function call
                )]
                function_call_response = {
                    "name": function_call.name,
                    "args": dict(function_call.args)
                }
            elif response.text:
                response_text = response.text.strip()
                # Parse tool actions from response if no function call
                tool_actions = await self._parse_tool_actions(user_message, response_text, user_id)
            else:
                # If there's no text and no function call, it's an issue.
                logger.warning("Gemini response has no text and no function call.", response=response)
                response_text = "No response text received." # Ensure response_text is not None

            # Add assistant response to session
            assistant_metadata = {
                "user_id": str(user_id),
                "tool_actions": [action.__dict__ for action in tool_actions]
            }
            if function_call_response:
                assistant_metadata["function_call"] = function_call_response

            # Add Gemini response details if available
            if response.candidates:
                candidate = response.candidates[0]
                assistant_metadata["gemini_response"] = {
                    "finish_reason": candidate.finish_reason.name if candidate.finish_reason else None,
                    "safety_ratings": [rating.__dict__ for rating in candidate.safety_ratings] if candidate.safety_ratings else []
                }

            assistant_msg = ChatMessage(
                id=str(uuid4()),
                role=ChatRole.ASSISTANT,
                content=response_text,
                timestamp=datetime.utcnow(),
                metadata=assistant_metadata
            )
            self.chat_sessions[session_id].append(assistant_msg)
            
            processing_time = time.time() - start_time
            
            logger.info("Generated chat response", 
                       session_id=session_id, 
                       user_id=str(user_id),
                       response_length=len(response_text),
                       tool_actions_count=len(tool_actions),
                       processing_time=processing_time)
            
            return GeminiChatResponse(
                text=response_text,
                tool_actions=tool_actions,
                confidence=0.9,  # Could be calculated based on response quality
                processing_time=processing_time,
                metadata={
                    "session_id": session_id,
                    "message_count": len(self.chat_sessions[session_id]),
                    "gemini_response": response.__dict__ if hasattr(response, '__dict__') else {}
                }
            )
            
        except Exception as e:
            logger.error("Failed to generate chat response", 
                        error=str(e), 
                        session_id=session_id, 
                        user_id=str(user_id))
            
            # Return error response
            return GeminiChatResponse(
                text=f"I apologize, but I encountered an error processing your request: {str(e)}",
                tool_actions=[],
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    def _build_conversation_history(self, session_id: str) -> List[str]:
        """Build conversation history for Gemini context."""
        messages = self.chat_sessions[session_id]
        history = []
        
        for msg in messages[-10:]:  # Keep last 10 messages for context
            if msg.role == ChatRole.USER:
                history.append(f"User: {msg.content}")
            elif msg.role == ChatRole.ASSISTANT:
                history.append(f"Assistant: {msg.content}")
        
        return history
    
    async def _parse_tool_actions(self, user_message: str, ai_response: str, user_id: UUID) -> List[ToolAction]:
        """
        Parse tool actions from user message and AI response.
        
        Args:
            user_message: Original user message
            ai_response: AI response text
            user_id: User identifier
            
        Returns:
            List[ToolAction]: Parsed tool actions
        """
        tool_actions = []
        
        # If AI response is empty or indicates a function call was handled, don't parse for JSON actions
        if not ai_response or "Function call" in ai_response:
            return tool_actions

        try:
            # First, check if AI response contains JSON tool actions
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                if json_end > json_start:
                    json_content = ai_response[json_start:json_end].strip()
                    try:
                        parsed_json = json.loads(json_content)
                        if "tool_actions" in parsed_json:
                            for action_data in parsed_json["tool_actions"]:
                                tool_actions.append(ToolAction(
                                    tool_name=action_data.get("tool_name", ""),
                                    action=action_data.get("action", ""),
                                    parameters=action_data.get("parameters", {}),
                                    confidence=action_data.get("confidence", 0.8)
                                ))
                    except json.JSONDecodeError:
                        logger.warning("Failed to decode JSON from AI response", json_content=json_content)
                        pass # Fall through to pattern matching if JSON parsing fails
            
            # If no JSON actions found, use pattern matching on user message
            if not tool_actions:
                tool_actions = await self._pattern_match_actions(user_message, user_id)
            
            return tool_actions
            
        except Exception as e:
            logger.error("Failed to parse tool actions", error=str(e), user_message=user_message, ai_response=ai_response)
            return []
    
    async def _pattern_match_actions(self, user_message: str, user_id: UUID) -> List[ToolAction]:
        """Use pattern matching to identify tool actions in user message."""
        import re
        
        tool_actions = []
        message_lower = user_message.lower()
        
        # Get user's configured tools
        with Session(self.engine) as session:
            user_tools = session.exec(
                select(AIToolConfig).where(
                    AIToolConfig.user_id == user_id,
                    AIToolConfig.is_active == True
                )
            ).all()
            
            configured_tools = {tool.tool_name for tool in user_tools}
        
        # Check patterns for each configured tool
        for tool_name, patterns in self.tool_patterns.items():
            if tool_name not in configured_tools:
                continue
                
            for pattern_info in patterns:
                if re.search(pattern_info["pattern"], message_lower):
                    # Extract parameters from message (simplified)
                    parameters = self._extract_parameters(user_message, pattern_info["required_params"])
                    
                    tool_actions.append(ToolAction(
                        tool_name=tool_name,
                        action=pattern_info["action"],
                        parameters=parameters,
                        confidence=0.7
                    ))
                    break
        
        return tool_actions
    
    def _extract_parameters(self, message: str, required_params: List[str]) -> Dict[str, Any]:
        """Extract parameters from user message (simplified implementation)."""
        import re
        
        parameters = {}
        
        # Email extraction
        if "to" in required_params:
            email_pattern = r'\b[A-Za-z0-TldZ0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, message)
            if emails:
                parameters["to"] = emails[0]
        
        # Phone number extraction
        if "phone" in required_params:
            phone_pattern = r'\+?[\d\s\-\(\)]{10,}'
            phones = re.findall(phone_pattern, message)
            if phones:
                parameters["phone"] = phones[0]
        
        # Subject/title extraction (text after "subject:" or "title:")
        if "subject" in required_params or "title" in required_params:
            subject_pattern = r'(?:subject|title):\s*([^\n]+)'
            subjects = re.findall(subject_pattern, message, re.IGNORECASE)
            if subjects:
                key = "subject" if "subject" in required_params else "title"
                parameters[key] = subjects[0].strip()
        
        return parameters
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat session history."""
        if session_id not in self.chat_sessions:
            return []
        
        history = []
        for msg in self.chat_sessions[session_id]:
            if msg.role != ChatRole.SYSTEM:  # Exclude system messages from history
                history.append({
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                })
        
        return history
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear a chat session."""
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
        if session_id in self.active_models:
            del self.active_models[session_id]
        
        logger.info("Cleared chat session", session_id=session_id)
        return True
    
    async def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self.chat_sessions.keys())

    def _get_function_declarations(self) -> List[genai.types.FunctionDeclaration]:
        """Build function declarations from tool patterns."""
        function_declarations = []
        for tool_name, patterns in self.tool_patterns.items():
            for pattern_info in patterns:
                function_name = f"{tool_name}_{pattern_info['action']}"
                description = f"Performs {pattern_info['action']} for {tool_name}"

                # Define properties based on required_params
                properties = {}
                for param in pattern_info["required_params"]:
                    properties[param] = genai.types.Schema(
                        type=genai.types.Type.STRING, # Assuming all params are strings for now
                        description=f"Parameter for {param}"
                    )

                function_declarations.append(
                    genai.types.FunctionDeclaration(
                        name=function_name,
                        description=description,
                        parameters=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            properties=properties,
                            required=pattern_info["required_params"]
                        )
                    )
                )
        return function_declarations


# Global service instance - lazy initialization
_gemini_chat_service = None

def get_gemini_chat_service() -> GeminiChatService:
    """Get global gemini chat service instance."""
    global _gemini_chat_service
    if _gemini_chat_service is None:
        _gemini_chat_service = GeminiChatService()
    return _gemini_chat_service