"""
Business Consultation Analysis Service

This service analyzes client consultations and creates personalized AI tool chains
based on their business needs. It specializes in understanding different business
types and recommending the most relevant automation tools.
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import uuid

import structlog
from sqlmodel import Session, select
import google.generativeai as genai

from config import CoreAPIConfig, get_api_keys
from models import (
    User, TemporaryPhoneAssignment, Subscription, SubscriptionStatus,
    Call, ConversationContext, AIToolChain, AIToolChainStep
)
from agentic_function_manager import AgenticFunctionManager

logger = structlog.get_logger(__name__)


class BusinessType:
    """Business type classifications with relevant tools."""
    
    HOTEL = {
        "name": "Hotel/Hospitality",
        "keywords": ["hotel", "гостиница", "отель", "номер", "бронирование", "reception", "guest"],
        "tools": [
            "hotel_booking", "calendar_management", "customer_followup", 
            "email_automation", "sms_automation", "payment_processing",
            "review_management", "inventory_management"
        ],
        "description": "Hotel and hospitality business automation"
    }
    
    RESTAURANT = {
        "name": "Restaurant/Food Service",
        "keywords": ["ресторан", "кафе", "еда", "заказ", "доставка", "menu", "food"],
        "tools": [
            "order_management", "delivery_coordination", "customer_followup",
            "inventory_management", "payment_processing", "review_management",
            "social_media_management", "email_automation"
        ],
        "description": "Restaurant and food service automation"
    }
    
    RETAIL = {
        "name": "Retail/E-commerce",
        "keywords": ["магазин", "продажи", "товар", "склад", "shop", "store", "product"],
        "tools": [
            "inventory_management", "order_management", "customer_followup",
            "email_automation", "social_media_management", "payment_processing",
            "analytics_reporting", "lead_generation"
        ],
        "description": "Retail and e-commerce automation"
    }
    
    HEALTHCARE = {
        "name": "Healthcare/Medical",
        "keywords": ["клиника", "врач", "медицина", "прием", "doctor", "medical", "clinic"],
        "tools": [
            "appointment_scheduling", "patient_followup", "sms_automation",
            "email_automation", "document_management", "calendar_management",
            "reminder_system", "analytics_reporting"
        ],
        "description": "Healthcare and medical practice automation"
    }
    
    BEAUTY = {
        "name": "Beauty/Salon",
        "keywords": ["салон", "красота", "стрижка", "маникюр", "beauty", "salon", "spa"],
        "tools": [
            "appointment_scheduling", "customer_followup", "sms_automation",
            "social_media_management", "review_management", "payment_processing",
            "inventory_management", "email_automation"
        ],
        "description": "Beauty salon and spa automation"
    }
    
    EDUCATION = {
        "name": "Education/Training",
        "keywords": ["школа", "курсы", "обучение", "урок", "education", "training", "course"],
        "tools": [
            "course_management", "student_followup", "email_automation",
            "calendar_management", "document_management", "payment_processing",
            "analytics_reporting", "communication_tools"
        ],
        "description": "Educational services automation"
    }
    
    REAL_ESTATE = {
        "name": "Real Estate",
        "keywords": ["недвижимость", "квартира", "дом", "аренда", "real estate", "property"],
        "tools": [
            "property_search", "lead_generation", "customer_followup",
            "document_management", "calendar_management", "email_automation",
            "sms_automation", "analytics_reporting"
        ],
        "description": "Real estate business automation"
    }
    
    CONSULTING = {
        "name": "Consulting/Professional Services",
        "keywords": ["консультации", "услуги", "консалтинг", "consulting", "service", "advice"],
        "tools": [
            "appointment_scheduling", "document_management", "email_automation",
            "customer_followup", "calendar_management", "payment_processing",
            "analytics_reporting", "communication_tools"
        ],
        "description": "Professional consulting services automation"
    }

    @classmethod
    def get_all_types(cls) -> List[Dict[str, Any]]:
        """Get all business types."""
        return [
            cls.HOTEL, cls.RESTAURANT, cls.RETAIL, cls.HEALTHCARE,
            cls.BEAUTY, cls.EDUCATION, cls.REAL_ESTATE, cls.CONSULTING
        ]


class ConsultationAnalysisService:
    """
    Service for analyzing business consultations and creating AI tool chains.
    
    This service processes conversation transcripts, identifies business needs,
    and creates personalized automation tool chains for clients.
    """
    
    def __init__(self, config: CoreAPIConfig, engine):
        self.config = config
        self.engine = engine
        self.api_keys = get_api_keys()
        
        # Initialize Gemini
        if self.api_keys.gemini_api_key:
            genai.configure(api_key=self.api_keys.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None
            logger.warning("Gemini API key not configured")
    
    async def analyze_consultation(
        self, 
        user_id: str, 
        conversation_transcript: str,
        call_duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Analyze consultation conversation and generate recommendations.
        
        Args:
            user_id: User ID
            conversation_transcript: Full conversation transcript
            call_duration_minutes: Duration of the call
            
        Returns:
            Analysis results with business type, needs, and tool recommendations
        """
        try:
            # Extract business information using Gemini
            business_analysis = await self._analyze_business_with_gemini(conversation_transcript)
            
            # Identify business type
            business_type = self._identify_business_type(conversation_transcript, business_analysis)
            
            # Extract specific needs and pain points
            client_needs = self._extract_client_needs(conversation_transcript, business_analysis)
            
            # Generate tool recommendations
            recommended_tools = self._recommend_tools(business_type, client_needs)
            
            # Create automation workflow
            automation_workflow = self._create_automation_workflow(recommended_tools, client_needs)
            
            # Calculate pricing
            pricing = self._calculate_pricing(recommended_tools, business_type)
            
            # Generate summary
            summary = self._generate_consultation_summary(
                business_type, client_needs, recommended_tools, call_duration_minutes
            )
            
            analysis_result = {
                "user_id": user_id,
                "business_type": business_type,
                "client_needs": client_needs,
                "recommended_tools": recommended_tools,
                "automation_workflow": automation_workflow,
                "pricing": pricing,
                "summary": summary,
                "confidence_score": business_analysis.get("confidence", 0.8),
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            # Save analysis to database
            await self._save_analysis_to_db(user_id, analysis_result)
            
            logger.info("Consultation analyzed", 
                       user_id=user_id, 
                       business_type=business_type["name"],
                       tools_count=len(recommended_tools))
            
            return {
                "success": True,
                "analysis": analysis_result
            }
            
        except Exception as e:
            logger.error("Consultation analysis failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_business_with_gemini(self, transcript: str) -> Dict[str, Any]:
        """Use Gemini to analyze business from conversation transcript."""
        if not self.gemini_model:
            return {"confidence": 0.5, "analysis": "Gemini not available"}
        
        try:
            prompt = f"""
            Analyze this business consultation conversation and extract key information:
            
            Conversation: {transcript}
            
            Please provide a JSON response with:
            1. business_type: What type of business is this?
            2. business_size: Small/Medium/Large
            3. main_challenges: List of main business challenges mentioned
            4. automation_interests: What processes they want to automate
            5. budget_indicators: Any budget or cost concerns mentioned
            6. urgency_level: How urgent their needs seem (1-10)
            7. confidence: How confident you are in this analysis (0-1)
            
            Focus on understanding their specific business needs and pain points.
            """
            
            response = await asyncio.to_thread(
                self.gemini_model.generate_content, prompt
            )
            
            # Parse JSON response
            try:
                analysis = json.loads(response.text)
                return analysis
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "business_type": "unknown",
                    "confidence": 0.6,
                    "analysis": response.text
                }
                
        except Exception as e:
            logger.error("Gemini analysis failed", error=str(e))
            return {"confidence": 0.3, "error": str(e)}
    
    def _identify_business_type(self, transcript: str, gemini_analysis: Dict) -> Dict[str, Any]:
        """Identify business type from transcript and Gemini analysis."""
        transcript_lower = transcript.lower()
        
        # Check Gemini analysis first
        gemini_business_type = gemini_analysis.get("business_type", "").lower()
        
        # Score each business type
        type_scores = {}
        for business_type in BusinessType.get_all_types():
            score = 0
            
            # Check keywords in transcript
            for keyword in business_type["keywords"]:
                if keyword.lower() in transcript_lower:
                    score += 1
            
            # Check Gemini analysis
            if any(keyword in gemini_business_type for keyword in business_type["keywords"]):
                score += 3
            
            type_scores[business_type["name"]] = score
        
        # Find best match
        best_type = max(type_scores, key=type_scores.get)
        best_score = type_scores[best_type]
        
        # Find the business type dict
        for business_type in BusinessType.get_all_types():
            if business_type["name"] == best_type:
                return {
                    **business_type,
                    "confidence_score": min(best_score / 5.0, 1.0)
                }
        
        # Default fallback
        return {
            "name": "General Business",
            "tools": ["email_automation", "customer_followup", "calendar_management"],
            "description": "General business automation",
            "confidence_score": 0.3
        }
    
    def _extract_client_needs(self, transcript: str, gemini_analysis: Dict) -> List[Dict[str, Any]]:
        """Extract specific client needs from conversation."""
        needs = []
        
        # From Gemini analysis
        if "main_challenges" in gemini_analysis:
            for challenge in gemini_analysis["main_challenges"]:
                needs.append({
                    "type": "challenge",
                    "description": challenge,
                    "priority": "high",
                    "source": "gemini_analysis"
                })
        
        if "automation_interests" in gemini_analysis:
            for interest in gemini_analysis["automation_interests"]:
                needs.append({
                    "type": "automation_request",
                    "description": interest,
                    "priority": "medium",
                    "source": "gemini_analysis"
                })
        
        # Pattern-based extraction from transcript
        patterns = {
            "time_saving": [
                r"времени не хватает", r"много времени", r"автоматизировать",
                r"save time", r"time consuming", r"automate"
            ],
            "customer_management": [
                r"клиенты", r"заказчики", r"customers", r"clients",
                r"обратная связь", r"feedback"
            ],
            "communication": [
                r"звонки", r"сообщения", r"уведомления", r"calls", r"messages", r"notifications"
            ],
            "scheduling": [
                r"расписание", r"запись", r"appointment", r"schedule", r"booking"
            ]
        }
        
        for need_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, transcript, re.IGNORECASE):
                    needs.append({
                        "type": need_type,
                        "description": f"Client mentioned {need_type} needs",
                        "priority": "medium",
                        "source": "pattern_matching"
                    })
                    break
        
        return needs
    
    def _recommend_tools(self, business_type: Dict, client_needs: List[Dict]) -> List[Dict[str, Any]]:
        """Recommend specific tools based on business type and needs."""
        recommended = []
        
        # Start with business type tools
        base_tools = business_type.get("tools", [])
        
        # Map needs to additional tools
        need_tool_mapping = {
            "time_saving": ["automation_workflows", "task_scheduling"],
            "customer_management": ["crm_integration", "customer_followup"],
            "communication": ["sms_automation", "email_automation", "voice_calls"],
            "scheduling": ["appointment_scheduling", "calendar_management"]
        }
        
        # Add tools based on needs
        additional_tools = set()
        for need in client_needs:
            need_type = need.get("type", "")
            if need_type in need_tool_mapping:
                additional_tools.update(need_tool_mapping[need_type])
        
        # Combine and prioritize tools
        all_tools = set(base_tools) | additional_tools
        
        # Create detailed tool recommendations
        for tool_name in all_tools:
            tool_info = self._get_tool_info(tool_name)
            if tool_info:
                recommended.append({
                    "name": tool_name,
                    "display_name": tool_info["display_name"],
                    "description": tool_info["description"],
                    "category": tool_info["category"],
                    "priority": self._calculate_tool_priority(tool_name, business_type, client_needs),
                    "estimated_time_savings": tool_info.get("time_savings", "2-5 hours/week"),
                    "setup_complexity": tool_info.get("complexity", "medium")
                })
        
        # Sort by priority
        recommended.sort(key=lambda x: x["priority"], reverse=True)
        
        return recommended[:8]  # Limit to top 8 tools
    
    def _get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a tool."""
        tool_catalog = {
            "hotel_booking": {
                "display_name": "Hotel Booking System",
                "description": "Automated hotel room booking and management",
                "category": "hospitality",
                "time_savings": "10-15 hours/week",
                "complexity": "medium"
            },
            "customer_followup": {
                "display_name": "Customer Follow-up",
                "description": "Automated customer follow-up calls and messages",
                "category": "communication",
                "time_savings": "5-8 hours/week",
                "complexity": "low"
            },
            "email_automation": {
                "display_name": "Email Automation",
                "description": "Automated email campaigns and responses",
                "category": "communication",
                "time_savings": "3-6 hours/week",
                "complexity": "low"
            },
            "sms_automation": {
                "display_name": "SMS Automation",
                "description": "Automated SMS notifications and marketing",
                "category": "communication",
                "time_savings": "2-4 hours/week",
                "complexity": "low"
            },
            "appointment_scheduling": {
                "display_name": "Appointment Scheduling",
                "description": "Automated appointment booking and reminders",
                "category": "scheduling",
                "time_savings": "8-12 hours/week",
                "complexity": "medium"
            },
            "calendar_management": {
                "display_name": "Calendar Management",
                "description": "Intelligent calendar scheduling and coordination",
                "category": "scheduling",
                "time_savings": "4-6 hours/week",
                "complexity": "low"
            },
            "payment_processing": {
                "display_name": "Payment Processing",
                "description": "Automated payment collection and invoicing",
                "category": "finance",
                "time_savings": "6-10 hours/week",
                "complexity": "high"
            },
            "inventory_management": {
                "display_name": "Inventory Management",
                "description": "Automated inventory tracking and ordering",
                "category": "operations",
                "time_savings": "8-15 hours/week",
                "complexity": "high"
            },
            "review_management": {
                "display_name": "Review Management",
                "description": "Automated review monitoring and responses",
                "category": "marketing",
                "time_savings": "3-5 hours/week",
                "complexity": "medium"
            },
            "social_media_management": {
                "display_name": "Social Media Management",
                "description": "Automated social media posting and engagement",
                "category": "marketing",
                "time_savings": "5-10 hours/week",
                "complexity": "medium"
            }
        }
        
        return tool_catalog.get(tool_name)
    
    def _calculate_tool_priority(self, tool_name: str, business_type: Dict, client_needs: List) -> float:
        """Calculate priority score for a tool."""
        priority = 0.5  # Base priority
        
        # Higher priority if it's in business type tools
        if tool_name in business_type.get("tools", []):
            priority += 0.3
        
        # Higher priority based on client needs
        need_keywords = {
            "customer_followup": ["customer", "client", "follow"],
            "email_automation": ["email", "message", "communication"],
            "appointment_scheduling": ["appointment", "schedule", "booking"],
            "sms_automation": ["sms", "text", "notification"]
        }
        
        if tool_name in need_keywords:
            for need in client_needs:
                need_desc = need.get("description", "").lower()
                if any(keyword in need_desc for keyword in need_keywords[tool_name]):
                    priority += 0.2
                    break
        
        return min(priority, 1.0)
    
    def _create_automation_workflow(self, tools: List[Dict], needs: List[Dict]) -> Dict[str, Any]:
        """Create an automation workflow based on recommended tools."""
        workflow_steps = []
        
        # Group tools by category
        categories = {}
        for tool in tools:
            category = tool.get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(tool)
        
        # Create workflow steps
        step_order = ["communication", "scheduling", "operations", "marketing", "finance"]
        
        for i, category in enumerate(step_order):
            if category in categories:
                workflow_steps.append({
                    "step": i + 1,
                    "category": category,
                    "tools": categories[category],
                    "description": f"Set up {category} automation tools",
                    "estimated_setup_time": f"{len(categories[category]) * 2}-{len(categories[category]) * 4} hours"
                })
        
        return {
            "name": "Business Automation Workflow",
            "description": "Step-by-step automation implementation plan",
            "total_steps": len(workflow_steps),
            "estimated_total_time": f"{len(tools) * 2}-{len(tools) * 5} hours",
            "steps": workflow_steps
        }
    
    def _calculate_pricing(self, tools: List[Dict], business_type: Dict) -> Dict[str, Any]:
        """Calculate pricing for the recommended tools."""
        base_price = 20.0  # Base monthly price
        
        # Price adjustments based on number of tools
        tool_count = len(tools)
        if tool_count > 5:
            base_price += (tool_count - 5) * 5
        
        # Business type adjustments
        business_multipliers = {
            "Hotel/Hospitality": 1.2,
            "Healthcare/Medical": 1.3,
            "Real Estate": 1.1,
            "Restaurant/Food Service": 1.0,
            "Retail/E-commerce": 1.1,
            "Beauty/Salon": 0.9,
            "Education/Training": 0.9,
            "Consulting/Professional Services": 1.0
        }
        
        multiplier = business_multipliers.get(business_type.get("name"), 1.0)
        final_price = base_price * multiplier
        
        return {
            "monthly_price": round(final_price, 2),
            "currency": "USD",
            "base_price": base_price,
            "business_multiplier": multiplier,
            "included_tools": tool_count,
            "price_breakdown": {
                "base_subscription": 20.0,
                "additional_tools": max(0, (tool_count - 5) * 5),
                "business_type_adjustment": round((final_price - base_price), 2)
            }
        }
    
    def _generate_consultation_summary(
        self, 
        business_type: Dict, 
        needs: List[Dict], 
        tools: List[Dict], 
        duration: int
    ) -> str:
        """Generate a comprehensive consultation summary."""
        summary = f"""
