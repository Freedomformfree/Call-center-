# AI Agent Tools Architecture & System Prompt Chaining

## 🏗️ Architecture Overview

Yes, the AI agent tools in this system follow a structured architecture where each tool and context has its own specialized system prompt that gets combined with the main prompt. Here's how it works:

## 📋 System Prompt Structure

### 1. **Hierarchical Prompt System**

```
Main System Prompt (Base)
├── Context-Specific Prompt (ai_tools_manager, workflow_builder, troubleshooter)
├── Tool-Specific Prompts (gmail, calendar, slack, etc.)
└── Chain-Specific Instructions (when tools are connected)
```

### 2. **Context-Based System Prompts**

Each chat context has its own specialized system prompt:

#### **AI Tools Manager Context**
```
You are an AI Tools Manager assistant specialized in helping users configure, 
manage, and execute various business automation tools. Your expertise includes:

1. **Tool Configuration**: Gmail, Calendar, Slack, WhatsApp, Trello, etc.
2. **API Integration**: OAuth flows, API key management, webhook setup
3. **Action Execution**: Email sending, calendar events, file management
4. **Troubleshooting**: Connection issues, authentication problems
5. **Best Practices**: Security and efficiency recommendations
```

#### **Workflow Builder Context**
```
You are a Workflow Builder assistant specialized in creating automated 
business processes and tool chains. Your expertise includes:

1. **Process Design**: Multi-step workflow creation
2. **Tool Chaining**: Connecting multiple tools in sequence
3. **Trigger Management**: Event-based automation setup
4. **Conditional Logic**: If-then-else workflow branches
5. **Optimization**: Performance and reliability improvements
```

#### **Troubleshooter Context**
```
You are a Technical Troubleshooter assistant specialized in diagnosing 
and resolving integration issues. Your expertise includes:

1. **Error Diagnosis**: API errors, authentication failures
2. **Performance Issues**: Slow responses, timeout problems
3. **Configuration Problems**: Incorrect settings, missing permissions
4. **Integration Conflicts**: Tool compatibility issues
5. **Resolution Guidance**: Step-by-step problem solving
```

## 🔗 Tool Chaining Architecture

### **Chain Definition Structure**

```json
{
  "chain_id": "lead_processing_chain",
  "name": "Lead Processing Automation",
  "description": "Automatically process new leads through multiple tools",
  "tools": [
    {
      "tool": "gmail",
      "action": "send_welcome_email",
      "order": 1,
      "conditions": ["lead.email_exists"],
      "system_prompt_addition": "When sending welcome emails, use professional tone and include company branding."
    },
    {
      "tool": "trello",
      "action": "create_lead_card",
      "order": 2,
      "conditions": ["email_sent_successfully"],
      "system_prompt_addition": "Create Trello cards with detailed lead information and set appropriate due dates."
    },
    {
      "tool": "slack",
      "action": "notify_sales_team",
      "order": 3,
      "conditions": ["card_created_successfully"],
      "system_prompt_addition": "Send concise Slack notifications with lead priority and next action items."
    }
  ]
}
```

### **Dynamic Prompt Composition**

When a chain is executed, the system dynamically composes prompts:

```python
def compose_chain_prompt(base_context: str, chain_config: dict) -> str:
    """Compose system prompt for tool chain execution."""
    
    # Start with base context prompt
    prompt_parts = [CONTEXT_PROMPTS[base_context]]
    
    # Add chain-specific instructions
    prompt_parts.append(f"""
    You are now executing a tool chain: {chain_config['name']}
    Description: {chain_config['description']}
    
    Chain execution rules:
    1. Execute tools in the specified order
    2. Check conditions before each step
    3. Handle errors gracefully and provide alternatives
    4. Maintain context between tool executions
    5. Provide clear status updates for each step
    """)
    
    # Add tool-specific prompt additions
    for tool_config in chain_config['tools']:
        if 'system_prompt_addition' in tool_config:
            prompt_parts.append(f"""
            For {tool_config['tool']} ({tool_config['action']}):
            {tool_config['system_prompt_addition']}
            """)
    
    return "\n\n".join(prompt_parts)
```

