/**
 * Gemini Chat Interface - Frontend JavaScript
 * 
 * Handles the Gemini AI chat interface including session management,
 * message sending, tool action display, and real-time updates.
 */

class GeminiChatInterface {
    constructor() {
        this.currentSessionId = null;
        this.messageCount = 0;
        this.isLoading = false;
        this.apiBaseUrl = '/api/v1/gemini-chat';
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }
    
    initialize() {
        this.setupEventListeners();
        this.updateSessionInfo();
        
        // Auto-start session when chat tab is opened
        this.checkAndStartSession();
    }
    
    setupEventListeners() {
        // Chat input keydown handler
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => this.handleChatKeydown(e));
            chatInput.addEventListener('input', () => this.adjustTextareaHeight());
        }
        
        // Send button
        const sendButton = document.getElementById('sendButton');
        if (sendButton) {
            sendButton.addEventListener('click', () => this.sendChatMessage());
        }
        
        // Context change
        const contextSelect = document.getElementById('chatContext');
        if (contextSelect) {
            contextSelect.addEventListener('change', () => this.handleContextChange());
        }
        
        // Navigation to chat section
        const chatNavItem = document.querySelector('[data-section="gemini-chat"]');
        if (chatNavItem) {
            chatNavItem.addEventListener('click', () => this.onChatSectionOpen());
        }
    }
    
    adjustTextareaHeight() {
        const textarea = document.getElementById('chatInput');
        if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        }
    }
    
    handleChatKeydown(event) {
        if (event.ctrlKey && event.key === 'Enter') {
            event.preventDefault();
            this.sendChatMessage();
        }
    }
    
    onChatSectionOpen() {
        // Check if we need to start a session
        this.checkAndStartSession();
    }
    
    async checkAndStartSession() {
        if (!this.currentSessionId) {
            await this.startNewChatSession();
        }
    }
    
    async startNewChatSession() {
        try {
            const context = document.getElementById('chatContext')?.value || 'ai_tools_manager';
            
            this.showLoading('Starting new chat session...');
            
            const response = await fetch(`${this.apiBaseUrl}/start-session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({ context })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.currentSessionId = data.session_id;
                this.messageCount = 0;
                this.updateSessionInfo();
                this.clearChatMessages();
                this.showWelcomeMessage();
                this.showSuccess('New chat session started successfully!');
            } else {
                throw new Error(data.message || 'Failed to start session');
            }
            
        } catch (error) {
            console.error('Failed to start chat session:', error);
            this.showError(`Failed to start chat session: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    async sendChatMessage() {
        const input = document.getElementById('chatInput');
        const message = input?.value?.trim();
        
        if (!message || this.isLoading) {
            return;
        }
        
        if (!this.currentSessionId) {
            await this.startNewChatSession();
            if (!this.currentSessionId) {
                return;
            }
        }
        
        try {
            // Clear input and show user message
            input.value = '';
            this.adjustTextareaHeight();
            this.addMessageToChat('user', message);
            
            // Show loading indicator
            this.showTypingIndicator();
            this.isLoading = true;
            this.updateSendButton(true);
            
            const autoExecute = document.getElementById('autoExecuteTools')?.checked || false;
            
            const response = await fetch(`${this.apiBaseUrl}/send-message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    message: message,
                    auto_execute_tools: autoExecute
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Remove typing indicator
                this.hideTypingIndicator();
                
                // Add assistant response
                this.addMessageToChat('assistant', data.response);
                
                // Show tool actions if any
                if (data.tool_actions && data.tool_actions.length > 0) {
                    this.displayToolActions(data.tool_actions, data.executed_actions);
                }
                
                // Show suggestions if any
                if (data.suggestions && data.suggestions.length > 0) {
                    this.displaySuggestions(data.suggestions);
                }
                
                this.messageCount += 2; // User + assistant message
                this.updateSessionInfo();
                
            } else {
                throw new Error(data.message || 'Failed to send message');
            }
            
        } catch (error) {
            console.error('Failed to send message:', error);
            this.hideTypingIndicator();
            this.addMessageToChat('assistant', `I apologize, but I encountered an error: ${error.message}`);
            this.showError(`Failed to send message: ${error.message}`);
        } finally {
            this.isLoading = false;
            this.updateSendButton(false);
        }
    }
    
    sendQuickMessage(message) {
        const input = document.getElementById('chatInput');
        if (input) {
            input.value = message;
            this.sendChatMessage();
        }
    }
    
    addMessageToChat(role, content) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;
        
        // Remove welcome message if it exists
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage && role === 'user') {
            welcomeMessage.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = `message-avatar ${role}`;
        avatar.textContent = role === 'user' ? '👤' : '🤖';
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = this.formatMessageContent(content);
        
        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString();
        
        bubble.appendChild(time);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(bubble);
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    formatMessageContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message assistant typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-avatar assistant">🤖</div>
            <div class="message-bubble">
                <div class="message-loading">
                    Thinking
                    <div class="loading-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    displayToolActions(toolActions, executedActions = []) {
        const panel = document.getElementById('toolActionsPanel');
        const list = document.getElementById('toolActionsList');
        
        if (!panel || !list) return;
        
        list.innerHTML = '';
        
        toolActions.forEach((action, index) => {
            const executedAction = executedActions[index];
            
            const actionDiv = document.createElement('div');
            actionDiv.className = 'tool-action-item';
            
            actionDiv.innerHTML = `
                <div class="tool-action-header">
                    <span class="tool-action-name">${action.tool_name} - ${action.action}</span>
                    <span class="tool-action-confidence">Confidence: ${(action.confidence * 100).toFixed(0)}%</span>
                </div>
                <div class="tool-action-params">${JSON.stringify(action.parameters, null, 2)}</div>
                ${executedAction ? `
                    <div class="tool-action-result ${executedAction.result.success ? 'success' : 'error'}">
                        ${executedAction.result.success ? 
                            `✅ Executed: ${executedAction.result.message}` : 
                            `❌ Failed: ${executedAction.result.error}`
                        }
                    </div>
                ` : ''}
            `;
            
            list.appendChild(actionDiv);
        });
        
        panel.classList.add('visible');
    }
    
    displaySuggestions(suggestions) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;
        
        const suggestionsDiv = document.createElement('div');
        suggestionsDiv.className = 'chat-message assistant';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar assistant';
        avatar.textContent = '💡';
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        const suggestionsHtml = suggestions.map(suggestion => 
            `<button class="suggestion-btn" onclick="geminiChat.sendQuickMessage('${suggestion.replace(/'/g, "\\'")}')">${suggestion}</button>`
        ).join('');
        
        bubble.innerHTML = `
            <strong>Suggestions:</strong><br>
            <div class="quick-suggestions" style="margin-top: 0.5rem;">
                ${suggestionsHtml}
            </div>
        `;
        
        suggestionsDiv.appendChild(avatar);
        suggestionsDiv.appendChild(bubble);
        
        messagesContainer.appendChild(suggestionsDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    async clearCurrentSession() {
        if (!this.currentSessionId) {
            this.showInfo('No active session to clear');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/session/${this.currentSessionId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                this.currentSessionId = null;
                this.messageCount = 0;
                this.clearChatMessages();
                this.showWelcomeMessage();
                this.updateSessionInfo();
                this.hideToolActionsPanel();
                this.showSuccess('Chat session cleared successfully!');
            } else {
                throw new Error('Failed to clear session');
            }
            
        } catch (error) {
            console.error('Failed to clear session:', error);
            this.showError(`Failed to clear session: ${error.message}`);
        }
    }
    
    handleContextChange() {
        // Start new session with new context
        this.startNewChatSession();
    }
    
    clearChatMessages() {
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
    }
    
    showWelcomeMessage() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;
        
        const context = document.getElementById('chatContext')?.value || 'ai_tools_manager';
        let contextDescription = '';
        
        switch (context) {
            case 'ai_tools_manager':
                contextDescription = 'I\'m here to help you manage your AI tools, create workflows, and automate your business processes.';
                break;
            case 'workflow_builder':
                contextDescription = 'I\'m specialized in helping you create automated workflows and business processes.';
                break;
            case 'troubleshooter':
                contextDescription = 'I\'m here to help you troubleshoot issues with your tools and integrations.';
                break;
        }
        
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="assistant-avatar">🤖</div>
                <div class="message-content">
                    <h3>Welcome to Gemini AI Assistant!</h3>
                    <p>${contextDescription} What would you like to do today?</p>
                    <div class="quick-suggestions">
                        <button class="suggestion-btn" onclick="geminiChat.sendQuickMessage('Show me available tools')">Show Available Tools</button>
                        <button class="suggestion-btn" onclick="geminiChat.sendQuickMessage('Create a workflow')">Create Workflow</button>
                        <button class="suggestion-btn" onclick="geminiChat.sendQuickMessage('Send an email')">Send Email</button>
                        <button class="suggestion-btn" onclick="geminiChat.sendQuickMessage('Schedule a meeting')">Schedule Meeting</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    updateSessionInfo() {
        const sessionStatus = document.getElementById('sessionStatus');
        const sessionId = document.getElementById('sessionId');
        const messageCount = document.getElementById('messageCount');
        const statusIndicator = document.querySelector('.session-status');
        
        if (this.currentSessionId) {
            if (sessionStatus) sessionStatus.textContent = 'Active session';
            if (sessionId) sessionId.textContent = this.currentSessionId.substring(0, 8) + '...';
            if (messageCount) messageCount.textContent = `${this.messageCount} messages`;
            if (statusIndicator) statusIndicator.classList.add('active');
        } else {
            if (sessionStatus) sessionStatus.textContent = 'No active session';
            if (sessionId) sessionId.textContent = '-';
            if (messageCount) messageCount.textContent = '0 messages';
            if (statusIndicator) statusIndicator.classList.remove('active');
        }
    }
    
    updateSendButton(disabled) {
        const sendButton = document.getElementById('sendButton');
        if (sendButton) {
            sendButton.disabled = disabled;
            sendButton.innerHTML = disabled ? 
                '<span class="loading-dots"><span></span><span></span><span></span></span> Sending...' :
                '<span class="send-icon">➤</span> Send';
        }
    }
    
    hideToolActionsPanel() {
        const panel = document.getElementById('toolActionsPanel');
        if (panel) {
            panel.classList.remove('visible');
        }
    }
    
    showLoading(message) {
        // You can implement a loading overlay here
        console.log('Loading:', message);
    }
    
    hideLoading() {
        // Hide loading overlay
        console.log('Loading complete');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showInfo(message) {
        this.showNotification(message, 'info');
    }
    
    showNotification(message, type) {
        // Simple notification system - you can enhance this
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            animation: slideInRight 0.3s ease;
            max-width: 400px;
        `;
        
        switch (type) {
            case 'success':
                notification.style.background = 'linear-gradient(135deg, #00ff41, #00cc33)';
                break;
            case 'error':
                notification.style.background = 'linear-gradient(135deg, #ff4444, #cc0000)';
                break;
            case 'info':
                notification.style.background = 'linear-gradient(135deg, #4444ff, #0000cc)';
                break;
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    getAuthToken() {
        // Get auth token from localStorage or wherever it's stored
        return localStorage.getItem('authToken') || '';
    }
}

// Global functions for HTML onclick handlers
function startNewChatSession() {
    if (window.geminiChat) {
        window.geminiChat.startNewChatSession();
    }
}

function clearCurrentSession() {
    if (window.geminiChat) {
        window.geminiChat.clearCurrentSession();
    }
}

function sendChatMessage() {
    if (window.geminiChat) {
        window.geminiChat.sendChatMessage();
    }
}

function sendQuickMessage(message) {
    if (window.geminiChat) {
        window.geminiChat.sendQuickMessage(message);
    }
}

function handleChatKeydown(event) {
    if (window.geminiChat) {
        window.geminiChat.handleChatKeydown(event);
    }
}

// Initialize the chat interface
window.geminiChat = new GeminiChatInterface();

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);