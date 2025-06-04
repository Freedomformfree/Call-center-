/**
 * Voice Call Management System
 * Handles 30-minute AI consultation sessions
 */

class VoiceCallManager {
    constructor() {
        this.currentSession = null;
        this.timer = null;
        this.sessionDuration = 30 * 60; // 30 minutes in seconds
        this.remainingTime = this.sessionDuration;
        this.isCallActive = false;
        this.companyPhone = null;
        
        this.initializeEventListeners();
        this.loadRecentCalls();
    }

    initializeEventListeners() {
        // Start consultation button
        const startBtn = document.getElementById('start-consultation');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startConsultation());
        }

        // End consultation button
        const endBtn = document.getElementById('end-consultation');
        if (endBtn) {
            endBtn.addEventListener('click', () => this.endConsultation());
        }

        // Request phone number button
        const requestPhoneBtn = document.getElementById('request-phone');
        if (requestPhoneBtn) {
            requestPhoneBtn.addEventListener('click', () => this.requestPhoneNumber());
        }
    }

    async requestPhoneNumber() {
        try {
            showLoading('Requesting company phone number...');
            
            const response = await fetch('/api/v1/client/request-temporary-phone', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            });

            const result = await response.json();
            hideLoading();

            if (result.success) {
                this.companyPhone = result.phone_number;
                this.updatePhoneDisplay(result.phone_number);
                this.enableConsultationStart();
                
                showNotification('Phone number assigned! You can now start your consultation.', 'success');
                
                // Auto-start timer for 30 minutes
                this.startSessionTimer();
            } else {
                showNotification(result.error || 'Failed to assign phone number', 'error');
            }
        } catch (error) {
            hideLoading();
            console.error('Error requesting phone number:', error);
            showNotification('Failed to request phone number', 'error');
        }
    }

    updatePhoneDisplay(phoneNumber) {
        const phoneDisplay = document.getElementById('company-phone-display');
        if (phoneDisplay) {
            phoneDisplay.textContent = phoneNumber;
            phoneDisplay.classList.add('active');
        }

        const phoneCard = document.querySelector('.phone-number-card');
        if (phoneCard) {
            phoneCard.classList.add('assigned');
        }
    }

    enableConsultationStart() {
        const startBtn = document.getElementById('start-consultation');
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.textContent = 'Start Consultation Call';
        }
    }

    async startConsultation() {
        if (!this.companyPhone) {
            showNotification('Please request a phone number first', 'warning');
            return;
        }

        try {
            showLoading('Starting consultation session...');

            const response = await fetch('/api/v1/client/start-consultation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify({
                    phone_number: this.companyPhone
                })
            });

            const result = await response.json();
            hideLoading();

            if (result.success) {
                this.currentSession = result.session;
                this.isCallActive = true;
                this.updateCallStatus('active');
                
                showNotification('Consultation started! Call the number to begin.', 'success');
                
                // Update UI
                this.showActiveCallInterface();
            } else {
                showNotification(result.error || 'Failed to start consultation', 'error');
            }
        } catch (error) {
            hideLoading();
            console.error('Error starting consultation:', error);
            showNotification('Failed to start consultation', 'error');
        }
    }

    async endConsultation() {
        if (!this.isCallActive) {
            return;
        }

        try {
            showLoading('Ending consultation...');

            const response = await fetch('/api/v1/client/end-consultation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify({
                    session_id: this.currentSession?.id
                })
            });

            const result = await response.json();
            hideLoading();

            if (result.success) {
                this.isCallActive = false;
                this.currentSession = null;
                this.stopTimer();
                this.updateCallStatus('ended');
                
                // Show consultation results if available
                if (result.analysis) {
                    this.showConsultationResults(result.analysis);
                }
                
                showNotification('Consultation ended successfully', 'success');
                this.resetInterface();
            } else {
                showNotification(result.error || 'Failed to end consultation', 'error');
            }
        } catch (error) {
            hideLoading();
            console.error('Error ending consultation:', error);
            showNotification('Failed to end consultation', 'error');
        }
    }

    startSessionTimer() {
        this.remainingTime = this.sessionDuration;
        this.updateTimerDisplay();
        
        this.timer = setInterval(() => {
            this.remainingTime--;
            this.updateTimerDisplay();
            
            if (this.remainingTime <= 0) {
                this.handleSessionTimeout();
            }
        }, 1000);
    }

    stopTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    updateTimerDisplay() {
        const timerElement = document.getElementById('session-timer');
        if (timerElement) {
            const minutes = Math.floor(this.remainingTime / 60);
            const seconds = this.remainingTime % 60;
            timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            // Change color when time is running low
            if (this.remainingTime <= 300) { // 5 minutes
                timerElement.classList.add('warning');
            }
            if (this.remainingTime <= 60) { // 1 minute
                timerElement.classList.add('critical');
            }
        }
    }

    handleSessionTimeout() {
        this.stopTimer();
        this.isCallActive = false;
        
        showNotification('Your 30-minute consultation session has ended', 'info');
        
        if (this.currentSession) {
            this.endConsultation();
        }
        
        this.resetInterface();
    }

    updateCallStatus(status) {
        const statusElement = document.getElementById('call-status');
        if (statusElement) {
            statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            statusElement.className = `status ${status}`;
        }
    }

    showActiveCallInterface() {
        const callInterface = document.getElementById('active-call-interface');
        if (callInterface) {
            callInterface.style.display = 'block';
        }

        const startBtn = document.getElementById('start-consultation');
        const endBtn = document.getElementById('end-consultation');
        
        if (startBtn) startBtn.style.display = 'none';
        if (endBtn) endBtn.style.display = 'block';
    }

    resetInterface() {
        const callInterface = document.getElementById('active-call-interface');
        if (callInterface) {
            callInterface.style.display = 'none';
        }

        const startBtn = document.getElementById('start-consultation');
        const endBtn = document.getElementById('end-consultation');
        
        if (startBtn) {
            startBtn.style.display = 'block';
            startBtn.disabled = true;
            startBtn.textContent = 'Request Phone Number First';
        }
        if (endBtn) endBtn.style.display = 'none';

        // Reset timer display
        const timerElement = document.getElementById('session-timer');
        if (timerElement) {
            timerElement.textContent = '30:00';
            timerElement.classList.remove('warning', 'critical');
        }

        // Reset phone display
        const phoneDisplay = document.getElementById('company-phone-display');
        if (phoneDisplay) {
            phoneDisplay.textContent = 'Not assigned';
            phoneDisplay.classList.remove('active');
        }

        const phoneCard = document.querySelector('.phone-number-card');
        if (phoneCard) {
            phoneCard.classList.remove('assigned');
        }

        this.companyPhone = null;
        this.updateCallStatus('ready');
    }

    showConsultationResults(analysis) {
        // Create modal for consultation results
        const modal = document.createElement('div');
        modal.className = 'modal consultation-results-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>🎯 Consultation Analysis Results</h3>
                    <span class="close">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="analysis-summary">
                        <h4>Business Type: ${analysis.business_type?.name || 'Not identified'}</h4>
                        <p><strong>Confidence:</strong> ${Math.round((analysis.business_type?.confidence || 0) * 100)}%</p>
                        <p><strong>Summary:</strong> ${analysis.summary || 'No summary available'}</p>
                    </div>
                    
                    <div class="recommended-tools">
                        <h4>🛠️ Recommended AI Tools</h4>
                        <div class="tools-grid">
                            ${analysis.recommended_tools?.map(tool => `
                                <div class="tool-card">
                                    <h5>${tool.name}</h5>
                                    <p>${tool.description}</p>
                                    <span class="priority ${tool.priority}">${tool.priority}</span>
                                </div>
                            `).join('') || '<p>No tools recommended</p>'}
                        </div>
                    </div>
                    
                    <div class="subscription-offer">
                        <h4>💰 Subscription Offer</h4>
                        <div class="pricing-card">
                            <div class="price">$${analysis.pricing?.monthly_price || 20}/month</div>
                            <p>Includes all recommended tools and automation workflows</p>
                            <button class="btn-primary" onclick="voiceCallManager.createSubscription(${JSON.stringify(analysis).replace(/"/g, '&quot;')})">
                                Subscribe Now
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.style.display = 'block';

        // Close modal functionality
        const closeBtn = modal.querySelector('.close');
        closeBtn.onclick = () => {
            document.body.removeChild(modal);
        };

        window.onclick = (event) => {
            if (event.target === modal) {
                document.body.removeChild(modal);
            }
        };
    }

    async createSubscription(analysis) {
        try {
            showLoading('Creating subscription...');

            const response = await fetch('/api/v1/client/create-ai-tool-chain', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify({
                    business_type: analysis.business_type?.name,
                    recommended_tools: analysis.recommended_tools,
                    chain_name: `${analysis.business_type?.name} Automation Chain`
                })
            });

            const result = await response.json();
            hideLoading();

            if (result.success) {
                showNotification('AI tool chain created successfully!', 'success');
                
                // Close modal
                const modal = document.querySelector('.consultation-results-modal');
                if (modal) {
                    document.body.removeChild(modal);
                }
                
                // Refresh AI tools tab
                if (window.loadAITools) {
                    window.loadAITools();
                }
            } else {
                showNotification(result.error || 'Failed to create tool chain', 'error');
            }
        } catch (error) {
            hideLoading();
            console.error('Error creating subscription:', error);
            showNotification('Failed to create subscription', 'error');
        }
    }

    async loadRecentCalls() {
        try {
            const response = await fetch('/api/v1/client/recent-calls', {
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            });

            if (response.ok) {
                const calls = await response.json();
                this.displayRecentCalls(calls);
            }
        } catch (error) {
            console.error('Error loading recent calls:', error);
        }
    }

    displayRecentCalls(calls) {
        const container = document.getElementById('recent-calls-list');
        if (!container || !calls.length) return;

        container.innerHTML = calls.map(call => `
            <div class="call-item">
                <div class="call-info">
                    <div class="call-date">${new Date(call.created_at).toLocaleDateString()}</div>
                    <div class="call-duration">${call.duration_minutes || 0} min</div>
                    <div class="call-status ${call.status}">${call.status}</div>
                </div>
                <div class="call-actions">
                    ${call.analysis_available ? 
                        `<button class="btn-small" onclick="voiceCallManager.viewCallAnalysis('${call.id}')">View Analysis</button>` :
                        '<span class="no-analysis">No analysis</span>'
                    }
                </div>
            </div>
        `).join('');
    }

    async viewCallAnalysis(callId) {
        try {
            showLoading('Loading call analysis...');

            const response = await fetch(`/api/v1/client/call-analysis/${callId}`, {
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            });

            const result = await response.json();
            hideLoading();

            if (result.success && result.analysis) {
                this.showConsultationResults(result.analysis);
            } else {
                showNotification('Analysis not available', 'info');
            }
        } catch (error) {
            hideLoading();
            console.error('Error loading call analysis:', error);
            showNotification('Failed to load analysis', 'error');
        }
    }
}