## 🛠️ Tool-Specific System Prompts

### **Gmail Tool Prompt**
```
Gmail Integration Instructions:
- Always validate email addresses before sending
- Use appropriate subject lines based on context
- Include unsubscribe links for marketing emails
- Handle attachments securely
- Respect rate limits (250 emails/day for free accounts)
- Use HTML formatting for professional emails
```

### **Calendar Tool Prompt**
```
Calendar Integration Instructions:
- Always specify timezone for events
- Include meeting links for virtual meetings
- Set appropriate reminders (15 min, 1 hour, 1 day)
- Check for conflicts before creating events
- Use descriptive titles and detailed descriptions
- Handle recurring events properly
```

### **Slack Tool Prompt**
```
Slack Integration Instructions:
- Use appropriate channels for different message types
- Format messages with proper markdown
- Include relevant mentions (@user, @channel)
- Use threads for follow-up discussions
- Respect workspace etiquette and guidelines
- Handle file uploads and link previews
```

## 🔄 Chain Execution Flow

### **1. Chain Initialization**
```python
async def initialize_chain(chain_config: dict, user_context: dict):
    """Initialize a tool chain with composed system prompt."""
    
    # Compose the full system prompt
    system_prompt = compose_chain_prompt(
        base_context=user_context.get('context', 'ai_tools_manager'),
        chain_config=chain_config
    )
    
    # Initialize AI model with composed prompt
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=system_prompt
    )
    
    return ChainExecutor(model, chain_config)
```

### **2. Step-by-Step Execution**
```python
async def execute_chain_step(step: dict, previous_results: list):
    """Execute a single step in the tool chain."""
    
    # Add step-specific context to prompt
    step_context = f"""
    Current step: {step['order']} of {len(chain_config['tools'])}
    Tool: {step['tool']}
    Action: {step['action']}
    Previous results: {json.dumps(previous_results, indent=2)}
    
    Execute this step and provide structured output with:
    1. Execution status (success/failure/partial)
    2. Results data
    3. Any errors or warnings
    4. Next step recommendations
    """
    
    # Send to AI with step context
    response = await model.generate_content(step_context)
    
    # Parse and validate response
    return parse_step_response(response.text)
```

## 📊 Prompt Composition Examples

### **Example 1: Simple Email Chain**
```
Base Context: AI Tools Manager
+ Tool Chain: "Customer Onboarding"
+ Gmail Prompt: "Send welcome emails with company branding"
+ Trello Prompt: "Create onboarding checklist cards"

Final Composed Prompt:
"You are an AI Tools Manager assistant... [base prompt]

You are now executing a tool chain: Customer Onboarding
Description: Automate new customer welcome process

For gmail (send_welcome_email):
Send welcome emails with company branding and include onboarding checklist

For trello (create_onboarding_card):
Create detailed onboarding checklist with due dates and assignments"
```

### **Example 2: Complex Workflow Chain**
```
Base Context: Workflow Builder
+ Tool Chain: "Lead Qualification Pipeline"
+ Multiple Tools: Gmail → HubSpot → Slack → Calendar
+ Conditional Logic: If lead score > 80, schedule call

Final Composed Prompt:
"You are a Workflow Builder assistant... [base prompt]

You are executing a complex workflow: Lead Qualification Pipeline
This workflow includes conditional logic and multiple tool integrations.

Execution flow:
1. Gmail: Send qualification questionnaire
2. HubSpot: Update lead score based on responses
3. Conditional: If score > 80, proceed to steps 4-5
4. Slack: Notify sales team of qualified lead
5. Calendar: Schedule qualification call

Handle each step with appropriate error checking and provide alternatives for failed conditions."
```

## 🎯 Advanced Features

### **1. Dynamic Prompt Injection**
```python
class DynamicPromptInjector:
    """Inject context-specific prompts based on user data and tool state."""
    
    def inject_user_context(self, base_prompt: str, user: User) -> str:
        """Inject user-specific context into prompt."""
        user_tools = get_user_configured_tools(user.id)
        user_preferences = get_user_preferences(user.id)
        
        context_injection = f"""
        User Context:
        - Configured tools: {', '.join(user_tools)}
        - Timezone: {user_preferences.get('timezone', 'UTC')}
        - Language: {user_preferences.get('language', 'en')}
        - Business type: {user_preferences.get('business_type', 'general')}
        
        Adapt your responses to this user's specific setup and preferences.
        """
        
        return base_prompt + "\n\n" + context_injection
```

