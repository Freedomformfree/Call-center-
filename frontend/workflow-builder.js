// Workflow Builder - Tool Connection System
// Allows tools to be connected in chains with visual flow

class WorkflowBuilder {
    constructor() {
        this.canvas = document.getElementById('workflowCanvas');
        this.nodesContainer = document.getElementById('workflowNodes');
        this.connectionsContainer = document.getElementById('connectionLines');
        this.paletteContainer = document.getElementById('paletteTools');
        this.propertiesPanel = document.getElementById('workflowProperties');
        
        this.nodes = new Map();
        this.connections = new Map();
        this.selectedNode = null;
        this.draggedNode = null;
        this.isConnecting = false;
        this.connectionStart = null;
        this.tempConnection = null;
        
        this.nodeIdCounter = 0;
        this.connectionIdCounter = 0;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadAvailableTools();
        this.createSampleWorkflow();
    }
    
    setupEventListeners() {
        // Canvas events
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleCanvasMouseMove(e));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Prevent default drag behavior
        this.canvas.addEventListener('dragover', (e) => e.preventDefault());
        this.canvas.addEventListener('drop', (e) => this.handleCanvasDrop(e));
    }
    
    loadAvailableTools() {
        const availableTools = [
            {
                id: 'customer_followup',
                name: 'Customer Follow-up',
                icon: '📞',
                category: 'customer',
                description: 'Automatically follow up with customers',
                inputs: ['customer_id', 'message_template'],
                outputs: ['follow_up_sent', 'response_received']
            },
            {
                id: 'lead_scoring',
                name: 'Lead Scoring',
                icon: '🎯',
                category: 'sales',
                description: 'Score leads based on behavior',
                inputs: ['lead_data'],
                outputs: ['score', 'grade', 'next_action']
            },
            {
                id: 'appointment_scheduler',
                name: 'Appointment Scheduler',
                icon: '📅',
                category: 'sales',
                description: 'Schedule appointments automatically',
                inputs: ['prospect_phone', 'preferred_time'],
                outputs: ['appointment_created', 'confirmation_sent']
            },
            {
                id: 'quote_generator',
                name: 'Quote Generator',
                icon: '💰',
                category: 'sales',
                description: 'Generate customized quotes',
                inputs: ['customer_id', 'services', 'discount'],
                outputs: ['quote_generated', 'quote_sent']
            },
            {
                id: 'sms_sender',
                name: 'SMS Sender',
                icon: '💬',
                category: 'communication',
                description: 'Send SMS messages',
                inputs: ['phone_number', 'message', 'module_id'],
                outputs: ['sms_sent', 'delivery_status']
            },
            {
                id: 'call_maker',
                name: 'Call Maker',
                icon: '📱',
                category: 'communication',
                description: 'Make outbound calls',
                inputs: ['phone_number', 'script', 'module_id'],
                outputs: ['call_initiated', 'call_result']
            },
            {
                id: 'data_filter',
                name: 'Data Filter',
                icon: '🔍',
                category: 'utility',
                description: 'Filter and process data',
                inputs: ['input_data', 'filter_criteria'],
                outputs: ['filtered_data', 'rejected_data']
            },
            {
                id: 'condition_check',
                name: 'Condition Check',
                icon: '❓',
                category: 'utility',
                description: 'Check conditions and branch flow',
                inputs: ['input_value', 'condition'],
                outputs: ['true_path', 'false_path']
            },
            {
                id: 'delay_timer',
                name: 'Delay Timer',
                icon: '⏰',
                category: 'utility',
                description: 'Add delays between actions',
                inputs: ['trigger', 'delay_duration'],
                outputs: ['delayed_trigger']
            },
            {
                id: 'webhook_trigger',
                name: 'Webhook Trigger',
                icon: '🔗',
                category: 'trigger',
                description: 'Trigger workflow from webhook',
                inputs: [],
                outputs: ['webhook_data', 'timestamp']
            },
            {
                id: 'schedule_trigger',
                name: 'Schedule Trigger',
                icon: '⏱️',
                category: 'trigger',
                description: 'Trigger workflow on schedule',
                inputs: ['schedule_config'],
                outputs: ['trigger_time', 'schedule_data']
            },
            {
                id: 'database_query',
                name: 'Database Query',
                icon: '🗄️',
                category: 'data',
                description: 'Query database for information',
                inputs: ['query_params'],
                outputs: ['query_results', 'row_count']
            }
        ];
        
        this.renderToolPalette(availableTools);
    }
    
    renderToolPalette(tools) {
        this.paletteContainer.innerHTML = '';
        
        tools.forEach(tool => {
            const toolElement = document.createElement('div');
            toolElement.className = 'palette-tool';
            toolElement.draggable = true;
            toolElement.dataset.toolId = tool.id;
            
            toolElement.innerHTML = `
                <span class="palette-tool-icon">${tool.icon}</span>
                <div class="palette-tool-info">
                    <div class="palette-tool-name">${tool.name}</div>
                    <div class="palette-tool-category">${tool.category}</div>
                </div>
            `;
            
            toolElement.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('application/json', JSON.stringify(tool));
            });
            
            this.paletteContainer.appendChild(toolElement);
        });
    }
    
    handleCanvasDrop(e) {
        e.preventDefault();
        
        try {
            const toolData = JSON.parse(e.dataTransfer.getData('application/json'));
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left - 75; // Center the node
            const y = e.clientY - rect.top - 40;
            
            this.createNode(toolData, x, y);
        } catch (error) {
            console.error('Error dropping tool:', error);
        }
    }
    
    createNode(toolData, x, y) {
        const nodeId = `node_${this.nodeIdCounter++}`;
        
        const node = {
            id: nodeId,
            toolId: toolData.id,
            name: toolData.name,
            icon: toolData.icon,
            category: toolData.category,
            description: toolData.description,
            inputs: toolData.inputs || [],
            outputs: toolData.outputs || [],
            x: Math.max(0, x),
            y: Math.max(0, y),
            config: {},
            connections: {
                inputs: new Map(),
                outputs: new Map()
            }
        };
        
        this.nodes.set(nodeId, node);
        this.renderNode(node);
        
        return node;
    }
    
    renderNode(node) {
        const nodeElement = document.createElement('div');
        nodeElement.className = 'workflow-node';
        nodeElement.dataset.nodeId = node.id;
        nodeElement.style.left = `${node.x}px`;
        nodeElement.style.top = `${node.y}px`;
        
        nodeElement.innerHTML = `
            <div class="node-header">
                <span class="node-icon">${node.icon}</span>
                <div class="node-title">${node.name}</div>
                <div class="node-actions">
                    <button class="node-action-btn" onclick="workflowBuilder.configureNode('${node.id}')" title="Configure">⚙️</button>
                    <button class="node-action-btn" onclick="workflowBuilder.deleteNode('${node.id}')" title="Delete">🗑️</button>
                </div>
            </div>
            <div class="node-body">
                <div class="node-inputs">
                    ${node.inputs.map(input => `
                        <div class="node-port input-port" data-port="${input}" data-type="input">
                            <div class="port-dot"></div>
                            <span class="port-label">${input}</span>
                        </div>
                    `).join('')}
                </div>
                <div class="node-outputs">
                    ${node.outputs.map(output => `
                        <div class="node-port output-port" data-port="${output}" data-type="output">
                            <span class="port-label">${output}</span>
                            <div class="port-dot"></div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        // Add event listeners
        this.setupNodeEventListeners(nodeElement, node);
        
        this.nodesContainer.appendChild(nodeElement);
    }
    
    setupNodeEventListeners(nodeElement, node) {
        // Node selection
        nodeElement.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectNode(node.id);
        });
        
        // Node dragging
        let isDragging = false;
        let dragOffset = { x: 0, y: 0 };
        
        nodeElement.addEventListener('mousedown', (e) => {
            if (e.target.closest('.node-action-btn') || e.target.closest('.node-port')) {
                return;
            }
            
            isDragging = true;
            this.draggedNode = node;
            
            const rect = nodeElement.getBoundingClientRect();
            const canvasRect = this.canvas.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;
            
            nodeElement.style.zIndex = '1000';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (isDragging && this.draggedNode === node) {
                const canvasRect = this.canvas.getBoundingClientRect();
                const newX = e.clientX - canvasRect.left - dragOffset.x;
                const newY = e.clientY - canvasRect.top - dragOffset.y;
                
                node.x = Math.max(0, Math.min(newX, this.canvas.clientWidth - 150));
                node.y = Math.max(0, Math.min(newY, this.canvas.clientHeight - 100));
                
                nodeElement.style.left = `${node.x}px`;
                nodeElement.style.top = `${node.y}px`;
                
                this.updateConnections();
            }
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                this.draggedNode = null;
                nodeElement.style.zIndex = '';
            }
        });
        
        // Port connection handling
        const ports = nodeElement.querySelectorAll('.node-port');
        ports.forEach(port => {
            port.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                this.startConnection(node.id, port.dataset.port, port.dataset.type);
            });
            
            port.addEventListener('mouseenter', (e) => {
                if (this.isConnecting) {
                    this.highlightPort(port, true);
                }
            });
            
            port.addEventListener('mouseleave', (e) => {
                if (this.isConnecting) {
                    this.highlightPort(port, false);
                }
            });
            
            port.addEventListener('mouseup', (e) => {
                if (this.isConnecting) {
                    e.stopPropagation();
                    this.endConnection(node.id, port.dataset.port, port.dataset.type);
                }
            });
        });
    }
    
    startConnection(nodeId, portName, portType) {
        if (portType === 'output') {
            this.isConnecting = true;
            this.connectionStart = { nodeId, portName, portType };
            
            // Create temporary connection line
            this.createTempConnection();
            
            document.addEventListener('mousemove', this.updateTempConnection.bind(this));
            document.addEventListener('mouseup', this.cancelConnection.bind(this));
        }
    }
    
    endConnection(nodeId, portName, portType) {
        if (this.isConnecting && this.connectionStart && portType === 'input') {
            const startNode = this.connectionStart.nodeId;
            const startPort = this.connectionStart.portName;
            const endNode = nodeId;
            const endPort = portName;
            
            // Prevent self-connection
            if (startNode !== endNode) {
                this.createConnection(startNode, startPort, endNode, endPort);
            }
        }
        
        this.cancelConnection();
    }
    
    createConnection(startNodeId, startPort, endNodeId, endPort) {
        const connectionId = `conn_${this.connectionIdCounter++}`;
        
        const connection = {
            id: connectionId,
            startNode: startNodeId,
            startPort: startPort,
            endNode: endNodeId,
            endPort: endPort,
            dataMapping: {}
        };
        
        // Remove existing connection to the input port
        this.removeConnectionsToPort(endNodeId, endPort);
        
        this.connections.set(connectionId, connection);
        
        // Update node connection maps
        const startNode = this.nodes.get(startNodeId);
        const endNode = this.nodes.get(endNodeId);
        
        if (!startNode.connections.outputs.has(startPort)) {
            startNode.connections.outputs.set(startPort, []);
        }
        startNode.connections.outputs.get(startPort).push(connectionId);
        
        endNode.connections.inputs.set(endPort, connectionId);
        
        this.renderConnection(connection);
        this.updateWorkflowValidation();
    }
    
    removeConnectionsToPort(nodeId, portName) {
        const connectionsToRemove = [];
        
        this.connections.forEach((connection, connectionId) => {
            if (connection.endNode === nodeId && connection.endPort === portName) {
                connectionsToRemove.push(connectionId);
            }
        });
        
        connectionsToRemove.forEach(connectionId => {
            this.removeConnection(connectionId);
        });
    }
    
    removeConnection(connectionId) {
        const connection = this.connections.get(connectionId);
        if (!connection) return;
        
        // Update node connection maps
        const startNode = this.nodes.get(connection.startNode);
        const endNode = this.nodes.get(connection.endNode);
        
        if (startNode) {
            const outputs = startNode.connections.outputs.get(connection.startPort);
            if (outputs) {
                const index = outputs.indexOf(connectionId);
                if (index > -1) {
                    outputs.splice(index, 1);
                }
            }
        }
        
        if (endNode) {
            endNode.connections.inputs.delete(connection.endPort);
        }
        
        // Remove visual connection
        const connectionElement = document.querySelector(`[data-connection-id="${connectionId}"]`);
        if (connectionElement) {
            connectionElement.remove();
        }
        
        this.connections.delete(connectionId);
        this.updateWorkflowValidation();
    }
    
    renderConnection(connection) {
        const startNode = this.nodes.get(connection.startNode);
        const endNode = this.nodes.get(connection.endNode);
        
        if (!startNode || !endNode) return;
        
        const startElement = document.querySelector(`[data-node-id="${connection.startNode}"] [data-port="${connection.startPort}"][data-type="output"]`);
        const endElement = document.querySelector(`[data-node-id="${connection.endNode}"] [data-port="${connection.endPort}"][data-type="input"]`);
        
        if (!startElement || !endElement) return;
        
        const startRect = startElement.getBoundingClientRect();
        const endRect = endElement.getBoundingClientRect();
        const canvasRect = this.canvas.getBoundingClientRect();
        
        const startX = startRect.right - canvasRect.left;
        const startY = startRect.top + startRect.height / 2 - canvasRect.top;
        const endX = endRect.left - canvasRect.left;
        const endY = endRect.top + endRect.height / 2 - canvasRect.top;
        
        // Create curved connection line
        const path = this.createConnectionPath(startX, startY, endX, endY);
        
        const pathElement = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        pathElement.setAttribute('d', path);
        pathElement.setAttribute('class', 'connection-line');
        pathElement.setAttribute('data-connection-id', connection.id);
        
        // Add click handler for connection selection/deletion
        pathElement.addEventListener('click', (e) => {
            e.stopPropagation();
            if (confirm('Delete this connection?')) {
                this.removeConnection(connection.id);
            }
        });
        
        this.connectionsContainer.appendChild(pathElement);
    }
    
    createConnectionPath(startX, startY, endX, endY) {
        const controlPointOffset = Math.abs(endX - startX) * 0.5;
        const cp1X = startX + controlPointOffset;
        const cp1Y = startY;
        const cp2X = endX - controlPointOffset;
        const cp2Y = endY;
        
        return `M ${startX} ${startY} C ${cp1X} ${cp1Y}, ${cp2X} ${cp2Y}, ${endX} ${endY}`;
    }
    
    updateConnections() {
        // Clear existing connection visuals
        this.connectionsContainer.innerHTML = '';
        
        // Re-render all connections
        this.connections.forEach(connection => {
            this.renderConnection(connection);
        });
    }
    
    createTempConnection() {
        this.tempConnection = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        this.tempConnection.setAttribute('class', 'connection-line temp-connection');
        this.tempConnection.style.stroke = 'var(--accent-color)';
        this.tempConnection.style.strokeDasharray = '5,5';
        this.connectionsContainer.appendChild(this.tempConnection);
    }
    
    updateTempConnection(e) {
        if (!this.isConnecting || !this.tempConnection || !this.connectionStart) return;
        
        const startElement = document.querySelector(`[data-node-id="${this.connectionStart.nodeId}"] [data-port="${this.connectionStart.portName}"][data-type="output"]`);
        if (!startElement) return;
        
        const startRect = startElement.getBoundingClientRect();
        const canvasRect = this.canvas.getBoundingClientRect();
        
        const startX = startRect.right - canvasRect.left;
        const startY = startRect.top + startRect.height / 2 - canvasRect.top;
        const endX = e.clientX - canvasRect.left;
        const endY = e.clientY - canvasRect.top;
        
        const path = this.createConnectionPath(startX, startY, endX, endY);
        this.tempConnection.setAttribute('d', path);
    }
    
    cancelConnection() {
        this.isConnecting = false;
        this.connectionStart = null;
        
        if (this.tempConnection) {
            this.tempConnection.remove();
            this.tempConnection = null;
        }
        
        document.removeEventListener('mousemove', this.updateTempConnection.bind(this));
        document.removeEventListener('mouseup', this.cancelConnection.bind(this));
        
        // Remove port highlights
        document.querySelectorAll('.node-port.highlighted').forEach(port => {
            port.classList.remove('highlighted');
        });
    }
    
    highlightPort(port, highlight) {
        if (highlight) {
            port.classList.add('highlighted');
        } else {
            port.classList.remove('highlighted');
        }
    }
    
    selectNode(nodeId) {
        // Remove previous selection
        document.querySelectorAll('.workflow-node.selected').forEach(node => {
            node.classList.remove('selected');
        });
        
        // Select new node
        const nodeElement = document.querySelector(`[data-node-id="${nodeId}"]`);
        if (nodeElement) {
            nodeElement.classList.add('selected');
            this.selectedNode = nodeId;
            this.showNodeProperties(nodeId);
        }
    }
    
    showNodeProperties(nodeId) {
        const node = this.nodes.get(nodeId);
        if (!node) return;
        
        const propertiesContent = this.propertiesPanel.querySelector('.properties-content');
        propertiesContent.innerHTML = `
            <div class="property-group">
                <label class="property-label">Node Name</label>
                <input type="text" class="property-input" value="${node.name}" 
                       onchange="workflowBuilder.updateNodeProperty('${nodeId}', 'name', this.value)">
            </div>
            
            <div class="property-group">
                <label class="property-label">Description</label>
                <textarea class="property-input" rows="3" 
                          onchange="workflowBuilder.updateNodeProperty('${nodeId}', 'description', this.value)">${node.description}</textarea>
            </div>
            
            <div class="property-group">
                <label class="property-label">Configuration</label>
                <div class="config-fields" id="configFields_${nodeId}">
                    ${this.renderConfigFields(node)}
                </div>
            </div>
            
            <div class="property-group">
                <label class="property-label">Connections</label>
                <div class="connection-info">
                    <div class="input-connections">
                        <strong>Inputs:</strong>
                        ${Array.from(node.connections.inputs.entries()).map(([port, connectionId]) => {
                            const connection = this.connections.get(connectionId);
                            const sourceNode = this.nodes.get(connection.startNode);
                            return `<div class="connection-item">${port} ← ${sourceNode.name}.${connection.startPort}</div>`;
                        }).join('')}
                    </div>
                    <div class="output-connections">
                        <strong>Outputs:</strong>
                        ${Array.from(node.connections.outputs.entries()).map(([port, connectionIds]) => {
                            return connectionIds.map(connectionId => {
                                const connection = this.connections.get(connectionId);
                                const targetNode = this.nodes.get(connection.endNode);
                                return `<div class="connection-item">${port} → ${targetNode.name}.${connection.endPort}</div>`;
                            }).join('');
                        }).join('')}
                    </div>
                </div>
            </div>
        `;
    }
    
    renderConfigFields(node) {
        const commonFields = {
            'customer_followup': [
                { name: 'message_template', type: 'textarea', label: 'Message Template', placeholder: 'Hello {name}, we wanted to follow up...' },
                { name: 'follow_up_delay', type: 'number', label: 'Delay (hours)', placeholder: '24' }
            ],
            'lead_scoring': [
                { name: 'scoring_criteria', type: 'textarea', label: 'Scoring Criteria (JSON)', placeholder: '{"engagement": 40, "budget": 30, "company": 20, "industry": 10}' }
            ],
            'appointment_scheduler': [
                { name: 'available_hours', type: 'text', label: 'Available Hours', placeholder: '9:00-17:00' },
                { name: 'timezone', type: 'text', label: 'Timezone', placeholder: 'UTC' }
            ],
            'sms_sender': [
                { name: 'default_module', type: 'select', label: 'Default Module', options: ['module1', 'module2', 'module3'] }
            ],
            'call_maker': [
                { name: 'default_module', type: 'select', label: 'Default Module', options: ['module1', 'module2', 'module3'] },
                { name: 'max_attempts', type: 'number', label: 'Max Attempts', placeholder: '3' }
            ],
            'condition_check': [
                { name: 'condition_type', type: 'select', label: 'Condition Type', options: ['equals', 'greater_than', 'less_than', 'contains'] },
                { name: 'condition_value', type: 'text', label: 'Condition Value', placeholder: 'Value to compare' }
            ],
            'delay_timer': [
                { name: 'delay_duration', type: 'number', label: 'Delay Duration (seconds)', placeholder: '300' }
            ]
        };
        
        const fields = commonFields[node.toolId] || [];
        
        return fields.map(field => {
            const value = node.config[field.name] || '';
            
            if (field.type === 'select') {
                return `
                    <div class="config-field">
                        <label class="property-label">${field.label}</label>
                        <select class="property-input" onchange="workflowBuilder.updateNodeConfig('${node.id}', '${field.name}', this.value)">
                            <option value="">Select ${field.label}</option>
                            ${field.options.map(option => `
                                <option value="${option}" ${value === option ? 'selected' : ''}>${option}</option>
                            `).join('')}
                        </select>
                    </div>
                `;
            } else if (field.type === 'textarea') {
                return `
                    <div class="config-field">
                        <label class="property-label">${field.label}</label>
                        <textarea class="property-input" rows="3" placeholder="${field.placeholder}"
                                  onchange="workflowBuilder.updateNodeConfig('${node.id}', '${field.name}', this.value)">${value}</textarea>
                    </div>
                `;
            } else {
                return `
                    <div class="config-field">
                        <label class="property-label">${field.label}</label>
                        <input type="${field.type}" class="property-input" value="${value}" placeholder="${field.placeholder}"
                               onchange="workflowBuilder.updateNodeConfig('${node.id}', '${field.name}', this.value)">
                    </div>
                `;
            }
        }).join('');
    }
    
    updateNodeProperty(nodeId, property, value) {
        const node = this.nodes.get(nodeId);
        if (node) {
            node[property] = value;
            
            // Update visual representation if needed
            if (property === 'name') {
                const nodeElement = document.querySelector(`[data-node-id="${nodeId}"] .node-title`);
                if (nodeElement) {
                    nodeElement.textContent = value;
                }
            }
        }
    }
    
    updateNodeConfig(nodeId, configKey, value) {
        const node = this.nodes.get(nodeId);
        if (node) {
            node.config[configKey] = value;
        }
    }
    
    configureNode(nodeId) {
        const node = this.nodes.get(nodeId);
        if (!node) return;
        
        // Open configuration modal
        const modal = document.getElementById('toolConfigModal');
        const title = document.getElementById('toolConfigTitle');
        const content = document.getElementById('toolConfigContent');
        
        title.textContent = `Configure ${node.name}`;
        
        content.innerHTML = `
            <div class="config-section">
                <h4>Basic Settings</h4>
                ${this.renderConfigFields(node)}
            </div>
            
            <div class="config-section">
                <h4>Advanced Settings</h4>
                <div class="config-field">
                    <label class="property-label">Execution Timeout (seconds)</label>
                    <input type="number" class="property-input" value="${node.config.timeout || 30}" 
                           onchange="workflowBuilder.updateNodeConfig('${nodeId}', 'timeout', this.value)">
                </div>
                
                <div class="config-field">
                    <label class="property-label">Retry Count</label>
                    <input type="number" class="property-input" value="${node.config.retries || 0}" 
                           onchange="workflowBuilder.updateNodeConfig('${nodeId}', 'retries', this.value)">
                </div>
                
                <div class="config-field">
                    <label class="property-label">Error Handling</label>
                    <select class="property-input" onchange="workflowBuilder.updateNodeConfig('${nodeId}', 'error_handling', this.value)">
                        <option value="stop" ${node.config.error_handling === 'stop' ? 'selected' : ''}>Stop Workflow</option>
                        <option value="continue" ${node.config.error_handling === 'continue' ? 'selected' : ''}>Continue</option>
                        <option value="retry" ${node.config.error_handling === 'retry' ? 'selected' : ''}>Retry</option>
                    </select>
                </div>
            </div>
        `;
        
        modal.style.display = 'block';
        this.currentConfigNode = nodeId;
    }
    
    saveToolConfiguration() {
        if (this.currentConfigNode) {
            const node = this.nodes.get(this.currentConfigNode);
            if (node) {
                showNotification(`Configuration saved for ${node.name}`, 'success');
            }
        }
        
        closeModal('toolConfigModal');
        this.currentConfigNode = null;
    }
    
    deleteNode(nodeId) {
        if (confirm('Are you sure you want to delete this node?')) {
            // Remove all connections to/from this node
            const connectionsToRemove = [];
            this.connections.forEach((connection, connectionId) => {
                if (connection.startNode === nodeId || connection.endNode === nodeId) {
                    connectionsToRemove.push(connectionId);
                }
            });
            
            connectionsToRemove.forEach(connectionId => {
                this.removeConnection(connectionId);
            });
            
            // Remove node element
            const nodeElement = document.querySelector(`[data-node-id="${nodeId}"]`);
            if (nodeElement) {
                nodeElement.remove();
            }
            
            // Remove from nodes map
            this.nodes.delete(nodeId);
            
            // Clear properties panel if this node was selected
            if (this.selectedNode === nodeId) {
                this.selectedNode = null;
                const propertiesContent = this.propertiesPanel.querySelector('.properties-content');
                propertiesContent.innerHTML = '<p>Select a node to edit its properties</p>';
            }
            
            this.updateWorkflowValidation();
        }
    }
    
    handleCanvasClick(e) {
        if (e.target === this.canvas || e.target.classList.contains('canvas-grid')) {
            // Deselect all nodes
            document.querySelectorAll('.workflow-node.selected').forEach(node => {
                node.classList.remove('selected');
            });
            
            this.selectedNode = null;
            const propertiesContent = this.propertiesPanel.querySelector('.properties-content');
            propertiesContent.innerHTML = '<p>Select a node to edit its properties</p>';
        }
    }
    
    handleKeyDown(e) {
        if (e.key === 'Delete' && this.selectedNode) {
            this.deleteNode(this.selectedNode);
        } else if (e.key === 'Escape') {
            this.cancelConnection();
        }
    }
    
    updateWorkflowValidation() {
        // Validate workflow for cycles, orphaned nodes, etc.
        const validation = this.validateWorkflow();
        
        // Update UI based on validation results
        document.querySelectorAll('.workflow-node').forEach(nodeElement => {
            nodeElement.classList.remove('error', 'warning');
        });
        
        validation.errors.forEach(error => {
            const nodeElement = document.querySelector(`[data-node-id="${error.nodeId}"]`);
            if (nodeElement) {
                nodeElement.classList.add('error');
                nodeElement.title = error.message;
            }
        });
        
        validation.warnings.forEach(warning => {
            const nodeElement = document.querySelector(`[data-node-id="${warning.nodeId}"]`);
            if (nodeElement) {
                nodeElement.classList.add('warning');
                nodeElement.title = warning.message;
            }
        });
    }
    
    validateWorkflow() {
        const errors = [];
        const warnings = [];
        
        // Check for cycles
        const visited = new Set();
        const recursionStack = new Set();
        
        const hasCycle = (nodeId) => {
            if (recursionStack.has(nodeId)) {
                return true;
            }
            if (visited.has(nodeId)) {
                return false;
            }
            
            visited.add(nodeId);
            recursionStack.add(nodeId);
            
            const node = this.nodes.get(nodeId);
            if (node) {
                for (const [port, connectionIds] of node.connections.outputs) {
                    for (const connectionId of connectionIds) {
                        const connection = this.connections.get(connectionId);
                        if (connection && hasCycle(connection.endNode)) {
                            return true;
                        }
                    }
                }
            }
            
            recursionStack.delete(nodeId);
            return false;
        };
        
        // Check each node for cycles
        for (const nodeId of this.nodes.keys()) {
            if (!visited.has(nodeId) && hasCycle(nodeId)) {
                errors.push({
                    nodeId: nodeId,
                    message: 'Circular dependency detected'
                });
            }
        }
        
        // Check for orphaned nodes (no inputs and no outputs)
        this.nodes.forEach((node, nodeId) => {
            const hasInputs = node.connections.inputs.size > 0;
            const hasOutputs = node.connections.outputs.size > 0;
            
            if (!hasInputs && !hasOutputs && !node.toolId.includes('trigger')) {
                warnings.push({
                    nodeId: nodeId,
                    message: 'Node has no connections'
                });
            }
        });
        
        return { errors, warnings };
    }
    
    exportWorkflow() {
        const workflow = {
            nodes: Array.from(this.nodes.values()),
            connections: Array.from(this.connections.values()),
            metadata: {
                name: 'Untitled Workflow',
                description: '',
                version: '1.0',
                created: new Date().toISOString()
            }
        };
        
        return workflow;
    }
    
    importWorkflow(workflowData) {
        // Clear existing workflow
        this.clearWorkflow();
        
        // Import nodes
        workflowData.nodes.forEach(nodeData => {
            const node = {
                ...nodeData,
                connections: {
                    inputs: new Map(),
                    outputs: new Map()
                }
            };
            this.nodes.set(node.id, node);
            this.renderNode(node);
        });
        
        // Import connections
        workflowData.connections.forEach(connectionData => {
            const connection = { ...connectionData };
            this.connections.set(connection.id, connection);
            
            // Update node connection maps
            const startNode = this.nodes.get(connection.startNode);
            const endNode = this.nodes.get(connection.endNode);
            
            if (startNode && endNode) {
                if (!startNode.connections.outputs.has(connection.startPort)) {
                    startNode.connections.outputs.set(connection.startPort, []);
                }
                startNode.connections.outputs.get(connection.startPort).push(connection.id);
                endNode.connections.inputs.set(connection.endPort, connection.id);
                
                this.renderConnection(connection);
            }
        });
        
        this.updateWorkflowValidation();
    }
    
    clearWorkflow() {
        this.nodes.clear();
        this.connections.clear();
        this.nodesContainer.innerHTML = '';
        this.connectionsContainer.innerHTML = '';
        this.selectedNode = null;
        
        const propertiesContent = this.propertiesPanel.querySelector('.properties-content');
        propertiesContent.innerHTML = '<p>Select a node to edit its properties</p>';
    }
    
    createSampleWorkflow() {
        // Create a sample workflow to demonstrate the system
        const triggerNode = this.createNode({
            id: 'webhook_trigger',
            name: 'New Lead Webhook',
            icon: '🔗',
            category: 'trigger',
            description: 'Triggered when new lead comes in',
            inputs: [],
            outputs: ['webhook_data', 'timestamp']
        }, 50, 50);
        
        const scoringNode = this.createNode({
            id: 'lead_scoring',
            name: 'Score Lead',
            icon: '🎯',
            category: 'sales',
            description: 'Score the incoming lead',
            inputs: ['lead_data'],
            outputs: ['score', 'grade', 'next_action']
        }, 300, 50);
        
        const conditionNode = this.createNode({
            id: 'condition_check',
            name: 'High Score?',
            icon: '❓',
            category: 'utility',
            description: 'Check if score is high enough',
            inputs: ['input_value', 'condition'],
            outputs: ['true_path', 'false_path']
        }, 550, 50);
        
        const callNode = this.createNode({
            id: 'call_maker',
            name: 'Make Call',
            icon: '📱',
            category: 'communication',
            description: 'Call high-value leads',
            inputs: ['phone_number', 'script', 'module_id'],
            outputs: ['call_initiated', 'call_result']
        }, 800, 20);
        
        const smsNode = this.createNode({
            id: 'sms_sender',
            name: 'Send SMS',
            icon: '💬',
            category: 'communication',
            description: 'Send SMS to lower-value leads',
            inputs: ['phone_number', 'message', 'module_id'],
            outputs: ['sms_sent', 'delivery_status']
        }, 800, 120);
        
        // Create connections
        setTimeout(() => {
            this.createConnection(triggerNode.id, 'webhook_data', scoringNode.id, 'lead_data');
            this.createConnection(scoringNode.id, 'score', conditionNode.id, 'input_value');
            this.createConnection(conditionNode.id, 'true_path', callNode.id, 'phone_number');
            this.createConnection(conditionNode.id, 'false_path', smsNode.id, 'phone_number');
        }, 100);
    }
    
    executeWorkflow(startNodeId, inputData) {
        // This would integrate with the backend to execute the workflow
        console.log('Executing workflow starting from node:', startNodeId, 'with data:', inputData);
        
        // Show execution visualization
        this.visualizeExecution(startNodeId);
    }
    
    visualizeExecution(nodeId) {
        const nodeElement = document.querySelector(`[data-node-id="${nodeId}"]`);
        if (nodeElement) {
            nodeElement.classList.add('executing');
            
            setTimeout(() => {
                nodeElement.classList.remove('executing');
                nodeElement.classList.add('executed');
                
                setTimeout(() => {
                    nodeElement.classList.remove('executed');
                }, 2000);
            }, 1000);
        }
    }
}

