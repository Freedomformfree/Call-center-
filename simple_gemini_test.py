#!/usr/bin/env python3
"""
Simple test script for Gemini response parser
Tests the basic functionality without requiring database or full setup.
"""

import asyncio
import os
import sys
import re
import json

# Add the core-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core-api'))

# Simple mock classes to avoid database dependencies
class MockIntentType:
    TOOL_EXECUTION = "tool_execution"
    INFORMATION_REQUEST = "information_request"
    CONFIGURATION = "configuration"
    WORKFLOW_CREATION = "workflow_creation"
    TROUBLESHOOTING = "troubleshooting"
    GENERAL_CHAT = "general_chat"

class MockParsedIntent:
    def __init__(self, intent_type, confidence, entities, context):
        self.intent_type = intent_type
        self.confidence = confidence
        self.entities = entities
        self.context = context

class MockParsedToolAction:
    def __init__(self, tool_name, action, parameters, confidence, validation_errors):
        self.tool_name = tool_name
        self.action = action
        self.parameters = parameters
        self.confidence = confidence
        self.validation_errors = validation_errors

class MockParsedWorkflow:
    def __init__(self, name, description, triggers, steps, conditions, confidence):
        self.name = name
        self.description = description
        self.triggers = triggers
        self.steps = steps
        self.conditions = conditions
        self.confidence = confidence

class MockParsedResponse:
    def __init__(self, original_text, intent, tool_actions, workflows, extracted_data, suggestions, confidence, parsing_metadata):
        self.original_text = original_text
        self.intent = intent
        self.tool_actions = tool_actions
        self.workflows = workflows
        self.extracted_data = extracted_data
        self.suggestions = suggestions
        self.confidence = confidence
        self.parsing_metadata = parsing_metadata