### **2. Tool State Awareness**
```python
def inject_tool_state(prompt: str, tool_states: dict) -> str:
    """Inject current tool states into prompt."""
    
    state_info = []
    for tool, state in tool_states.items():
        if state['connected']:
            state_info.append(f"- {tool}: Connected, last used {state['last_used']}")
        else:
            state_info.append(f"- {tool}: Disconnected, error: {state['error']}")
    
    state_injection = f"""
    Current Tool States:
    {chr(10).join(state_info)}
    
    Consider these states when suggesting actions or troubleshooting.
    """
    
    return prompt + "\n\n" + state_injection
```

### **3. Learning from Interactions**
```python
class PromptLearningSystem:
    """Learn from user interactions to improve prompt effectiveness."""
    
    def analyze_interaction_success(self, prompt: str, user_message: str, 
                                  ai_response: str, user_feedback: dict):
        """Analyze interaction success and suggest prompt improvements."""
        
        success_metrics = {
            'task_completed': user_feedback.get('task_completed', False),
            'response_helpful': user_feedback.get('helpful', 0),  # 1-5 scale
            'follow_up_needed': user_feedback.get('follow_up_needed', False)
        }
        
        # Store interaction data for prompt optimization
        self.store_interaction_data({
            'prompt_hash': hash(prompt),
            'user_intent': classify_intent(user_message),
            'ai_actions': extract_actions(ai_response),
            'success_metrics': success_metrics,
            'timestamp': datetime.utcnow()
        })
        
        # Suggest prompt improvements based on patterns
        return self.suggest_prompt_improvements(prompt, success_metrics)
```

## 🔧 Implementation Best Practices

### **1. Modular Prompt Design**
- Keep base prompts focused and clear
- Make tool-specific additions concise
- Use consistent formatting across all prompts
- Include error handling instructions

### **2. Chain Validation**
- Validate tool compatibility before execution
- Check user permissions for each tool
- Verify required parameters are available
- Test chain logic with dry runs

### **3. Performance Optimization**
- Cache composed prompts for repeated chains
- Use prompt compression for long chains
- Implement prompt versioning for A/B testing
- Monitor token usage and optimize accordingly

### **4. Error Handling**
- Include fallback instructions in prompts
- Provide clear error messages and recovery steps
- Log prompt composition for debugging
- Implement graceful degradation for failed tools

## 📈 Monitoring & Analytics

### **Chain Performance Metrics**
```python
class ChainAnalytics:
    """Monitor and analyze tool chain performance."""
    
    def track_chain_execution(self, chain_id: str, execution_data: dict):
        """Track chain execution metrics."""
        metrics = {
            'chain_id': chain_id,
            'execution_time': execution_data['duration'],
            'steps_completed': execution_data['completed_steps'],
            'steps_failed': execution_data['failed_steps'],
            'success_rate': execution_data['success_rate'],
            'user_satisfaction': execution_data.get('user_rating', None),
            'prompt_tokens_used': execution_data['token_usage'],
            'timestamp': datetime.utcnow()
        }
        
        self.store_metrics(metrics)
        return self.generate_insights(chain_id)
```

## 🚀 Future Enhancements

### **1. AI-Generated Prompts**
- Use AI to generate optimal prompts for new tool combinations
- Automatically adapt prompts based on user success patterns
- Create personalized prompt variations for different user types

### **2. Visual Prompt Builder**
- Drag-and-drop interface for creating tool chains
- Visual prompt composition with real-time preview
- Template library for common business processes

### **3. Multi-Language Support**
- Translate system prompts to user's preferred language
- Maintain context and technical accuracy across languages
- Support for region-specific business practices

This architecture provides a flexible, scalable foundation for AI agent tools that can be easily extended and customized for different business needs while maintaining consistency and reliability across all integrations.