// Initialize workflow builder when DOM is loaded
let workflowBuilder;

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('workflowCanvas')) {
        workflowBuilder = new WorkflowBuilder();
    }
});

// Global functions for UI interactions
function createNewWorkflow() {
    if (workflowBuilder) {
        if (confirm('Create a new workflow? This will clear the current workflow.')) {
            workflowBuilder.clearWorkflow();
            showNotification('New workflow created', 'success');
        }
    }
}

function importWorkflow() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const workflowData = JSON.parse(e.target.result);
                    workflowBuilder.importWorkflow(workflowData);
                    showNotification('Workflow imported successfully', 'success');
                } catch (error) {
                    showNotification('Failed to import workflow: Invalid file format', 'error');
                }
            };
            reader.readAsText(file);
        }
    };
    
    input.click();
}

function exportWorkflow() {
    if (workflowBuilder) {
        const workflow = workflowBuilder.exportWorkflow();
        const dataStr = JSON.stringify(workflow, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = 'workflow.json';
        link.click();
        
        showNotification('Workflow exported', 'success');
    }
}

function executeWorkflow() {
    if (workflowBuilder) {
        // Find trigger nodes
        const triggerNodes = Array.from(workflowBuilder.nodes.values())
            .filter(node => node.toolId.includes('trigger'));
        
        if (triggerNodes.length === 0) {
            showNotification('No trigger nodes found in workflow', 'warning');
            return;
        }
        
        // Execute from first trigger
        const startNode = triggerNodes[0];
        workflowBuilder.executeWorkflow(startNode.id, {});
        showNotification('Workflow execution started', 'success');
    }
}