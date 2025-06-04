"""
Gemini Chat Service for AI Agent Tools Management
Specialized system prompt for creating, editing, deleting, and connecting AI tools
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class GeminiChatService:
    """
    Gemini AI service specialized for AI agent tools management
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
        # Specialized system prompt for AI tools management
        self.system_prompt = """
You are an AI assistant specialized in managing call center AI tools and automation workflows. Your role is to help users:

1. CREATE new AI tools and workflows
2. EDIT existing tool configurations  
3. DELETE unused tools
4. CONNECT tools to create automation chains
5. ANALYZE business needs and suggest relevant tools

Available Tools:
- Call Automation: Automated calling workflows
- SMS Campaigns: Bulk SMS management  
- Analytics: Performance tracking
- Lead Scoring: AI-powered lead qualification
- Appointment Booking: Automated scheduling
- Follow-up: Customer follow-up automation

When users request tool operations, respond with:
1. Clear explanation of what you're doing
2. Specific tool configurations
3. Connection details between tools
4. Expected outcomes and benefits

Always be helpful, specific, and focused on practical call center automation solutions.
"""
        
        self.conversation_history = []
        
    def send_message(self, message: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Send a message to Gemini with specialized AI tools context
        """
        try:
            if not self.api_key:
                return self._demo_response(message)
            
            # Prepare the conversation context
            full_prompt = f"{self.system_prompt}\n\nUser: {message}"
            
            # Add user context if provided
            if user_context:
                context_str = f"User Context: {json.dumps(user_context, indent=2)}"
                full_prompt = f"{self.system_prompt}\n\n{context_str}\n\nUser: {message}"
            
            # Prepare request payload
            payload = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            # Make API request
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if 'candidates' in result and len(result['candidates']) > 0:
                    gemini_response = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Store conversation history
                    self.conversation_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'user_message': message,
                        'gemini_response': gemini_response,
                        'user_context': user_context
                    })
                    
                    return {
                        'success': True,
                        'response': gemini_response,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    logger.error(f"No candidates in Gemini response: {result}")
                    return self._demo_response(message)
            else:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return self._demo_response(message)
                
        except Exception as e:
            logger.error(f"Gemini chat service error: {e}")
            return self._demo_response(message)
    
    def _demo_response(self, message: str) -> Dict[str, Any]:
        """
        Generate a demo response when Gemini API is not available
        """
        message_lower = message.lower()
        
        # Analyze the message and provide contextual demo responses
        if 'connect' in message_lower and 'lead scoring' in message_lower and 'appointment' in message_lower:
            response = """✅ **Tool Connection Created: Lead Scoring → Appointment Booking**

I've created an automation chain that connects your Lead Scoring tool to Appointment Booking:

**Configuration:**
- **Trigger**: When lead score ≥ 80 (high-quality lead)
- **Action**: Automatically schedule appointment
- **Timing**: Within 5 minutes of scoring
- **Notification**: Send SMS confirmation to lead

**Benefits:**
- 🎯 Only high-quality leads get immediate booking
- ⚡ Faster response time increases conversion
- 🤖 Reduces manual work for your team
- 📊 Better tracking of lead-to-appointment conversion

**Next Steps:**
- Test the connection with a sample lead
- Adjust scoring threshold if needed
- Set up follow-up sequences for lower-scored leads

Would you like me to create additional connections or modify this workflow?"""

        elif 'create' in message_lower and 'tool' in message_lower:
            response = """🛠️ **Creating New AI Tool**

I can help you create a custom AI tool for your call center. Here are some popular options:

**Available Tool Templates:**
1. **Voice Analytics** - Analyze call sentiment and keywords
2. **Customer Segmentation** - Automatically categorize customers
3. **Callback Scheduler** - Smart callback timing optimization
4. **Script Generator** - Dynamic call scripts based on customer data
5. **Quality Assurance** - Automated call quality scoring

**To create a tool, please specify:**
- Tool purpose and functionality
- Input data sources
- Expected outputs
- Integration requirements

What type of tool would you like to create?"""

        elif 'edit' in message_lower or 'modify' in message_lower:
            response = """✏️ **Tool Configuration Editor**

I can help you modify existing tools. Here's what I can edit:

**Editable Parameters:**
- Trigger conditions and thresholds
- Automation timing and schedules
- Notification settings
- Data processing rules
- Integration endpoints

**Current Tools Available for Editing:**
- Call Automation (Active)
- SMS Campaigns (Active) 
- Analytics (Active)
- Lead Scoring (Active)
- Appointment Booking (Active)
- Follow-up (Active)

Which tool would you like to modify and what changes do you need?"""

        elif 'delete' in message_lower:
            response = """🗑️ **Tool Deletion Manager**

I can help you safely remove unused tools. Before deletion, I'll:

**Safety Checks:**
- Verify tool is not actively used
- Check for dependent connections
- Backup current configurations
- Confirm deletion with you

**Currently Deletable Tools:**
- Unused workflow templates
- Inactive automation rules
- Disconnected integrations

Which tool would you like to remove? I'll perform safety checks first."""

        elif 'analyze' in message_lower or 'suggest' in message_lower:
            response = """📊 **Business Analysis & Tool Suggestions**

Based on typical call center needs, here are my recommendations:

**High-Impact Tool Combinations:**
1. **Lead Nurturing Chain**: Lead Scoring → SMS Campaigns → Follow-up
2. **Appointment Optimization**: Analytics → Appointment Booking → Follow-up
3. **Quality Improvement**: Call Automation → Analytics → Follow-up

**Suggested Next Steps:**
- Connect your highest-performing tools
- Set up automated follow-up sequences
- Implement lead scoring for better targeting
- Add analytics to track performance

What's your primary business goal? I can suggest specific tool configurations."""

        else:
            response = """🤖 **AI Tools Assistant Ready**

I'm here to help you manage your call center AI tools! I can:

**Tool Management:**
- ✨ Create new tools and workflows
- ✏️ Edit existing configurations
- 🗑️ Delete unused tools
- 🔗 Connect tools for automation
- 📊 Analyze and suggest improvements

**Quick Actions:**
- "Connect lead scoring to SMS campaigns"
- "Create a callback scheduling tool"
- "Edit appointment booking settings"
- "Delete unused analytics rules"
- "Suggest tools for lead nurturing"

What would you like to do with your AI tools today?"""

        return {
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'demo_mode': True
        }
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_tool_suggestions(self, business_type: str = "call_center") -> List[Dict]:
        """Get AI tool suggestions based on business type"""
        suggestions = [
            {
                "name": "Smart Lead Scoring",
                "description": "AI-powered lead qualification and prioritization",
                "category": "Lead Management",
                "benefits": ["Higher conversion rates", "Better resource allocation", "Automated prioritization"]
            },
            {
                "name": "Intelligent Call Routing",
                "description": "Route calls to best-suited agents based on skills and availability",
                "category": "Call Management", 
                "benefits": ["Reduced wait times", "Better customer satisfaction", "Optimized agent utilization"]
            },
            {
                "name": "Automated Follow-up Sequences",
                "description": "Smart follow-up campaigns based on customer behavior",
                "category": "Customer Retention",
                "benefits": ["Increased retention", "Automated nurturing", "Personalized communication"]
            },
            {
                "name": "Real-time Analytics Dashboard",
                "description": "Live performance monitoring and insights",
                "category": "Analytics",
                "benefits": ["Data-driven decisions", "Performance optimization", "Trend identification"]
            }
        ]
        
        return suggestions