CONSULTATION SUMMARY
===================

Business Type: {business_type['name']}
Call Duration: {duration} minutes
Analysis Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

IDENTIFIED BUSINESS NEEDS:
"""
        
        for i, need in enumerate(needs[:5], 1):
            summary += f"{i}. {need['description']} (Priority: {need['priority']})\n"
        
        summary += f"""

RECOMMENDED AUTOMATION TOOLS ({len(tools)} tools):
"""
        
        for i, tool in enumerate(tools, 1):
            summary += f"{i}. {tool['display_name']}\n"
            summary += f"   - {tool['description']}\n"
            summary += f"   - Time Savings: {tool['estimated_time_savings']}\n\n"
        
        summary += f"""
NEXT STEPS:
1. Subscribe to our Monthly AI Assistant plan
2. Complete tool setup (estimated 1-2 weeks)
3. Begin automation workflow implementation
4. Monitor and optimize performance

This consultation identified significant automation opportunities for your {business_type['name']} business.
Our AI tools can help streamline operations and improve customer experience.
"""
        
        return summary
    
    async def _save_analysis_to_db(self, user_id: str, analysis: Dict[str, Any]):
        """Save consultation analysis to database."""
        try:
            with Session(self.engine) as session:
                # Update temporary phone assignment
                user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
                
                assignment = session.exec(
                    select(TemporaryPhoneAssignment).where(
                        TemporaryPhoneAssignment.user_id == user_uuid,
                        TemporaryPhoneAssignment.is_active == True
                    )
                ).first()
                
                if assignment:
                    assignment.conversation_summary = analysis["summary"]
                    assignment.client_needs = [need["description"] for need in analysis["client_needs"]]
                    assignment.recommended_features = [tool["name"] for tool in analysis["recommended_tools"]]
                    assignment.subscription_offered = True
                    assignment.analysis_data = json.dumps(analysis)
                    
                    session.commit()
                    
                logger.info("Analysis saved to database", user_id=user_id)
                
        except Exception as e:
            logger.error("Failed to save analysis to database", error=str(e))
    
    async def create_subscription_from_analysis(
        self, 
        user_id: str, 
        selected_tools: List[str] = None
    ) -> Dict[str, Any]:
        """Create subscription based on consultation analysis."""
        try:
            with Session(self.engine) as session:
                user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
                
                # Get the analysis data
                assignment = session.exec(
                    select(TemporaryPhoneAssignment).where(
                        TemporaryPhoneAssignment.user_id == user_uuid,
                        TemporaryPhoneAssignment.subscription_offered == True
                    )
                ).first()
                
                if not assignment or not assignment.analysis_data:
                    return {"success": False, "error": "No consultation analysis found"}
                
                analysis = json.loads(assignment.analysis_data)
                
                # Use selected tools or all recommended tools
                if selected_tools:
                    tools = [t for t in analysis["recommended_tools"] if t["name"] in selected_tools]
                else:
                    tools = analysis["recommended_tools"]
                
                # Create subscription
                subscription = Subscription(
                    user_id=user_uuid,
                    plan_name="Monthly AI Assistant",
                    monthly_price=analysis["pricing"]["monthly_price"],
                    currency=analysis["pricing"]["currency"],
                    status=SubscriptionStatus.ACTIVE,
                    features=json.dumps([tool["name"] for tool in tools]),
                    starts_at=datetime.utcnow(),
                    next_billing_date=datetime.utcnow() + timedelta(days=30)
                )
                
                session.add(subscription)
                session.commit()
                session.refresh(subscription)
                
                # Create AI tool chain
                await self._create_ai_tool_chain(user_uuid, tools, analysis, session)
                
                logger.info("Subscription created from analysis", 
                           user_id=user_id, 
                           subscription_id=subscription.id,
                           tools_count=len(tools))
                
                return {
                    "success": True,
                    "subscription_id": str(subscription.id),
                    "tools_enabled": [tool["name"] for tool in tools],
                    "monthly_price": subscription.monthly_price
                }
                
        except Exception as e:
            logger.error("Failed to create subscription from analysis", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_ai_tool_chain(
        self, 
        user_id: UUID, 
        tools: List[Dict], 
        analysis: Dict, 
        session: Session
    ):
        """Create AI tool chain for the user."""
        try:
            # Create main tool chain
            tool_chain = AIToolChain(
                user_id=user_id,
                name=f"{analysis['business_type']['name']} Automation Chain",
                description=f"Automated tool chain for {analysis['business_type']['name']} business",
                business_type=analysis['business_type']['name'],
                is_active=True,
                created_from_consultation=True
            )
            
            session.add(tool_chain)
            session.commit()
            session.refresh(tool_chain)
            
            # Create tool chain steps
            for i, tool in enumerate(tools):
                step = AIToolChainStep(
                    tool_chain_id=tool_chain.id,
                    step_order=i + 1,
                    tool_name=tool["name"],
                    tool_config=json.dumps({
                        "display_name": tool["display_name"],
                        "description": tool["description"],
                        "category": tool["category"],
                        "auto_execute": tool["priority"] > 0.7
                    }),
                    is_enabled=True
                )
                session.add(step)
            
            session.commit()
            
            logger.info("AI tool chain created", 
                       user_id=user_id, 
                       chain_id=tool_chain.id,
                       steps_count=len(tools))
            
        except Exception as e:
            logger.error("Failed to create AI tool chain", error=str(e))
            raise


# Global service instance
consultation_analysis_service = None


def get_consultation_analysis_service() -> ConsultationAnalysisService:
    """Get consultation analysis service instance."""
    global consultation_analysis_service
    if consultation_analysis_service is None:
        from main import app_state
        consultation_analysis_service = app_state.get('consultation_analysis_service')
    return consultation_analysis_service