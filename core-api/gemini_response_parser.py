"""
Gemini Response Parser for AI Agent Tools
Parses Gemini responses and extracts actionable tool operations
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class GeminiResponseParser:
    """
    Parser for Gemini AI responses to extract tool operations and actions
    """
    
    def __init__(self):
        self.tool_patterns = self._initialize_tool_patterns()
        self.action_patterns = self._initialize_action_patterns()
        
    def _initialize_tool_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for recognizing tool mentions"""
        return {
            'call_automation': [
                r'call\s+automation', r'automated\s+calling', r'call\s+workflows',
                r'phone\s+automation', r'dialing\s+system'
            ],
            'sms_campaigns': [
                r'sms\s+campaigns?', r'text\s+messaging', r'bulk\s+sms',
                r'sms\s+automation', r'text\s+campaigns?'
            ],
            'analytics': [
                r'analytics', r'performance\s+tracking', r'reporting',
                r'metrics', r'dashboard', r'insights'
            ],
            'lead_scoring': [
                r'lead\s+scoring', r'lead\s+qualification', r'lead\s+ranking',
                r'prospect\s+scoring', r'lead\s+prioritization'
            ],
            'appointment_booking': [
                r'appointment\s+booking', r'scheduling', r'calendar\s+booking',
                r'meeting\s+scheduling', r'appointment\s+scheduling'
            ],
            'follow_up': [
                r'follow[\-\s]?up', r'customer\s+follow[\-\s]?up', r'follow[\-\s]?up\s+automation',
                r'nurturing', r'customer\s+retention'
            ]
        }
    
    def _initialize_action_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for recognizing actions"""
        return {
            'create': [
                r'create', r'build', r'set\s+up', r'establish', r'generate',
                r'make', r'add', r'new', r'configure'
            ],
            'edit': [
                r'edit', r'modify', r'update', r'change', r'adjust',
                r'configure', r'customize', r'alter'
            ],
            'delete': [
                r'delete', r'remove', r'eliminate', r'disable', r'deactivate',
                r'turn\s+off', r'stop', r'cancel'
            ],
            'connect': [
                r'connect', r'link', r'integrate', r'chain', r'combine',
                r'join', r'merge', r'tie\s+together', r'workflow'
            ],
            'analyze': [
                r'analyze', r'suggest', r'recommend', r'review', r'assess',
                r'evaluate', r'examine', r'study'
            ]
        }
    
    def parse_response(self, user_message: str, gemini_response: str) -> Dict[str, Any]:
        """
        Parse Gemini response and extract tool operations
        
        Args:
            user_message: Original user message
            gemini_response: Gemini AI response
            
        Returns:
            Dict containing parsed operations and metadata
        """
        try:
            # Extract tool mentions
            mentioned_tools = self._extract_tools(user_message + " " + gemini_response)
            
            # Extract actions
            detected_actions = self._extract_actions(user_message)
            
            # Extract tool connections
            connections = self._extract_connections(user_message, gemini_response)
            
            # Extract configuration parameters
            configurations = self._extract_configurations(gemini_response)
            
            # Determine primary operation
            primary_operation = self._determine_primary_operation(detected_actions, mentioned_tools)
            
            # Extract success indicators
            success_indicators = self._extract_success_indicators(gemini_response)
            
            # Parse structured data if present
            structured_data = self._extract_structured_data(gemini_response)
            
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'parsing_results': {
                    'mentioned_tools': mentioned_tools,
                    'detected_actions': detected_actions,
                    'connections': connections,
                    'configurations': configurations,
                    'primary_operation': primary_operation,
                    'success_indicators': success_indicators,
                    'structured_data': structured_data
                },
                'actionable_items': self._generate_actionable_items(
                    primary_operation, mentioned_tools, connections, configurations
                ),
                'metadata': {
                    'user_message_length': len(user_message),
                    'response_length': len(gemini_response),
                    'tools_count': len(mentioned_tools),
                    'actions_count': len(detected_actions),
                    'connections_count': len(connections)
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _extract_tools(self, text: str) -> List[Dict[str, Any]]:
        """Extract mentioned tools from text"""
        mentioned_tools = []
        text_lower = text.lower()
        
        for tool_name, patterns in self.tool_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    mentioned_tools.append({
                        'name': tool_name,
                        'display_name': tool_name.replace('_', ' ').title(),
                        'pattern_matched': pattern,
                        'confidence': 0.8
                    })
                    break  # Only add each tool once
        
        return mentioned_tools
    
    def _extract_actions(self, text: str) -> List[Dict[str, Any]]:
        """Extract actions from text"""
        detected_actions = []
        text_lower = text.lower()
        
        for action_name, patterns in self.action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    detected_actions.append({
                        'action': action_name,
                        'pattern_matched': pattern,
                        'confidence': 0.9
                    })
                    break  # Only add each action once
        
        return detected_actions
    
    def _extract_connections(self, user_message: str, gemini_response: str) -> List[Dict[str, Any]]:
        """Extract tool connections from messages"""
        connections = []
        combined_text = user_message + " " + gemini_response
        text_lower = combined_text.lower()
        
        # Look for connection patterns
        connection_patterns = [
            r'connect\s+(\w+(?:\s+\w+)*)\s+to\s+(\w+(?:\s+\w+)*)',
            r'link\s+(\w+(?:\s+\w+)*)\s+with\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+→\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+->\s+(\w+(?:\s+\w+)*)',
            r'chain\s+(\w+(?:\s+\w+)*)\s+and\s+(\w+(?:\s+\w+)*)'
        ]
        
        for pattern in connection_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                source_tool = match.group(1).strip()
                target_tool = match.group(2).strip()
                
                connections.append({
                    'source_tool': source_tool,
                    'target_tool': target_tool,
                    'connection_type': 'workflow',
                    'pattern_matched': pattern,
                    'confidence': 0.85
                })
        
        return connections
    
    def _extract_configurations(self, text: str) -> Dict[str, Any]:
        """Extract configuration parameters from text"""
        configurations = {}
        
        # Look for configuration patterns
        config_patterns = {
            'threshold': r'threshold[:\s]+(\d+(?:\.\d+)?)',
            'timing': r'(?:within|after|every)\s+(\d+)\s+(minutes?|hours?|days?)',
            'score': r'score[:\s]+(\d+(?:\.\d+)?)',
            'percentage': r'(\d+(?:\.\d+)?)%',
            'temperature': r'temperature[:\s]+(\d+(?:\.\d+)?)',
            'max_tokens': r'(?:max[_\s]?tokens?|token[_\s]?limit)[:\s]+(\d+)'
        }
        
        text_lower = text.lower()
        for config_name, pattern in config_patterns.items():
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                configurations[config_name] = match.group(1)
        
        return configurations
    
    def _determine_primary_operation(self, actions: List[Dict], tools: List[Dict]) -> Optional[Dict[str, Any]]:
        """Determine the primary operation from detected actions and tools"""
        if not actions:
            return None
        
        # Priority order for actions
        action_priority = ['create', 'connect', 'edit', 'delete', 'analyze']
        
        for priority_action in action_priority:
            for action in actions:
                if action['action'] == priority_action:
                    return {
                        'action': priority_action,
                        'tools_involved': [tool['name'] for tool in tools],
                        'confidence': action['confidence']
                    }
        
        return actions[0] if actions else None
    
    def _extract_success_indicators(self, text: str) -> List[str]:
        """Extract success indicators from response"""
        success_patterns = [
            r'✅', r'successfully', r'completed', r'created', r'configured',
            r'established', r'connected', r'activated', r'enabled'
        ]
        
        indicators = []
        text_lower = text.lower()
        
        for pattern in success_patterns:
            if re.search(pattern, text_lower):
                indicators.append(pattern)
        
        return indicators
    
    def _extract_structured_data(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract structured data (JSON, tables, etc.) from response"""
        try:
            # Look for JSON blocks
            json_pattern = r'```json\s*(.*?)\s*```'
            json_matches = re.finditer(json_pattern, text, re.DOTALL)
            
            for match in json_matches:
                try:
                    json_data = json.loads(match.group(1))
                    return {'type': 'json', 'data': json_data}
                except json.JSONDecodeError:
                    continue
            
            # Look for configuration blocks
            config_pattern = r'\*\*Configuration:\*\*(.*?)(?=\*\*|$)'
            config_matches = re.finditer(config_pattern, text, re.DOTALL)
            
            for match in config_matches:
                config_text = match.group(1).strip()
                return {'type': 'configuration', 'data': config_text}
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return None
    
    def _generate_actionable_items(self, primary_operation: Optional[Dict], 
                                 tools: List[Dict], connections: List[Dict], 
                                 configurations: Dict) -> List[Dict[str, Any]]:
        """Generate actionable items based on parsed data"""
        actionable_items = []
        
        if primary_operation:
            action = primary_operation['action']
            
            if action == 'create' and tools:
                for tool in tools:
                    actionable_items.append({
                        'type': 'create_tool',
                        'tool_name': tool['name'],
                        'description': f"Create {tool['display_name']} tool",
                        'priority': 'high',
                        'estimated_time': '15-30 minutes'
                    })
            
            elif action == 'connect' and connections:
                for connection in connections:
                    actionable_items.append({
                        'type': 'create_connection',
                        'source_tool': connection['source_tool'],
                        'target_tool': connection['target_tool'],
                        'description': f"Connect {connection['source_tool']} to {connection['target_tool']}",
                        'priority': 'medium',
                        'estimated_time': '10-20 minutes'
                    })
            
            elif action == 'edit' and tools:
                for tool in tools:
                    actionable_items.append({
                        'type': 'edit_tool',
                        'tool_name': tool['name'],
                        'description': f"Edit {tool['display_name']} configuration",
                        'priority': 'medium',
                        'estimated_time': '5-15 minutes'
                    })
            
            elif action == 'delete' and tools:
                for tool in tools:
                    actionable_items.append({
                        'type': 'delete_tool',
                        'tool_name': tool['name'],
                        'description': f"Delete {tool['display_name']} tool",
                        'priority': 'low',
                        'estimated_time': '2-5 minutes'
                    })
        
        return actionable_items
    
    def get_parsing_statistics(self) -> Dict[str, Any]:
        """Get statistics about parsing capabilities"""
        return {
            'supported_tools': list(self.tool_patterns.keys()),
            'supported_actions': list(self.action_patterns.keys()),
            'total_patterns': sum(len(patterns) for patterns in self.tool_patterns.values()) + 
                            sum(len(patterns) for patterns in self.action_patterns.values()),
            'version': '1.0.0'
        }