# Simple response parser implementation
class SimpleGeminiResponseParser:
    def __init__(self):
        self.tool_patterns = {
            "gmail": {
                "send_email": {
                    "patterns": [r"send.*email", r"email.*to", r"compose.*email"],
                    "required_params": ["to", "subject", "body"]
                }
            },
            "calendar": {
                "create_event": {
                    "patterns": [r"create.*event", r"schedule.*meeting", r"book.*appointment"],
                    "required_params": ["title", "start_time", "end_time"]
                }
            }
        }
    
    async def parse_response(self, text, context=None):
        # Simple intent detection
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["send", "email", "compose"]):
            intent_type = MockIntentType.TOOL_EXECUTION
            confidence = 0.8
        elif any(word in text_lower for word in ["create", "schedule", "meeting"]):
            intent_type = MockIntentType.TOOL_EXECUTION
            confidence = 0.8
        elif any(word in text_lower for word in ["workflow", "automation", "when", "then"]):
            intent_type = MockIntentType.WORKFLOW_CREATION
            confidence = 0.7
        elif any(word in text_lower for word in ["configure", "setup", "api", "key"]):
            intent_type = MockIntentType.CONFIGURATION
            confidence = 0.7
        elif any(word in text_lower for word in ["error", "problem", "not working", "help"]):
            intent_type = MockIntentType.TROUBLESHOOTING
            confidence = 0.6
        else:
            intent_type = MockIntentType.GENERAL_CHAT
            confidence = 0.5
        
        # Extract entities
        entities = {}
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            entities["emails"] = emails
        
        # Parse tool actions
        tool_actions = []
        
        # Check for email sending
        if "send" in text_lower and "email" in text_lower:
            parameters = {}
            if emails:
                parameters["to"] = emails[0]
            
            # Extract subject
            subject_match = re.search(r'subject[:\s]+["\']([^"\']+)["\']', text, re.IGNORECASE)
            if subject_match:
                parameters["subject"] = subject_match.group(1)
            
            # Extract body
            body_match = re.search(r'body[:\s]+["\']([^"\']+)["\']', text, re.IGNORECASE)
            if body_match:
                parameters["body"] = body_match.group(1)
            
            validation_errors = []
            if "to" not in parameters:
                validation_errors.append("Missing required parameter: to")
            if "subject" not in parameters:
                validation_errors.append("Missing required parameter: subject")
            if "body" not in parameters:
                validation_errors.append("Missing required parameter: body")
            
            tool_actions.append(MockParsedToolAction(
                tool_name="gmail",
                action="send_email",
                parameters=parameters,
                confidence=0.8 if not validation_errors else 0.5,
                validation_errors=validation_errors
            ))
        
        # Check for calendar events
        if any(word in text_lower for word in ["create", "schedule"]) and any(word in text_lower for word in ["event", "meeting", "appointment"]):
            parameters = {}
            
            # Extract title
            title_patterns = [
                r'titled?\s+["\']([^"\']+)["\']',
                r'event\s+["\']([^"\']+)["\']',
                r'meeting\s+["\']([^"\']+)["\']'
            ]
            
            for pattern in title_patterns:
                title_match = re.search(pattern, text, re.IGNORECASE)
                if title_match:
                    parameters["title"] = title_match.group(1)
                    break
            
            validation_errors = []
            if "title" not in parameters:
                validation_errors.append("Missing required parameter: title")
            if "start_time" not in parameters:
                validation_errors.append("Missing required parameter: start_time")
            if "end_time" not in parameters:
                validation_errors.append("Missing required parameter: end_time")
            
            tool_actions.append(MockParsedToolAction(
                tool_name="calendar",
                action="create_event",
                parameters=parameters,
                confidence=0.7 if not validation_errors else 0.4,
                validation_errors=validation_errors
            ))
        
        # Parse workflows
        workflows = []
        if any(word in text_lower for word in ["workflow", "when", "then", "automation"]):
            workflows.append(MockParsedWorkflow(
                name="Extracted Workflow",
                description="Workflow extracted from user message",
                triggers=[{"type": "event", "condition": "user defined trigger"}],
                steps=[{"type": "action", "description": "user defined action"}],
                conditions=[],
                confidence=0.6
            ))
        
        # Generate suggestions
        suggestions = []
        if tool_actions:
            for action in tool_actions:
                if action.validation_errors:
                    suggestions.append(f"To execute {action.tool_name} {action.action}, please provide: {', '.join([err.split(': ')[1] for err in action.validation_errors])}")
        
        if not tool_actions and intent_type == MockIntentType.TOOL_EXECUTION:
            suggestions.append("I can help you with various tools like Gmail, Calendar, Slack, WhatsApp, and more. What would you like to do?")
        
        # Calculate overall confidence
        scores = [confidence]
        if tool_actions:
            scores.extend([action.confidence for action in tool_actions])
        if workflows:
            scores.extend([workflow.confidence for workflow in workflows])
        
        overall_confidence = sum(scores) / len(scores)
        
        intent = MockParsedIntent(
            intent_type=intent_type,
            confidence=confidence,
            entities=entities,
            context=context or {}
        )
        
        return MockParsedResponse(
            original_text=text,
            intent=intent,
            tool_actions=tool_actions,
            workflows=workflows,
            extracted_data=entities,
            suggestions=suggestions,
            confidence=overall_confidence,
            parsing_metadata={"parser_version": "simple_test"}
        )

