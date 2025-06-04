// Dashboard JavaScript - Main functionality
const API_BASE_URL = 'https://work-2-lnfsvueowecmomfa.prod-runtime.all-hands.dev';

let currentSection = 'overview';
let selectedTool = null;
let workflowNodes = [];
let connections = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    loadDashboardData();
    initializeCharts();
    setupEventListeners();
});

function initializeDashboard() {
    // Set up navigation
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            switchSection(section);
        });
    });

    // Load initial data
    loadBusinessTools();
    loadModules();
    loadApiKeys();
    startLiveUpdates();
}

function switchSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.dashboard-section').forEach(section => {
        section.classList.remove('active');
    });

    // Show selected section
    const targetSection = document.getElementById(sectionName);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

    currentSection = sectionName;

    // Load section-specific data
    switch (sectionName) {
        case 'tools':
            loadBusinessTools();
            break;
        case 'connections':
            loadWorkflowBuilder();
            break;
        case 'analytics':
            updateCharts();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// Business-focused AI tools
const businessTools = [
    {
        id: 'customer_followup',
        name: 'Customer Follow-up',
        description: 'Automatically follow up with customers via SMS or call based on their interaction history',
        icon: '📞',
        category: 'customer',
        active: true,
        config: {
            followup_delay: 24,
            message_template: 'Hello {name}! We wanted to follow up on your recent inquiry.',
            max_attempts: 3
        }
    },
    {
        id: 'lead_scoring',
        name: 'Lead Scoring',
        description: 'Score leads based on engagement and profile to prioritize sales efforts',
        icon: '🎯',
        category: 'sales',
        active: true,
        config: {
            scoring_factors: ['calls', 'emails', 'budget', 'industry'],
            threshold_high: 80,
            threshold_medium: 60
        }
    },
    {
        id: 'appointment_scheduler',
        name: 'Appointment Scheduler',
        description: 'Automatically schedule appointments with prospects based on availability',
        icon: '📅',
        category: 'sales',
        active: false,
        config: {
            business_hours: '9:00-17:00',
            buffer_time: 30,
            confirmation_sms: true
        }
    },
    {
        id: 'quote_generator',
        name: 'Quote Generator',
        description: 'Generate customized quotes for prospects automatically',
        icon: '💰',
        category: 'sales',
        active: true,
        config: {
            default_discount: 10,
            valid_days: 30,
            auto_send: true
        }
    },
    {
        id: 'sales_report',
        name: 'Sales Reports',
        description: 'Generate automated daily, weekly, and monthly sales reports',
        icon: '📊',
        category: 'analytics',
        active: true,
        config: {
            frequency: 'daily',
            recipients: ['manager@company.com'],
            include_charts: true
        }
    },
    {
        id: 'customer_satisfaction',
        name: 'Customer Satisfaction',
        description: 'Send satisfaction surveys and analyze customer feedback',
        icon: '😊',
        category: 'customer',
        active: false,
        config: {
            survey_delay: 48,
            rating_scale: 5,
            follow_up_low_scores: true
        }
    }
];

function loadBusinessTools() {
    const toolsGrid = document.getElementById('toolsGrid');
    if (!toolsGrid) return;

    const currentFilter = document.querySelector('.filter-btn.active')?.dataset.filter || 'all';
    
    const filteredTools = currentFilter === 'all' 
        ? businessTools 
        : businessTools.filter(tool => tool.category === currentFilter);

    toolsGrid.innerHTML = filteredTools.map(tool => `
        <div class="tool-card" data-tool-id="${tool.id}">
            <div class="tool-header">
                <div>
                    <div class="tool-icon">${tool.icon}</div>
                    <div class="tool-status ${tool.active ? 'active' : ''}"></div>
                </div>
            </div>
            <h3 class="tool-title">${tool.name}</h3>
            <p class="tool-description">${tool.description}</p>
            <div class="tool-actions">
                <button class="tool-btn ${tool.active ? 'primary' : ''}" onclick="toggleTool('${tool.id}')">
                    ${tool.active ? 'Disable' : 'Enable'}
                </button>
                <button class="tool-btn" onclick="configureTool('${tool.id}')">Configure</button>
                <button class="tool-btn" onclick="runTool('${tool.id}')">Run Now</button>
            </div>
        </div>
    `).join('');

    // Setup filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadBusinessTools();
        });
    });
}

