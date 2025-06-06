"""
Gemini Response Parser - Advanced parsing and interpretation of Gemini AI responses.

This module provides sophisticated parsing capabilities for Gemini AI responses,
including intent recognition, parameter extraction, tool action identification,
and structured data extraction from natural language responses.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


class IntentType(Enum):
    """Types of user intents that can be recognized."""
    TOOL_EXECUTION = "tool_execution"
    INFORMATION_REQUEST = "information_request"
    CONFIGURATION = "configuration"
    WORKFLOW_CREATION = "workflow_creation"
    TROUBLESHOOTING = "troubleshooting"
    GENERAL_CHAT = "general_chat"


class ConfidenceLevel(Enum):
    """Confidence levels for parsed results."""
    HIGH = "high"      # 0.8 - 1.0
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"        # 0.0 - 0.5


@dataclass
class ParsedIntent:
    """Parsed user intent from message."""
    intent_type: IntentType
    confidence: float
    entities: Dict[str, Any]
    context: Dict[str, Any]


@dataclass
class ParsedToolAction:
    """Parsed tool action from response."""
    tool_name: str
    action: str
    parameters: Dict[str, Any]
    confidence: float
    validation_errors: List[str]


@dataclass
class ParsedWorkflow:
    """Parsed workflow definition."""
    name: str
    description: str
    triggers: List[Dict[str, Any]]
    steps: List[Dict[str, Any]]
    conditions: List[Dict[str, Any]]
    confidence: float


@dataclass
class ParsedResponse:
    """Complete parsed response from Gemini."""
    original_text: str
    intent: ParsedIntent
    tool_actions: List[ParsedToolAction]
    workflows: List[ParsedWorkflow]
    extracted_data: Dict[str, Any]
    suggestions: List[str]
    confidence: float
    parsing_metadata: Dict[str, Any]


class GeminiResponseParser:
    """
    Advanced parser for Gemini AI responses with intelligent interpretation.
    
    This parser can:
    - Identify user intents and extract entities
    - Parse tool actions with parameter validation
    - Extract workflow definitions
    - Recognize structured data patterns
    - Provide confidence scores for all extractions
    """
    
    def __init__(self):
        """Initialize the response parser."""
        self.intent_patterns = self._initialize_intent_patterns()
        self.tool_patterns = self._initialize_tool_patterns()
        self.entity_extractors = self._initialize_entity_extractors()
        self.workflow_patterns = self._initialize_workflow_patterns()
        
    def _initialize_intent_patterns(self) -> Dict[IntentType, List[Dict[str, Any]]]:
        """Initialize patterns for intent recognition."""
        return {
            IntentType.TOOL_EXECUTION: [
                {
                    "patterns": [
                        r"send.*email|email.*to|compose.*message",
                        r"create.*event|schedule.*meeting|book.*appointment",
                        r"upload.*file|save.*document|store.*file",
                        r"send.*sms|text.*message|whatsapp.*message",
                        r"post.*slack|message.*team|notify.*channel",
                        r"create.*card|add.*task|new.*ticket"
                    ],
                    "confidence_boost": 0.2
                },
                {
                    "patterns": [
                        r"execute|run|perform|do|make|send|create|add|update|delete"
                    ],
                    "confidence_boost": 0.1
                }
            ],
            IntentType.CONFIGURATION: [
                {
                    "patterns": [
                        r"configure|setup|connect|integrate|install",
                        r"api.*key|token|credentials|authentication",
                        r"settings|preferences|options|parameters"
                    ],
                    "confidence_boost": 0.2
                }
            ],
            IntentType.WORKFLOW_CREATION: [
                {
                    "patterns": [
                        r"workflow|automation|process|sequence",
                        r"when.*then|if.*then|trigger.*action",
                        r"automate|automatic|auto.*run"
                    ],
                    "confidence_boost": 0.2
                }
            ],
            IntentType.INFORMATION_REQUEST: [
                {
                    "patterns": [
                        r"what.*is|how.*to|can.*you|tell.*me",
                        r"list|show|display|get|fetch|retrieve",
                        r"status|info|information|details"
                    ],
                    "confidence_boost": 0.1
                }
            ],
            IntentType.TROUBLESHOOTING: [
                {
                    "patterns": [
                        r"error|problem|issue|bug|not.*working",
                        r"fix|solve|resolve|debug|troubleshoot",
                        r"failed|broken|wrong|incorrect"
                    ],
                    "confidence_boost": 0.2
                }
            ]
        }
    
    def _initialize_tool_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for tool action recognition."""
        return {
            "gmail": {
                "actions": {
                    "send_email": {
                        "patterns": [r"send.*email", r"email.*to", r"compose.*email"],
                        "required_params": ["to", "subject", "body"],
                        "optional_params": ["cc", "bcc", "attachments"]
                    },
                    "read_emails": {
                        "patterns": [r"read.*email", r"check.*inbox", r"get.*messages"],
                        "required_params": [],
                        "optional_params": ["limit", "unread_only", "from_sender"]
                    }
                }
            },
            "calendar": {
                "actions": {
                    "create_event": {
                        "patterns": [r"create.*event", r"schedule.*meeting", r"book.*appointment"],
                        "required_params": ["title", "start_time", "end_time"],
                        "optional_params": ["description", "attendees", "location"]
                    },
                    "list_events": {
                        "patterns": [r"list.*events", r"show.*calendar", r"check.*schedule"],
                        "required_params": [],
                        "optional_params": ["date_range", "calendar_id"]
                    }
                }
            },
            "slack": {
                "actions": {
                    "send_message": {
                        "patterns": [r"send.*slack", r"message.*team", r"post.*channel"],
                        "required_params": ["channel", "text"],
                        "optional_params": ["thread_ts", "attachments"]
                    }
                }
            },
            "whatsapp": {
                "actions": {
                    "send_message": {
                        "patterns": [r"send.*whatsapp", r"whatsapp.*message"],
                        "required_params": ["phone", "message"],
                        "optional_params": ["media_url", "media_type"]
                    }
                }
            },
            "trello": {
                "actions": {
                    "create_card": {
                        "patterns": [r"create.*card", r"add.*task", r"new.*ticket"],
                        "required_params": ["board_id", "list_id", "name"],
                        "optional_params": ["description", "due_date", "labels"]
                    }
                }
            }
        }
    
    def _initialize_entity_extractors(self) -> Dict[str, Dict[str, Any]]:
        """Initialize entity extraction patterns."""
        return {
            "email": {
                "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "type": "contact"
            },
            "phone": {
                "pattern": r'\+?[\d\s\-\(\)]{10,}',
                "type": "contact"
            },
            "url": {
                "pattern": r'https?://[^\s]+',
                "type": "resource"
            },
            "date": {
                "pattern": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b',
                "type": "temporal"
            },
            "time": {
                "pattern": r'\b\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?\b',
                "type": "temporal"
            },
            "money": {
                "pattern": r'\$\d+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*(?:USD|EUR|GBP)',
                "type": "financial"
            }
        }
    
    def _initialize_workflow_patterns(self) -> Dict[str, List[str]]:
        """Initialize workflow definition patterns."""
        return {
            "trigger_patterns": [
                r"when\s+(.+?)\s+then",
                r"if\s+(.+?)\s+then",
                r"trigger:\s*(.+)",
                r"on\s+(.+?)\s+do"
            ],
            "action_patterns": [
                r"then\s+(.+)",
                r"do\s+(.+)",
                r"action:\s*(.+)",
                r"execute\s+(.+)"
            ],
            "condition_patterns": [
                r"if\s+(.+?)\s+(?:then|do)",
                r"when\s+(.+?)\s+(?:then|do)",
                r"condition:\s*(.+)"
            ]
        }
    
    async def parse_response(self, response_text: str, context: Dict[str, Any] = None) -> ParsedResponse:
        """
        Parse a Gemini response and extract structured information.
        
        Args:
            response_text: The raw response text from Gemini
            context: Optional context information
            
        Returns:
            ParsedResponse: Structured parsed response
        """
        start_time = datetime.utcnow()
        
        try:
            # Parse intent
            intent = await self._parse_intent(response_text, context)
            
            # Parse tool actions
            tool_actions = await self._parse_tool_actions(response_text, context)
            
            # Parse workflows
            workflows = await self._parse_workflows(response_text, context)
            
            # Extract entities and structured data
            extracted_data = await self._extract_entities(response_text)
            
            # Generate suggestions
            suggestions = await self._generate_suggestions(response_text, intent, tool_actions)
            
            # Calculate overall confidence
            confidence = self._calculate_overall_confidence(intent, tool_actions, workflows)
            
            parsing_time = (datetime.utcnow() - start_time).total_seconds()
            
            parsed_response = ParsedResponse(
                original_text=response_text,
                intent=intent,
                tool_actions=tool_actions,
                workflows=workflows,
                extracted_data=extracted_data,
                suggestions=suggestions,
                confidence=confidence,
                parsing_metadata={
                    "parsing_time": parsing_time,
                    "context": context or {},
                    "parser_version": "1.0.0"
                }
            )
            
            logger.info("Parsed Gemini response",
                       intent_type=intent.intent_type.value,
                       tool_actions_count=len(tool_actions),
                       workflows_count=len(workflows),
                       confidence=confidence,
                       parsing_time=parsing_time)
            
            return parsed_response
            
        except Exception as e:
            logger.error("Failed to parse Gemini response", error=str(e))
            
            # Return minimal parsed response on error
            return ParsedResponse(
                original_text=response_text,
                intent=ParsedIntent(
                    intent_type=IntentType.GENERAL_CHAT,
                    confidence=0.0,
                    entities={},
                    context={}
                ),
                tool_actions=[],
                workflows=[],
                extracted_data={},
                suggestions=[],
                confidence=0.0,
                parsing_metadata={"error": str(e)}
            )
    
    async def _parse_intent(self, text: str, context: Dict[str, Any] = None) -> ParsedIntent:
        """Parse user intent from text."""
        text_lower = text.lower()
        intent_scores = {}
        
        # Calculate scores for each intent type
        for intent_type, pattern_groups in self.intent_patterns.items():
            score = 0.0
            
            for pattern_group in pattern_groups:
                for pattern in pattern_group["patterns"]:
                    if re.search(pattern, text_lower):
                        score += pattern_group.get("confidence_boost", 0.1)
            
            intent_scores[intent_type] = min(score, 1.0)
        
        # Find the highest scoring intent
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
        else:
            best_intent = IntentType.GENERAL_CHAT
            confidence = 0.5
        
        # Extract entities relevant to the intent
        entities = await self._extract_intent_entities(text, best_intent)
        
        return ParsedIntent(
            intent_type=best_intent,
            confidence=confidence,
            entities=entities,
            context=context or {}
        )
    
    async def _parse_tool_actions(self, text: str, context: Dict[str, Any] = None) -> List[ParsedToolAction]:
        """Parse tool actions from text."""
        tool_actions = []
        text_lower = text.lower()
        
        # First, check for JSON-formatted tool actions
        json_actions = self._extract_json_tool_actions(text)
        if json_actions:
            for action_data in json_actions:
                validation_errors = self._validate_tool_action(action_data)
                tool_actions.append(ParsedToolAction(
                    tool_name=action_data.get("tool_name", ""),
                    action=action_data.get("action", ""),
                    parameters=action_data.get("parameters", {}),
                    confidence=action_data.get("confidence", 0.9),
                    validation_errors=validation_errors
                ))
        
        # Then, use pattern matching for natural language
        for tool_name, tool_config in self.tool_patterns.items():
            for action_name, action_config in tool_config["actions"].items():
                for pattern in action_config["patterns"]:
                    if re.search(pattern, text_lower):
                        # Extract parameters
                        parameters = await self._extract_action_parameters(
                            text, action_config["required_params"] + action_config["optional_params"]
                        )
                        
                        # Validate parameters
                        validation_errors = []
                        for required_param in action_config["required_params"]:
                            if required_param not in parameters:
                                validation_errors.append(f"Missing required parameter: {required_param}")
                        
                        confidence = 0.8 if not validation_errors else 0.5
                        
                        tool_actions.append(ParsedToolAction(
                            tool_name=tool_name,
                            action=action_name,
                            parameters=parameters,
                            confidence=confidence,
                            validation_errors=validation_errors
                        ))
                        break
        
        return tool_actions
    
    def _extract_json_tool_actions(self, text: str) -> List[Dict[str, Any]]:
        """Extract JSON-formatted tool actions from text."""
        actions = []
        
        # Look for JSON blocks
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        json_matches = re.findall(json_pattern, text, re.DOTALL)
        
        for json_str in json_matches:
            try:
                data = json.loads(json_str)
                if "tool_actions" in data:
                    actions.extend(data["tool_actions"])
                elif "tool_name" in data:  # Single action
                    actions.append(data)
            except json.JSONDecodeError:
                continue
        
        # Also look for inline JSON
        inline_pattern = r'\{[^{}]*"tool_name"[^{}]*\}'
        inline_matches = re.findall(inline_pattern, text)
        
        for json_str in inline_matches:
            try:
                data = json.loads(json_str)
                actions.append(data)
            except json.JSONDecodeError:
                continue
        
        return actions
    
    def _validate_tool_action(self, action_data: Dict[str, Any]) -> List[str]:
        """Validate a tool action data structure."""
        errors = []
        
        if not action_data.get("tool_name"):
            errors.append("Missing tool_name")
        
        if not action_data.get("action"):
            errors.append("Missing action")
        
        tool_name = action_data.get("tool_name")
        action_name = action_data.get("action")
        
        if tool_name in self.tool_patterns:
            tool_config = self.tool_patterns[tool_name]
            if action_name in tool_config["actions"]:
                action_config = tool_config["actions"][action_name]
                parameters = action_data.get("parameters", {})
                
                for required_param in action_config["required_params"]:
                    if required_param not in parameters:
                        errors.append(f"Missing required parameter: {required_param}")
        
        return errors
    
    async def _extract_action_parameters(self, text: str, param_names: List[str]) -> Dict[str, Any]:
        """Extract action parameters from text."""
        parameters = {}
        
        # Extract entities first
        entities = await self._extract_entities(text)
        
        # Map entities to parameters
        for param_name in param_names:
            if param_name in ["to", "email"] and "emails" in entities:
                parameters[param_name] = entities["emails"][0] if entities["emails"] else None
            elif param_name in ["phone", "number"] and "phones" in entities:
                parameters[param_name] = entities["phones"][0] if entities["phones"] else None
            elif param_name in ["url", "link"] and "urls" in entities:
                parameters[param_name] = entities["urls"][0] if entities["urls"] else None
            elif param_name in ["date", "start_date", "end_date"] and "dates" in entities:
                parameters[param_name] = entities["dates"][0] if entities["dates"] else None
            elif param_name in ["time", "start_time", "end_time"] and "times" in entities:
                parameters[param_name] = entities["times"][0] if entities["times"] else None
        
        # Extract specific patterns
        if "subject" in param_names or "title" in param_names:
            subject_pattern = r'(?:subject|title):\s*([^\n]+)'
            subjects = re.findall(subject_pattern, text, re.IGNORECASE)
            if subjects:
                key = "subject" if "subject" in param_names else "title"
                parameters[key] = subjects[0].strip()
        
        if "body" in param_names or "message" in param_names or "text" in param_names:
            # Look for quoted text or text after keywords
            body_patterns = [
                r'(?:body|message|text):\s*"([^"]+)"',
                r'(?:body|message|text):\s*([^\n]+)',
                r'"([^"]+)"'  # Any quoted text
            ]
            
            for pattern in body_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    key = next((p for p in ["body", "message", "text"] if p in param_names), "body")
                    parameters[key] = matches[0].strip()
                    break
        
        return parameters
    
    async def _parse_workflows(self, text: str, context: Dict[str, Any] = None) -> List[ParsedWorkflow]:
        """Parse workflow definitions from text."""
        workflows = []
        
        # Look for workflow indicators
        workflow_indicators = [
            r"workflow|automation|process",
            r"when.*then|if.*then",
            r"trigger.*action"
        ]
        
        has_workflow = any(re.search(pattern, text.lower()) for pattern in workflow_indicators)
        
        if not has_workflow:
            return workflows
        
        # Extract workflow components
        triggers = []
        steps = []
        conditions = []
        
        # Extract triggers
        for pattern in self.workflow_patterns["trigger_patterns"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                triggers.append({"type": "event", "condition": match.strip()})
        
        # Extract actions/steps
        for pattern in self.workflow_patterns["action_patterns"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                steps.append({"type": "action", "description": match.strip()})
        
        # Extract conditions
        for pattern in self.workflow_patterns["condition_patterns"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                conditions.append({"type": "condition", "expression": match.strip()})
        
        if triggers or steps:
            workflows.append(ParsedWorkflow(
                name="Extracted Workflow",
                description="Workflow extracted from user message",
                triggers=triggers,
                steps=steps,
                conditions=conditions,
                confidence=0.7 if triggers and steps else 0.5
            ))
        
        return workflows
    
    async def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text using regex patterns."""
        entities = {}
        
        for entity_name, entity_config in self.entity_extractors.items():
            matches = re.findall(entity_config["pattern"], text)
            if matches:
                entities[f"{entity_name}s"] = matches
        
        return entities
    
    async def _extract_intent_entities(self, text: str, intent_type: IntentType) -> Dict[str, Any]:
        """Extract entities specific to the identified intent."""
        entities = {}
        
        # Get general entities
        general_entities = await self._extract_entities(text)
        entities.update(general_entities)
        
        # Add intent-specific entities
        if intent_type == IntentType.TOOL_EXECUTION:
            # Extract tool names mentioned
            tool_names = []
            for tool_name in self.tool_patterns.keys():
                if tool_name.lower() in text.lower():
                    tool_names.append(tool_name)
            if tool_names:
                entities["mentioned_tools"] = tool_names
        
        elif intent_type == IntentType.CONFIGURATION:
            # Extract configuration-related terms
            config_terms = re.findall(r'\b(?:api|key|token|secret|credential|setting|config)\b', text.lower())
            if config_terms:
                entities["config_terms"] = list(set(config_terms))
        
        return entities
    
    async def _generate_suggestions(self, text: str, intent: ParsedIntent, tool_actions: List[ParsedToolAction]) -> List[str]:
        """Generate helpful suggestions based on parsed content."""
        suggestions = []
        
        # Suggest missing parameters for tool actions
        for action in tool_actions:
            if action.validation_errors:
                suggestions.append(f"To execute {action.tool_name} {action.action}, please provide: {', '.join(action.validation_errors)}")
        
        # Suggest related tools based on intent
        if intent.intent_type == IntentType.TOOL_EXECUTION and not tool_actions:
            suggestions.append("I can help you with various tools like Gmail, Calendar, Slack, WhatsApp, and more. What would you like to do?")
        
        # Suggest workflow creation for complex requests
        if len(tool_actions) > 1:
            suggestions.append("You can create an automated workflow to combine these actions. Would you like me to help set that up?")
        
        return suggestions
    
    def _calculate_overall_confidence(self, intent: ParsedIntent, tool_actions: List[ParsedToolAction], workflows: List[ParsedWorkflow]) -> float:
        """Calculate overall confidence score for the parsed response."""
        scores = [intent.confidence]
        
        if tool_actions:
            action_scores = [action.confidence for action in tool_actions]
            scores.extend(action_scores)
        
        if workflows:
            workflow_scores = [workflow.confidence for workflow in workflows]
            scores.extend(workflow_scores)
        
        return sum(scores) / len(scores) if scores else 0.0


# Global parser instance
gemini_response_parser = GeminiResponseParser()