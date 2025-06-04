#!/usr/bin/env python3
"""
Test script for Gemini integration
Tests the basic functionality of the Gemini chat service and response parser.
"""

import asyncio
import os
import sys
from uuid import uuid4

# Add the core-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core-api'))

from gemini_chat_service import gemini_chat_service
from gemini_response_parser import gemini_response_parser


async def test_gemini_response_parser():
    """Test the Gemini response parser with sample text."""
    print("🧪 Testing Gemini Response Parser...")
    
    test_texts = [
        "Send an email to john@example.com with subject 'Meeting Tomorrow' and body 'Let's meet at 2 PM'",
        "Create a calendar event for tomorrow at 3 PM titled 'Team Meeting'",
        "When a new lead comes in, send them a welcome email and create a Trello card",
        "I need help configuring my Gmail API settings",
        "My Slack integration is not working properly"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- Test {i}: {text[:50]}... ---")
        
        try:
            parsed_response = await gemini_response_parser.parse_response(text)
            
            print(f"Intent: {parsed_response.intent.intent_type.value} (confidence: {parsed_response.intent.confidence:.2f})")
            print(f"Tool Actions: {len(parsed_response.tool_actions)}")
            
            for action in parsed_response.tool_actions:
                print(f"  - {action.tool_name}.{action.action} (confidence: {action.confidence:.2f})")
                if action.validation_errors:
                    print(f"    Errors: {', '.join(action.validation_errors)}")
            
            print(f"Workflows: {len(parsed_response.workflows)}")
            print(f"Suggestions: {len(parsed_response.suggestions)}")
            print(f"Overall Confidence: {parsed_response.confidence:.2f}")
            
        except Exception as e:
            print(f"❌ Error parsing text: {e}")


async def test_gemini_chat_service():
    """Test the Gemini chat service (requires API key)."""
    print("\n🤖 Testing Gemini Chat Service...")
    
    # Check if API key is available
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️  GEMINI_API_KEY not set. Skipping chat service test.")
        print("   Set GEMINI_API_KEY environment variable to test the chat service.")
        return
    
    try:
        # Initialize the service
        print("Initializing Gemini chat service...")
        initialized = await gemini_chat_service.initialize()
        
        if not initialized:
            print("❌ Failed to initialize Gemini chat service")
            return
        
        print("✅ Gemini chat service initialized successfully")
        
        # Start a test session
        user_id = uuid4()
        session_id = await gemini_chat_service.start_chat_session(user_id, "ai_tools_manager")
        print(f"✅ Started chat session: {session_id}")
        
        # Send a test message
        test_message = "Hello! Can you help me send an email?"
        print(f"Sending message: {test_message}")
        
        response = await gemini_chat_service.send_message(session_id, test_message, user_id)
        
        print(f"✅ Received response:")
        print(f"   Text: {response.text[:100]}...")
        print(f"   Tool Actions: {len(response.tool_actions)}")
        print(f"   Confidence: {response.confidence:.2f}")
        print(f"   Processing Time: {response.processing_time:.2f}s")
        
        # Get session history
        history = await gemini_chat_service.get_session_history(session_id)
        print(f"✅ Session history: {len(history)} messages")
        
        # Clear session
        await gemini_chat_service.clear_session(session_id)
        print("✅ Session cleared")
        
    except Exception as e:
        print(f"❌ Error testing chat service: {e}")


async def test_integration():
    """Test the integration between parser and chat service."""
    print("\n🔗 Testing Integration...")
    
    # Test response parsing with chat-like responses
    sample_responses = [
        """I can help you send an email! Here's what I'll do:

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

Would you like me to proceed with sending this email?""",

        """I'll create a workflow for you that automatically handles new leads:

1. **Trigger**: When a new lead is detected
2. **Action 1**: Send welcome email
3. **Action 2**: Create Trello card for follow-up

This will help streamline your lead management process."""
    ]
    
    for i, response_text in enumerate(sample_responses, 1):
        print(f"\n--- Integration Test {i} ---")
        
        try:
            parsed = await gemini_response_parser.parse_response(response_text)
            
            print(f"Parsed {len(parsed.tool_actions)} tool actions")
            print(f"Parsed {len(parsed.workflows)} workflows")
            print(f"Generated {len(parsed.suggestions)} suggestions")
            
            for action in parsed.tool_actions:
                print(f"  Action: {action.tool_name}.{action.action}")
                print(f"  Parameters: {list(action.parameters.keys())}")
                print(f"  Valid: {len(action.validation_errors) == 0}")
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")


def print_summary():
    """Print test summary and next steps."""
    print("\n" + "="*60)
    print("🎉 GEMINI INTEGRATION TEST SUMMARY")
    print("="*60)
    print()
    print("✅ Components tested:")
    print("   - Gemini Response Parser")
    print("   - Gemini Chat Service (if API key available)")
    print("   - Integration between components")
    print()
    print("🚀 Next steps:")
    print("   1. Set GEMINI_API_KEY environment variable")
    print("   2. Start the core-api server: uvicorn main:app --reload")
    print("   3. Open the dashboard and navigate to 'Gemini Chat' tab")
    print("   4. Test the chat interface with real Gemini API")
    print()
    print("📝 API Endpoints available:")
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
    
    # Test response parser (doesn't require API key)
    await test_gemini_response_parser()
    
    # Test chat service (requires API key)
    await test_gemini_chat_service()
    
    # Test integration
    await test_integration()
    
    # Print summary
    print_summary()


if __name__ == "__main__":
    asyncio.run(main())