function toggleTool(toolId) {
    const tool = businessTools.find(t => t.id === toolId);
    if (tool) {
        tool.active = !tool.active;
        loadBusinessTools();
        showNotification(`${tool.name} ${tool.active ? 'enabled' : 'disabled'}`, 'success');
    }
}

function configureTool(toolId) {
    const tool = businessTools.find(t => t.id === toolId);
    if (!tool) return;

    selectedTool = tool;
    document.getElementById('toolConfigTitle').textContent = `Configure ${tool.name}`;
    
    // Load configuration interface
    loadToolConfiguration(tool);
    openModal('toolConfigModal');
}

function loadToolConfiguration(tool) {
    const content = document.getElementById('toolConfigContent');
    
    // Generate configuration form based on tool config
    const configForm = Object.entries(tool.config).map(([key, value]) => {
        const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const inputType = typeof value === 'number' ? 'number' : 
                         typeof value === 'boolean' ? 'checkbox' : 'text';
        
        if (inputType === 'checkbox') {
            return `
                <div class="property-group">
                    <label class="property-label">
                        <input type="checkbox" ${value ? 'checked' : ''} data-config="${key}">
                        ${label}
                    </label>
                </div>
            `;
        } else {
            return `
                <div class="property-group">
                    <label class="property-label">${label}</label>
                    <input type="${inputType}" class="property-input" value="${value}" data-config="${key}">
                </div>
            `;
        }
    }).join('');

    content.innerHTML = `
        <div class="tab-content active" data-tab="settings">
            <form class="tool-config-form">
                ${configForm}
            </form>
        </div>
        <div class="tab-content" data-tab="triggers">
            <h4>Trigger Conditions</h4>
            <div class="trigger-list">
                <div class="trigger-item">
                    <label>Run when new lead is added</label>
                    <input type="checkbox" class="toggle-switch" checked>
                </div>
                <div class="trigger-item">
                    <label>Run on schedule</label>
                    <input type="checkbox" class="toggle-switch">
                </div>
                <div class="trigger-item">
                    <label>Run manually only</label>
                    <input type="checkbox" class="toggle-switch">
                </div>
            </div>
        </div>
        <div class="tab-content" data-tab="actions">
            <h4>Actions After Execution</h4>
            <div class="action-list">
                <div class="action-item">
                    <label>Send notification</label>
                    <input type="checkbox" class="toggle-switch" checked>
                </div>
                <div class="action-item">
                    <label>Update CRM</label>
                    <input type="checkbox" class="toggle-switch" checked>
                </div>
                <div class="action-item">
                    <label>Log to analytics</label>
                    <input type="checkbox" class="toggle-switch" checked>
                </div>
            </div>
        </div>
    `;

    // Setup tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
        });
    });
}

function saveToolConfiguration() {
    if (!selectedTool) return;

    // Get form data
    const form = document.querySelector('.tool-config-form');
    const formData = new FormData(form);
    
    // Update tool configuration
    const inputs = form.querySelectorAll('[data-config]');
    inputs.forEach(input => {
        const key = input.dataset.config;
        let value = input.value;
        
        if (input.type === 'checkbox') {
            value = input.checked;
        } else if (input.type === 'number') {
            value = parseFloat(value);
        }
        
        selectedTool.config[key] = value;
    });

    closeModal('toolConfigModal');
    showNotification(`${selectedTool.name} configuration saved`, 'success');
    selectedTool = null;
}