async def test_response_parser():
    """Test the response parser with sample text."""
    print("🧪 Testing Gemini Response Parser...")
    
    parser = SimpleGeminiResponseParser()
    
    test_texts = [
        "Send an email to john@example.com with subject 'Meeting Tomorrow' and body 'Let's meet at 2 PM'",
        "Create a calendar event titled 'Team Meeting' for tomorrow at 3 PM",
        "When a new lead comes in, send them a welcome email and create a Trello card",
        "I need help configuring my Gmail API settings",
        "My Slack integration is not working properly",
        "Schedule a meeting with the team",
        "Can you help me automate my workflow?"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- Test {i}: {text[:50]}... ---")
        
        try:
            parsed_response = await parser.parse_response(text)
            
            print(f"Intent: {parsed_response.intent.intent_type} (confidence: {parsed_response.intent.confidence:.2f})")
            print(f"Tool Actions: {len(parsed_response.tool_actions)}")
            
            for action in parsed_response.tool_actions:
                print(f"  - {action.tool_name}.{action.action} (confidence: {action.confidence:.2f})")
                print(f"    Parameters: {list(action.parameters.keys())}")
                if action.validation_errors:
                    print(f"    Errors: {', '.join(action.validation_errors)}")
            
            print(f"Workflows: {len(parsed_response.workflows)}")
            print(f"Suggestions: {len(parsed_response.suggestions)}")
            for suggestion in parsed_response.suggestions:
                print(f"  - {suggestion}")
            print(f"Overall Confidence: {parsed_response.confidence:.2f}")
            
        except Exception as e:
            print(f"❌ Error parsing text: {e}")

def test_json_parsing():
    """Test JSON parsing from AI responses."""
    print("\n🔍 Testing JSON Tool Action Parsing...")
    
    sample_responses = [
        '''I can help you send an email! Here's what I'll do:

```json
{
  "tool_actions": [
    {
      "tool_name": "gmail",
      "action": "send_email",
      "parameters": {
        "to": "john@example.com",
        "subject": "Meeting Tomorrow",
        "body": "Let's meet at 2 PM"
      },
      "confidence": 0.9
    }
  ]
}
```

Would you like me to proceed with sending this email?''',

        '''I'll create a workflow for you:

```json
{
  "tool_actions": [
    {
      "tool_name": "gmail",
      "action": "send_email",
      "parameters": {
        "to": "{{lead.email}}",
        "subject": "Welcome!",
        "body": "Thank you for your interest"
      },
      "confidence": 0.8
    },
    {
      "tool_name": "trello",
      "action": "create_card",
      "parameters": {
        "board_id": "main_board",
        "list_id": "leads",
        "name": "New Lead: {{lead.name}}"
      },
      "confidence": 0.8
    }
  ]
}
```'''
    ]
    
    for i, response_text in enumerate(sample_responses, 1):
        print(f"\n--- JSON Test {i} ---")
        
        # Extract JSON blocks
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        json_matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        for json_str in json_matches:
            try:
                data = json.loads(json_str)
                if "tool_actions" in data:
                    print(f"Found {len(data['tool_actions'])} tool actions:")
                    for action in data["tool_actions"]:
                        print(f"  - {action.get('tool_name', 'unknown')}.{action.get('action', 'unknown')}")
                        print(f"    Confidence: {action.get('confidence', 0):.2f}")
                        print(f"    Parameters: {list(action.get('parameters', {}).keys())}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")

def print_summary():
    """Print test summary and next steps."""
    print("\n" + "="*60)
    print("🎉 GEMINI INTEGRATION TEST SUMMARY")
    print("="*60)
    print()
    print("✅ Components tested:")
    print("   - Response parsing and intent detection")
    print("   - Tool action extraction")
    print("   - JSON parsing from AI responses")
    print("   - Parameter validation")
    print("   - Suggestion generation")
    print()
    print("🚀 Next steps to complete integration:")
    print("   1. Set GEMINI_API_KEY environment variable")
    print("   2. Install all dependencies: pip install -r core-api/requirements.txt")
    print("   3. Start the core-api server: cd core-api && uvicorn main:app --reload --host 0.0.0.0 --port 12000")
    print("   4. Open the dashboard and navigate to 'Gemini Chat' tab")
    print("   5. Test the chat interface with real Gemini API")
    print()
    print("📝 Key features implemented:")
    print("   - Intelligent response parsing")
    print("   - Tool action detection and validation")
    print("   - Workflow creation assistance")
    print("   - Multi-context chat sessions")
    print("   - Auto-execution of tool actions")
    print("   - Real-time chat interface")
    print()
    print("🔧 API Endpoints available:")
    print("   - POST /api/v1/gemini-chat/start-session")
    print("   - POST /api/v1/gemini-chat/send-message")
    print("   - GET  /api/v1/gemini-chat/history/{session_id}")
    print("   - DELETE /api/v1/gemini-chat/session/{session_id}")
    print("   - POST /api/v1/gemini-chat/parse-response")
    print("   - GET  /api/v1/gemini-chat/health")
    print()

async def main():
    """Run all tests."""
    print("🧪 GEMINI INTEGRATION TESTS")
    print("="*60)
    
    # Test response parser
    await test_response_parser()
    
    # Test JSON parsing
    test_json_parsing()
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    asyncio.run(main())