// Utility functions
function getAuthToken() {
    return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
}

function showLoading(message = 'Loading...') {
    // Implementation depends on your loading system
    console.log('Loading:', message);
}

function hideLoading() {
    // Implementation depends on your loading system
    console.log('Loading complete');
}

function showNotification(message, type = 'info') {
    // Implementation depends on your notification system
    console.log(`${type.toUpperCase()}: ${message}`);
    
    // Simple notification implementation
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#2196F3'};
        color: white;
        border-radius: 4px;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Initialize voice call manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.voiceCallManager = new VoiceCallManager();
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .phone-number-card.assigned {
        border-color: #4CAF50;
        background: linear-gradient(135deg, #f8f9fa 0%, #e8f5e8 100%);
    }
    
    .phone-number-card.assigned #company-phone-display.active {
        color: #4CAF50;
        font-weight: bold;
    }
    
    .status.active {
        color: #4CAF50;
    }
    
    .status.ended {
        color: #666;
    }
    
    .status.ready {
        color: #2196F3;
    }
    
    #session-timer.warning {
        color: #ff9800;
    }
    
    #session-timer.critical {
        color: #f44336;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .consultation-results-modal .tools-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
        margin: 15px 0;
    }
    
    .consultation-results-modal .tool-card {
        padding: 15px;
        border: 1px solid #ddd;
        border-radius: 8px;
        background: #f9f9f9;
    }
    
    .consultation-results-modal .priority.high {
        background: #f44336;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
    }
    
    .consultation-results-modal .priority.medium {
        background: #ff9800;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
    }
    
    .consultation-results-modal .priority.low {
        background: #4CAF50;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
    }
    
    .consultation-results-modal .pricing-card {
        text-align: center;
        padding: 20px;
        border: 2px solid #4CAF50;
        border-radius: 12px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e8f5e8 100%);
    }
    
    .consultation-results-modal .price {
        font-size: 2em;
        font-weight: bold;
        color: #4CAF50;
        margin-bottom: 10px;
    }
`;
document.head.appendChild(style);