async function runTool(toolId) {
    const tool = businessTools.find(t => t.id === toolId);
    if (!tool) return;

    showNotification(`Running ${tool.name}...`, 'info');

    try {
        // Simulate API call to run tool
        const response = await fetch(`${API_BASE_URL}/api/v1/tools/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify({
                tool_id: toolId,
                config: tool.config
            })
        });

        if (response.ok) {
            const result = await response.json();
            showNotification(`${tool.name} completed successfully`, 'success');
            
            // Add to activity feed
            addActivityItem({
                title: `${tool.name} executed`,
                meta: `Completed at ${new Date().toLocaleTimeString()}`,
                status: 'success'
            });
        } else {
            throw new Error('Tool execution failed');
        }
    } catch (error) {
        showNotification(`${tool.name} execution failed`, 'error');
        console.error('Tool execution error:', error);
    }
}

// Live data updates
function startLiveUpdates() {
    // Update stats every 30 seconds
    setInterval(updateStats, 30000);
    
    // Update activity feed every 10 seconds
    setInterval(updateActivityFeed, 10000);
    
    // Initial load
    updateStats();
    updateActivityFeed();
}

function updateStats() {
    // Simulate real-time stats updates
    const stats = [
        { value: Math.floor(Math.random() * 50) + 10, change: (Math.random() - 0.5) * 20 },
        { value: Math.floor(Math.random() * 2000) + 500, change: (Math.random() - 0.5) * 30 },
        { value: (Math.random() * 20 + 20).toFixed(1), change: (Math.random() - 0.5) * 10 },
        { value: Math.floor(Math.random() * 20000) + 5000, change: (Math.random() - 0.5) * 25 }
    ];

    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        const valueEl = card.querySelector('.stat-value');
        const changeEl = card.querySelector('.stat-change');
        
        if (valueEl && changeEl && stats[index]) {
            valueEl.textContent = index === 3 ? `$${stats[index].value.toLocaleString()}` : 
                                 index === 2 ? `${stats[index].value}%` : stats[index].value;
            
            const change = stats[index].change;
            changeEl.textContent = `${change > 0 ? '+' : ''}${change.toFixed(1)}%`;
            changeEl.className = `stat-change ${change > 0 ? 'positive' : 'negative'}`;
        }
    });
}

function updateActivityFeed() {
    updateRecentCalls();
    updateToolExecutions();
}

function updateRecentCalls() {
    const container = document.getElementById('recentCalls');
    if (!container) return;

    const calls = [
        { phone: '+1 (555) 123-4567', duration: '2:34', status: 'completed', time: '2 min ago' },
        { phone: '+1 (555) 987-6543', duration: '1:45', status: 'completed', time: '5 min ago' },
        { phone: '+1 (555) 456-7890', duration: '0:23', status: 'missed', time: '8 min ago' },
        { phone: '+1 (555) 321-0987', duration: '3:12', status: 'completed', time: '12 min ago' }
    ];

    container.innerHTML = calls.map(call => `
        <div class="activity-item">
            <div class="activity-info">
                <div class="activity-title">${call.phone}</div>
                <div class="activity-meta">Duration: ${call.duration} • ${call.time}</div>
            </div>
            <div class="activity-status ${call.status === 'completed' ? 'success' : 'error'}">
                ${call.status}
            </div>
        </div>
    `).join('');
}

function updateToolExecutions() {
    const container = document.getElementById('toolExecutions');
    if (!container) return;

    const executions = [
        { tool: 'Lead Scoring', result: 'Scored 15 leads', status: 'success', time: '1 min ago' },
        { tool: 'Customer Follow-up', result: 'Sent 8 SMS messages', status: 'success', time: '3 min ago' },
        { tool: 'Quote Generator', result: 'Generated 2 quotes', status: 'success', time: '7 min ago' },
        { tool: 'Sales Report', result: 'Report generation failed', status: 'error', time: '15 min ago' }
    ];

    container.innerHTML = executions.map(exec => `
        <div class="activity-item">
            <div class="activity-info">
                <div class="activity-title">${exec.tool}</div>
                <div class="activity-meta">${exec.result} • ${exec.time}</div>
            </div>
            <div class="activity-status ${exec.status}">
                ${exec.status}
            </div>
        </div>
    `).join('');
}

function addActivityItem(item) {
    const container = document.getElementById('toolExecutions');
    if (!container) return;

    const itemHtml = `
        <div class="activity-item">
            <div class="activity-info">
                <div class="activity-title">${item.title}</div>
                <div class="activity-meta">${item.meta}</div>
            </div>
            <div class="activity-status ${item.status}">
                ${item.status}
            </div>
        </div>
    `;

    container.insertAdjacentHTML('afterbegin', itemHtml);
    
    // Remove oldest item if more than 10
    const items = container.querySelectorAll('.activity-item');
    if (items.length > 10) {
        items[items.length - 1].remove();
    }
}

// SIM800C Module Management
function loadModules() {
    const modulesList = document.getElementById('modulesList');
    if (!modulesList) return;

    const modules = [
        { id: 'module1', name: 'SIM800C-01', port: '/dev/ttyUSB0', status: 'connected', signal: 85 },
        { id: 'module2', name: 'SIM800C-02', port: '/dev/ttyUSB2', status: 'connected', signal: 92 },
        { id: 'module3', name: 'SIM800C-03', port: '/dev/ttyUSB4', status: 'disconnected', signal: 0 }
    ];

    modulesList.innerHTML = modules.map(module => `
        <div class="module-item">
            <div class="module-info">
                <div class="module-name">${module.name}</div>
                <div class="module-status">
                    Port: ${module.port} • 
                    Status: ${module.status} • 
                    Signal: ${module.signal}%
                </div>
            </div>
            <div class="module-actions">
                <button class="tool-btn" onclick="configureModule('${module.id}')">Configure</button>
                <button class="tool-btn ${module.status === 'connected' ? 'primary' : ''}" 
                        onclick="toggleModule('${module.id}')">
                    ${module.status === 'connected' ? 'Disconnect' : 'Connect'}
                </button>
            </div>
        </div>
    `).join('');
}

function addNewModule() {
    // Open module configuration modal
    showNotification('Module configuration modal would open here', 'info');
}

function configureModule(moduleId) {
    showNotification(`Configuring module ${moduleId}`, 'info');
}

function toggleModule(moduleId) {
    showNotification(`Toggling module ${moduleId}`, 'info');
    setTimeout(() => {
        loadModules();
    }, 1000);
}

// API Keys Management
function loadApiKeys() {
    const apiKeysList = document.getElementById('apiKeysList');
    if (!apiKeysList) return;

    const apiKeys = [
        { service: 'SIM800C Local GSM', status: 'configured', masked: '/dev/ttyUSB0' },
        { service: 'OpenAI', status: 'configured', masked: '••••••••••••5678' },
        { service: 'Stripe', status: 'not_configured', masked: 'Not set' },
        { service: 'SendGrid', status: 'configured', masked: '••••••••••••9012' }
    ];

    apiKeysList.innerHTML = apiKeys.map(key => `
        <div class="module-item">
            <div class="module-info">
                <div class="module-name">${key.service}</div>
                <div class="module-status">
                    Key: ${key.masked} • 
                    Status: ${key.status.replace('_', ' ')}
                </div>
            </div>
            <div class="module-actions">
                <button class="tool-btn" onclick="editApiKey('${key.service}')">
                    ${key.status === 'configured' ? 'Update' : 'Configure'}
                </button>
            </div>
        </div>
    `).join('');

    // Load Gemini keys per module
    loadGeminiKeys();
}

function loadGeminiKeys() {
    const geminiKeysList = document.getElementById('geminiKeysList');
    if (!geminiKeysList) return;

    const geminiKeys = [
        { module: 'SIM800C-01', key: '••••••••••••abcd', status: 'active' },
        { module: 'SIM800C-02', key: '••••••••••••efgh', status: 'active' },
        { module: 'SIM800C-03', key: 'Not configured', status: 'inactive' }
    ];

    geminiKeysList.innerHTML = geminiKeys.map(key => `
        <div class="module-item">
            <div class="module-info">
                <div class="module-name">${key.module}</div>
                <div class="module-status">
                    Gemini Key: ${key.key} • 
                    Status: ${key.status}
                </div>
            </div>
            <div class="module-actions">
                <button class="tool-btn" onclick="editGeminiKey('${key.module}')">
                    ${key.status === 'active' ? 'Update' : 'Configure'}
                </button>
            </div>
        </div>
    `).join('');
}

function manageApiKeys() {
    showNotification('API keys management modal would open here', 'info');
}

function editApiKey(service) {
    showNotification(`Editing ${service} API key`, 'info');
}

function editGeminiKey(module) {
    showNotification(`Editing Gemini key for ${module}`, 'info');
}

// Charts initialization
function initializeCharts() {
    if (typeof Chart === 'undefined') return;

    // Call Volume Chart
    const callVolumeCtx = document.getElementById('callVolumeChart');
    if (callVolumeCtx) {
        new Chart(callVolumeCtx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Calls',
                    data: [65, 59, 80, 81, 56, 55, 40],
                    borderColor: '#00ff41',
                    backgroundColor: 'rgba(0, 255, 65, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                },
                scales: {
                    x: { ticks: { color: '#b0b0b0' } },
                    y: { ticks: { color: '#b0b0b0' } }
                }
            }
        });
    }

    // Add other charts...
}

function updateCharts() {
    // Update chart data
    showNotification('Charts updated', 'info');
}

// Floating Action Button
function toggleQuickActions() {
    const fab = document.querySelector('.fab');
    const fabMenu = document.getElementById('fabMenu');
    
    fab.classList.toggle('active');
    fabMenu.classList.toggle('active');
}

function quickCall() {
    toggleQuickActions();
    openModal('quickCallModal');
}

function quickSMS() {
    toggleQuickActions();
    openModal('quickSMSModal');
}

function quickTool() {
    toggleQuickActions();
    showNotification('Quick tool execution panel would open here', 'info');
}

async function makeQuickCall(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    showLoading(form);
    
    try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        hideLoading(form);
        closeModal('quickCallModal');
        form.reset();
        showNotification('Call initiated successfully', 'success');
        
    } catch (error) {
        hideLoading(form);
        showNotification('Failed to initiate call', 'error');
    }
}

async function sendQuickSMS(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    showLoading(form);
    
    try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        hideLoading(form);
        closeModal('quickSMSModal');
        form.reset();
        showNotification('SMS sent successfully', 'success');
        
    } catch (error) {
        hideLoading(form);
        showNotification('Failed to send SMS', 'error');
    }
}

// Additional utility functions
function startNewCampaign() {
    showNotification('Campaign creation wizard would open here', 'info');
}

function openToolsPanel() {
    switchSection('tools');
}

function exportReport() {
    showNotification('Exporting report...', 'info');
    setTimeout(() => {
        showNotification('Report exported successfully', 'success');
    }, 2000);
}

function loadSettings() {
    loadModules();
    loadApiKeys();
}

function loadDashboardData() {
    // Load all dashboard data
    updateStats();
    updateActivityFeed();
}

function setupEventListeners() {
    // Close FAB menu when clicking outside
    document.addEventListener('click', (e) => {
        const fab = document.querySelector('.fab');
        const fabMenu = document.getElementById('fabMenu');
        
        if (!fab.contains(e.target) && fabMenu.classList.contains('active')) {
            toggleQuickActions();
        }
    });
}

// Workflow Management Functions
function createNewWorkflow() {
    workflowBuilder.clearWorkflow();
    showNotification('New workflow created. Start by dragging tools from the palette.', 'info');
}

function importWorkflow() {
    showNotification('Import workflow functionality coming soon!', 'info');
}

// Workflow Execution
async function executeWorkflow() {
    const executeBtn = document.getElementById('executeWorkflowBtn');
    executeBtn.disabled = true;
    executeBtn.innerHTML = '⏳ Running...';
    
    try {
        showNotification('Starting workflow execution...', 'info');
        
        // Get workflow data from the builder
        const workflowData = {
            nodes: Array.from(workflowBuilder.nodes.values()),
            connections: Array.from(workflowBuilder.connections.values())
        };
        
        if (workflowData.nodes.length === 0) {
            throw new Error('No workflow nodes found. Please create a workflow first.');
        }
        
        const response = await fetch(`${API_BASE_URL}/api/execute-workflow`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify({
                workflow: workflowData,
                trigger_data: {
                    timestamp: new Date().toISOString(),
                    source: 'manual_execution',
                    user_id: 'current_user'
                }
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(`Workflow executed successfully! Execution ID: ${result.execution_id}`, 'success');
            
            // Show execution results
            displayWorkflowResults(result);
        } else {
            throw new Error(result.error || 'Workflow execution failed');
        }
        
    } catch (error) {
        console.error('Workflow execution error:', error);
        showNotification(`Workflow execution failed: ${error.message}`, 'error');
    } finally {
        executeBtn.disabled = false;
        executeBtn.innerHTML = '▶️ Run Workflow';
    }
}

function displayWorkflowResults(result) {
    const resultsHtml = `
        <div class="workflow-results">
            <h3>Workflow Execution Results</h3>
            <div class="execution-info">
                <p><strong>Execution ID:</strong> ${result.execution_id}</p>
                <p><strong>Status:</strong> <span class="status-${result.status}">${result.status}</span></p>
                <p><strong>Duration:</strong> ${result.duration}ms</p>
                <p><strong>Nodes Executed:</strong> ${result.nodes_executed}</p>
            </div>
            <div class="execution-steps">
                <h4>Execution Steps:</h4>
                ${result.steps.map(step => `
                    <div class="step-item">
                        <span class="step-icon">${step.status === 'success' ? '✅' : '❌'}</span>
                        <span class="step-name">${step.node_name}</span>
                        <span class="step-duration">${step.duration}ms</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    // Show results in a modal or dedicated section
    showModal('Workflow Results', resultsHtml);
}