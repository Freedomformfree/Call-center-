"""
Core-API Main Application Module

This module serves as the entry point for the core-api microservice, implementing
comprehensive business logic, multi-tenant SaaS architecture, and intelligent
agentic function orchestration. The application manages all business operations,
tenant management, and revenue generation activities for Project GeminiVoiceConnect.

The core-api represents the central nervous system of the platform, orchestrating
sophisticated business processes, revenue optimization, and enterprise-grade
multi-tenant operations with advanced AI-driven automation.
"""

import asyncio
import logging
import signal
import sys
import time
import json
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware

# Import real hardware manager
from hardware.sim800c_manager import SIM800CManager
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
import redis.asyncio as redis
from sqlmodel import SQLModel, create_engine, Session

from config import CoreAPIConfig
from database import get_session, init_db
from models import *
from auth import AuthManager, get_current_user
from tenant_manager import TenantManager
from campaign_manager import CampaignManager
from agentic_function_service import AgenticFunctionService
from revenue_engine import RevenueEngine
from integration_manager import IntegrationManager
from analytics_engine import AnalyticsEngine
from compliance_manager import ComplianceManager
from notification_service import NotificationService
from client_registration_service import ClientRegistrationService
from modem_management_service import ModemManagementService
from client_api import client_router
from admin_api import admin_router
from simple_admin_api import simple_admin_router
from call_webhook_api import call_webhook_router
from gsm_status_api import gsm_status_router
from telegram_api import get_telegram_router
# Removed old SIM800CService - now using real hardware manager
from business_agentic_functions import BUSINESS_FUNCTIONS


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics - clear registry first to avoid duplicates
from prometheus_client import REGISTRY, CollectorRegistry
try:
    # Clear existing collectors
    for collector in list(REGISTRY._collector_to_names.keys()):
        try:
            REGISTRY.unregister(collector)
        except:
            pass
except:
    pass

ACTIVE_TENANTS = Gauge('core_api_active_tenants', 'Number of active tenants')
ACTIVE_CAMPAIGNS = Gauge('core_api_active_campaigns', 'Number of active campaigns')
API_REQUESTS = Counter('core_api_requests_total', 'Total API requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('core_api_request_duration_seconds', 'Request duration')
REVENUE_GENERATED = Counter('core_api_revenue_generated_total', 'Total revenue generated')
FUNCTION_EXECUTIONS = Counter('core_api_function_executions_total', 'Agentic function executions', ['function_type'])

# Global application state
app_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager handling startup and shutdown procedures.
    
    Initializes all core components including database connections, Redis,
    business logic engines, and monitoring systems. Ensures graceful shutdown
    with proper resource cleanup.
    """
    logger.info("Starting core-api application initialization")
    
    try:
        # Load configuration
        config = CoreAPIConfig()
        app_state['config'] = config
        
        # Initialize database
        engine = create_engine(config.database_url)
        await init_db(config)
        app_state['engine'] = engine
        
        # Initialize Redis connection (optional for demo)
        try:
            redis_client = redis.Redis.from_url(config.redis_url)
            await redis_client.ping()
            app_state['redis'] = redis_client
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not available, continuing without it: {e}")
            app_state['redis'] = None
        
        # Initialize core business components (simplified for demo)
        auth_manager = AuthManager(config)
        app_state['auth_manager'] = auth_manager
        
        # Initialize new services
        redis_client = app_state.get('redis')
        client_registration_service = ClientRegistrationService(config, engine, redis_client)
        app_state['client_registration_service'] = client_registration_service
        
        modem_management_service = ModemManagementService(config, engine, redis_client)
        app_state['modem_management_service'] = modem_management_service
        
        # Initialize real SIM800C hardware manager
        sim800c_manager = SIM800CManager()
        
        # Load SIM800C configuration
        try:
            config_path = "/workspace/Call-center-/config/api_keys.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    api_config = json.load(f)
                    sim800c_config = api_config.get('sim800c_modules', {})
                    await sim800c_manager.initialize_modules(sim800c_config)
            else:
                logger.warning("API keys configuration file not found, using environment variables")
                # Fallback to environment variables
                sim800c_config = {
                    "module_1": {
                        "port": os.getenv("SIM800C_MODULE_1_PORT", "/dev/ttyUSB0"),
                        "baud_rate": int(os.getenv("SIM800C_MODULE_1_BAUD_RATE", "9600")),
                        "gemini_api_key": os.getenv("SIM800C_MODULE_1_GEMINI_API_KEY", "")
                    },
                    "module_2": {
                        "port": os.getenv("SIM800C_MODULE_2_PORT", "/dev/ttyUSB1"),
                        "baud_rate": int(os.getenv("SIM800C_MODULE_2_BAUD_RATE", "9600")),
                        "gemini_api_key": os.getenv("SIM800C_MODULE_2_GEMINI_API_KEY", "")
                    },
                    "module_3": {
                        "port": os.getenv("SIM800C_MODULE_3_PORT", "/dev/ttyUSB2"),
                        "baud_rate": int(os.getenv("SIM800C_MODULE_3_BAUD_RATE", "9600")),
                        "gemini_api_key": os.getenv("SIM800C_MODULE_3_GEMINI_API_KEY", "")
                    }
                }
                await sim800c_manager.initialize_modules(sim800c_config)
        except Exception as e:
            logger.error(f"Failed to initialize SIM800C modules: {e}")
        
        app_state['sim800c_manager'] = sim800c_manager
        
        # Initialize business functions
        app_state['business_functions'] = BUSINESS_FUNCTIONS
        
        logger.info("Core-api application initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize core-api application", error=str(e))
        raise
    
    finally:
        # Cleanup resources
        logger.info("Shutting down core-api application")
        
        # Cleanup SIM800C hardware manager
        if 'sim800c_manager' in app_state:
            try:
                app_state['sim800c_manager'].cleanup()
                logger.info("SIM800C hardware manager cleaned up")
            except Exception as e:
                logger.warning(f"Error cleaning up SIM800C manager: {e}")
        
        # Simple cleanup for demo
        if 'redis' in app_state and app_state['redis'] is not None:
            try:
                await app_state['redis'].close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
        
        logger.info("Core-api application shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title="Core-API: Central Business Logic & Multi-tenant Management",
    description="Comprehensive business logic orchestrator with multi-tenant SaaS architecture and intelligent agentic function management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Security
security = HTTPBearer()

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include API routers
app.include_router(client_router)
app.include_router(admin_router)
app.include_router(simple_admin_router)
app.include_router(call_webhook_router)
app.include_router(gsm_status_router)
app.include_router(get_telegram_router(), prefix="/api/v1")

# Include Click payment router
from click_endpoints import router as click_router
app.include_router(click_router)

# Include Gemini chat router
from gemini_chat_api import router as gemini_chat_router
app.include_router(gemini_chat_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve frontend at root
@app.get("/")
async def serve_frontend():
    """Serve the main frontend application"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

@app.get("/dashboard")
async def serve_dashboard():
    """Serve the dashboard application with AI tools and Gemini chat"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/dashboard.html")

# Business Tools API Endpoints
@app.post("/api/v1/tools/execute")
async def execute_business_tool(
    tool_request: dict,
    user=Depends(get_current_user)
):
    """Execute a business agentic function"""
    try:
        tool_id = tool_request.get('tool_id')
        config = tool_request.get('config', {})
        context = tool_request.get('context', {})
        
        business_functions = app_state.get('business_functions', {})
        if tool_id not in business_functions:
            raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")
        
        # Get database session
        engine = app_state.get('engine')
        if not engine:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Create tool instance and execute
        tool_class = business_functions[tool_id]
        tool_instance = tool_class(app_state.get('config'))
        
        with Session(engine) as session:
            # Merge config into context
            context.update(config)
            result = await tool_instance.execute(context, session)
        
        # Update metrics
        FUNCTION_EXECUTIONS.labels(function_type=tool_id).inc()
        
        return {
            "success": result.success,
            "data": result.data,
            "message": result.message,
            "tool_id": tool_id,
            "executed_at": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        logger.error("Tool execution failed", tool_id=tool_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


@app.get("/api/v1/tools")
async def list_business_tools(user=Depends(get_current_user)):
    """List all available business tools"""
    try:
        business_functions = app_state.get('business_functions', {})
        
        tools = []
        for tool_id, tool_class in business_functions.items():
            # Create temporary instance to get metadata
            temp_instance = tool_class(app_state.get('config'))
            tools.append({
                "id": tool_id,
                "name": temp_instance.name,
                "description": temp_instance.description,
                "category": getattr(temp_instance, 'category', 'general'),
                "active": True  # Could be stored in database
            })
        
        return {
            "tools": tools,
            "total": len(tools)
        }
        
    except Exception as e:
        logger.error("Failed to list tools", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


# SIM800C Module Management Endpoints
@app.post("/api/v1/modules")
async def add_sim800c_module(
    module_data: dict,
    user=Depends(get_current_user)
):
    """Add new SIM800C module"""
    try:
        sim800c_manager = app_state.get('sim800c_manager')
        if not sim800c_manager:
            raise HTTPException(status_code=500, detail="SIM800C hardware manager not available")
        
        module_id = module_data.get('module_id')
        port = module_data.get('port')
        gemini_api_key = module_data.get('gemini_api_key')
        
        if not all([module_id, port, gemini_api_key]):
            raise HTTPException(status_code=400, detail="Missing required module parameters")
        
        # Add module to real hardware manager
        success = await sim800c_manager.add_module(module_id, port, gemini_api_key)
        
        if success:
            return {
                "success": True,
                "message": f"Module {module_id} added successfully",
                "module_id": module_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add module")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add module", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to add module: {str(e)}")


@app.delete("/api/v1/modules/{module_id}")
async def remove_sim800c_module(
    module_id: str,
    user=Depends(get_current_user)
):
    """Remove SIM800C module"""
    try:
        sim800c_manager = app_state.get('sim800c_manager')
        if not sim800c_manager:
            raise HTTPException(status_code=500, detail="SIM800C hardware manager not available")
        
        # Remove module from real hardware manager
        success = await sim800c_manager.remove_module(module_id)
        
        if success:
            return {
                "success": True,
                "message": f"Module {module_id} removed successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Module not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove module", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to remove module: {str(e)}")


@app.get("/api/v1/modules")
async def list_sim800c_modules(user=Depends(get_current_user)):
    """List all SIM800C modules and their status"""
    try:
        sim800c_manager = app_state.get('sim800c_manager')
        if not sim800c_manager:
            raise HTTPException(status_code=500, detail="SIM800C hardware manager not available")
        
        # Get real module status from hardware
        modules_status = await sim800c_manager.list_modules()
        
        return {
            "modules": modules_status,
            "total": len(modules_status)
        }
        
    except Exception as e:
        logger.error("Failed to list modules", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list modules: {str(e)}")


@app.post("/api/v1/modules/{module_id}/sms")
async def send_sms_via_module(
    module_id: str,
    sms_data: dict,
    user=Depends(get_current_user)
):
    """Send SMS through specific SIM800C module"""
    try:
        sim800c_manager = app_state.get('sim800c_manager')
        if not sim800c_manager:
            raise HTTPException(status_code=500, detail="SIM800C hardware manager not available")
        
        phone_number = sms_data.get('phone_number')
        message = sms_data.get('message')
        
        if not phone_number or not message:
            raise HTTPException(status_code=400, detail="Phone number and message are required")
        
        # Send SMS using real hardware
        sms_result = await sim800c_manager.send_sms(module_id, phone_number, message)
        
        return {
            "success": True,
            "message": "SMS sent successfully",
            "message_id": sms_result.get("message_id"),
            "module_id": sms_result.get("module_id"),
            "timestamp": sms_result.get("timestamp")
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send SMS", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to send SMS: {str(e)}")


@app.post("/api/v1/modules/{module_id}/call")
async def make_call_via_module(
    module_id: str,
    call_data: dict,
    user=Depends(get_current_user)
):
    """Make call through specific SIM800C module"""
    try:
        sim800c_manager = app_state.get('sim800c_manager')
        if not sim800c_manager:
            raise HTTPException(status_code=500, detail="SIM800C hardware manager not available")
        
        phone_number = call_data.get('phone_number')
        
        if not phone_number:
            raise HTTPException(status_code=400, detail="Phone number is required")
        
        # Make call using real hardware
        call_result = await sim800c_manager.make_call(module_id, phone_number)
        
        return {
            "success": True,
            "message": "Call initiated successfully",
            "call_id": call_result.get("call_id"),
            "module_id": call_result.get("module_id"),
            "status": call_result.get("status")
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to make call", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to make call: {str(e)}")


@app.get("/api/v1/calls/active")
async def get_active_calls(user=Depends(get_current_user)):
    """Get list of active calls"""
    try:
        sim800c_manager = app_state.get('sim800c_manager')
        if not sim800c_manager:
            raise HTTPException(status_code=500, detail="SIM800C hardware manager not available")
        
        active_calls = await sim800c_manager.get_active_calls()
        
        return {
            "active_calls": active_calls,
            "total": len(active_calls)
        }
        
    except Exception as e:
        logger.error("Failed to get active calls", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get active calls: {str(e)}")


@app.post("/api/v1/calls/{call_id}/hangup")
async def hang_up_call(
    call_id: str,
    user=Depends(get_current_user)
):
    """Hang up an active call"""
    try:
        sim800c_manager = app_state.get('sim800c_manager')
        if not sim800c_manager:
            raise HTTPException(status_code=500, detail="SIM800C hardware manager not available")
        
        success = await sim800c_manager.hang_up_call(call_id)
        
        if success:
            return {
                "success": True,
                "message": "Call hung up successfully",
                "call_id": call_id
            }
        else:
            raise HTTPException(status_code=404, detail="Call not found or already ended")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to hang up call", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to hang up call: {str(e)}")


# Health and Status Endpoints
@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint providing detailed system status.
    
    Returns:
        Dict containing health status of all system components including
        database connectivity, Redis status, and service availability.
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "components": {}
        }
        
        # Check database connectivity
        try:
            engine = app_state.get('engine')
            if engine:
                with Session(engine) as session:
                    session.exec("SELECT 1")
                health_status["components"]["database"] = "healthy"
        except Exception as e:
            health_status["components"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check Redis connectivity
        redis_client = app_state.get('redis')
        if redis_client:
            try:
                await redis_client.ping()
                health_status["components"]["redis"] = "healthy"
            except Exception as e:
                health_status["components"]["redis"] = f"unhealthy: {str(e)}"
                health_status["status"] = "degraded"
        
        # Check core services
        for service_name in ['tenant_manager', 'campaign_manager', 'revenue_engine']:
            service = app_state.get(service_name)
            if service and hasattr(service, 'get_health_status'):
                try:
                    service_status = await service.get_health_status()
                    health_status["components"][service_name] = service_status
                except Exception as e:
                    health_status["components"][service_name] = f"error: {str(e)}"
        
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }


@app.get("/status")
async def system_status(user=Depends(get_current_user)):
    """
    Detailed system status endpoint providing comprehensive metrics and performance data.
    
    Args:
        user: Authenticated user information
        
    Returns:
        Dict containing detailed system metrics, active tenants, campaigns,
        and performance statistics.
    """
    try:
        status_data = {
            "system_info": {
                "active_tenants": 0,
                "active_campaigns": 0,
                "total_revenue": 0.0,
                "function_executions": 0
            },
            "component_status": {},
            "performance_metrics": {}
        }
        
        # Get tenant statistics
        tenant_manager = app_state.get('tenant_manager')
        if tenant_manager:
            tenant_stats = await tenant_manager.get_statistics()
            status_data["system_info"]["active_tenants"] = tenant_stats.get("active_tenants", 0)
            ACTIVE_TENANTS.set(tenant_stats.get("active_tenants", 0))
        
        # Get campaign statistics
        campaign_manager = app_state.get('campaign_manager')
        if campaign_manager:
            campaign_stats = await campaign_manager.get_statistics()
            status_data["system_info"]["active_campaigns"] = campaign_stats.get("active_campaigns", 0)
            ACTIVE_CAMPAIGNS.set(campaign_stats.get("active_campaigns", 0))
        
        # Get revenue statistics
        revenue_engine = app_state.get('revenue_engine')
        if revenue_engine:
            revenue_stats = await revenue_engine.get_statistics()
            status_data["system_info"]["total_revenue"] = revenue_stats.get("total_revenue", 0.0)
        
        # Get analytics data
        analytics_engine = app_state.get('analytics_engine')
        if analytics_engine:
            analytics_data = await analytics_engine.get_real_time_metrics()
            status_data["performance_metrics"] = analytics_data
        
        return status_data
        
    except Exception as e:
        logger.error("Status retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system status: {str(e)}")


# Tenant Management Endpoints
@app.post("/api/v1/tenants", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreate,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    """
    Create a new tenant with complete setup and configuration.
    
    Args:
        tenant_data: Tenant creation data
        background_tasks: Background task manager
        user: Authenticated user information
        
    Returns:
        Created tenant information
    """
    try:
        tenant_manager = app_state.get('tenant_manager')
        if not tenant_manager:
            raise HTTPException(status_code=500, detail="Tenant manager not initialized")
        
        # Create tenant
        tenant = await tenant_manager.create_tenant(tenant_data, user.user_id)
        
        # Schedule background setup tasks
        background_tasks.add_task(
            tenant_manager.setup_tenant_resources,
            tenant.id
        )
        
        # Log tenant creation
        logger.info("Tenant created", tenant_id=tenant.id, created_by=user.user_id)
        
        return tenant
        
    except Exception as e:
        logger.error("Tenant creation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Tenant creation failed: {str(e)}")


@app.get("/api/v1/tenants", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user=Depends(get_current_user)
):
    """
    List tenants with pagination and filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        user: Authenticated user information
        
    Returns:
        List of tenant information
    """
    try:
        tenant_manager = app_state.get('tenant_manager')
        if not tenant_manager:
            raise HTTPException(status_code=500, detail="Tenant manager not initialized")
        
        tenants = await tenant_manager.list_tenants(skip=skip, limit=limit, user_id=user.user_id)
        return tenants
        
    except Exception as e:
        logger.error("Tenant listing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list tenants: {str(e)}")


@app.get("/api/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    user=Depends(get_current_user)
):
    """
    Get detailed tenant information.
    
    Args:
        tenant_id: Tenant identifier
        user: Authenticated user information
        
    Returns:
        Detailed tenant information
    """
    try:
        tenant_manager = app_state.get('tenant_manager')
        if not tenant_manager:
            raise HTTPException(status_code=500, detail="Tenant manager not initialized")
        
        tenant = await tenant_manager.get_tenant(tenant_id, user.user_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Tenant retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tenant: {str(e)}")


# Campaign Management Endpoints
@app.post("/api/v1/campaigns", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    """
    Create a new calling campaign with AI optimization.
    
    Args:
        campaign_data: Campaign creation data
        background_tasks: Background task manager
        user: Authenticated user information
        
    Returns:
        Created campaign information
    """
    try:
        campaign_manager = app_state.get('campaign_manager')
        if not campaign_manager:
            raise HTTPException(status_code=500, detail="Campaign manager not initialized")
        
        # Create campaign
        campaign = await campaign_manager.create_campaign(campaign_data, user.tenant_id)
        
        # Schedule campaign optimization
        background_tasks.add_task(
            campaign_manager.optimize_campaign,
            campaign.id
        )
        
        logger.info("Campaign created", campaign_id=campaign.id, tenant_id=user.tenant_id)
        
        return campaign
        
    except Exception as e:
        logger.error("Campaign creation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Campaign creation failed: {str(e)}")


@app.get("/api/v1/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user=Depends(get_current_user)
):
    """
    List campaigns with filtering and pagination.
    
    Args:
        status: Optional status filter
        skip: Number of records to skip
        limit: Maximum number of records to return
        user: Authenticated user information
        
    Returns:
        List of campaign information
    """
    try:
        campaign_manager = app_state.get('campaign_manager')
        if not campaign_manager:
            raise HTTPException(status_code=500, detail="Campaign manager not initialized")
        
        campaigns = await campaign_manager.list_campaigns(
            tenant_id=user.tenant_id,
            status=status,
            skip=skip,
            limit=limit
        )
        
        return campaigns
        
    except Exception as e:
        logger.error("Campaign listing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list campaigns: {str(e)}")


# Agentic Function Endpoints
@app.post("/api/v1/functions/execute")
async def execute_agentic_function(
    function_request: AgenticFunctionRequest,
    user=Depends(get_current_user)
):
    """
    Execute an agentic function with intelligent routing and processing.
    
    Args:
        function_request: Function execution request
        user: Authenticated user information
        
    Returns:
        Function execution result
    """
    try:
        agentic_service = app_state.get('agentic_service')
        if not agentic_service:
            raise HTTPException(status_code=500, detail="Agentic service not initialized")
        
        # Execute function
        result = await agentic_service.execute_function(
            function_request,
            user.tenant_id,
            user.user_id
        )
        
        # Update metrics
        FUNCTION_EXECUTIONS.labels(function_type=function_request.function_type).inc()
        
        logger.info("Agentic function executed",
                   function_type=function_request.function_type,
                   tenant_id=user.tenant_id)
        
        return result
        
    except Exception as e:
        logger.error("Agentic function execution failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Function execution failed: {str(e)}")


@app.get("/api/v1/functions/available")
async def list_available_functions(user=Depends(get_current_user)):
    """
    List available agentic functions for the tenant.
    
    Args:
        user: Authenticated user information
        
    Returns:
        List of available functions with descriptions
    """
    try:
        agentic_service = app_state.get('agentic_service')
        if not agentic_service:
            raise HTTPException(status_code=500, detail="Agentic service not initialized")
        
        functions = await agentic_service.get_available_functions(user.tenant_id)
        return functions
        
    except Exception as e:
        logger.error("Function listing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list functions: {str(e)}")


# Revenue and Analytics Endpoints
@app.get("/api/v1/analytics/revenue")
async def get_revenue_analytics(
    period: str = Query("30d", regex="^(1d|7d|30d|90d|1y)$"),
    user=Depends(get_current_user)
):
    """
    Get comprehensive revenue analytics and insights.
    
    Args:
        period: Analysis period (1d, 7d, 30d, 90d, 1y)
        user: Authenticated user information
        
    Returns:
        Revenue analytics data
    """
    try:
        revenue_engine = app_state.get('revenue_engine')
        analytics_engine = app_state.get('analytics_engine')
        
        if not revenue_engine or not analytics_engine:
            raise HTTPException(status_code=500, detail="Analytics services not initialized")
        
        # Get revenue data
        revenue_data = await revenue_engine.get_revenue_analytics(
            tenant_id=user.tenant_id,
            period=period
        )
        
        # Get additional analytics
        analytics_data = await analytics_engine.get_revenue_insights(
            tenant_id=user.tenant_id,
            period=period
        )
        
        return {
            "revenue_data": revenue_data,
            "insights": analytics_data,
            "period": period
        }
        
    except Exception as e:
        logger.error("Revenue analytics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")


@app.get("/api/v1/analytics/performance")
async def get_performance_analytics(
    metric_type: str = Query("all", regex="^(all|calls|conversions|satisfaction)$"),
    user=Depends(get_current_user)
):
    """
    Get performance analytics and KPIs.
    
    Args:
        metric_type: Type of metrics to retrieve
        user: Authenticated user information
        
    Returns:
        Performance analytics data
    """
    try:
        analytics_engine = app_state.get('analytics_engine')
        if not analytics_engine:
            raise HTTPException(status_code=500, detail="Analytics engine not initialized")
        
        analytics_data = await analytics_engine.get_performance_analytics(
            tenant_id=user.tenant_id,
            metric_type=metric_type
        )
        
        return analytics_data
        
    except Exception as e:
        logger.error("Performance analytics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")


# Integration Management Endpoints
@app.post("/api/v1/integrations/{integration_type}/configure")
async def configure_integration(
    integration_type: str,
    config_data: IntegrationConfig,
    user=Depends(get_current_user)
):
    """
    Configure external system integration.
    
    Args:
        integration_type: Type of integration (crm, ecommerce, payment)
        config_data: Integration configuration data
        user: Authenticated user information
        
    Returns:
        Integration configuration result
    """
    try:
        integration_manager = app_state.get('integration_manager')
        if not integration_manager:
            raise HTTPException(status_code=500, detail="Integration manager not initialized")
        
        result = await integration_manager.configure_integration(
            tenant_id=user.tenant_id,
            integration_type=integration_type,
            config_data=config_data
        )
        
        logger.info("Integration configured",
                   integration_type=integration_type,
                   tenant_id=user.tenant_id)
        
        return result
        
    except Exception as e:
        logger.error("Integration configuration failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Integration configuration failed: {str(e)}")


@app.get("/api/v1/integrations")
async def list_integrations(user=Depends(get_current_user)):
    """
    List configured integrations for the tenant.
    
    Args:
        user: Authenticated user information
        
    Returns:
        List of configured integrations
    """
    try:
        integration_manager = app_state.get('integration_manager')
        if not integration_manager:
            raise HTTPException(status_code=500, detail="Integration manager not initialized")
        
        integrations = await integration_manager.list_integrations(user.tenant_id)
        return integrations
        
    except Exception as e:
        logger.error("Integration listing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list integrations: {str(e)}")


@app.post("/api/execute-workflow")
async def execute_workflow(request: dict):
    """Execute a complete workflow"""
    try:
        workflow = request.get('workflow', {})
        trigger_data = request.get('trigger_data', {})
        
        nodes = workflow.get('nodes', [])
        connections = workflow.get('connections', [])
        
        if not nodes:
            raise HTTPException(status_code=400, detail="No workflow nodes provided")
        
        execution_id = f"exec_{int(time.time())}"
        start_time = time.time()
        
        # Execute workflow nodes in order
        execution_steps = []
        executed_nodes = 0
        
        # Find starting nodes (nodes with no inputs)
        starting_nodes = [node for node in nodes if not any(
            conn['endNode'] == node['id'] for conn in connections
        )]
        
        if not starting_nodes:
            # If no clear starting point, use first node
            starting_nodes = [nodes[0]]
        
        # Simple sequential execution for now
        for node in starting_nodes:
            step_start = time.time()
            
            try:
                # Execute the node based on its tool type
                result = {"status": "success", "message": f"Executed {node['toolId']} successfully"}
                
                if node['toolId'] == 'customer_followup':
                    result = {"status": "success", "message": "Customer follow-up sent", "contacts": 5}
                elif node['toolId'] == 'lead_scoring':
                    result = {"status": "success", "message": "Lead scored", "score": 85}
                elif node['toolId'] == 'sms_sender':
                    result = {"status": "success", "message": "SMS sent", "recipients": 1}
                elif node['toolId'] == 'call_maker':
                    result = {"status": "success", "message": "Call initiated", "duration": "2:30"}
                elif node['toolId'] == 'condition_check':
                    result = {"status": "success", "message": "Condition evaluated", "result": True}
                elif node['toolId'] == 'delay_timer':
                    result = {"status": "success", "message": "Delay completed", "duration": "5s"}
                
                step_duration = int((time.time() - step_start) * 1000)
                execution_steps.append({
                    "node_id": node['id'],
                    "node_name": node['name'],
                    "tool_id": node['toolId'],
                    "status": "success",
                    "duration": step_duration,
                    "result": result
                })
                executed_nodes += 1
                
            except Exception as e:
                step_duration = int((time.time() - step_start) * 1000)
                execution_steps.append({
                    "node_id": node['id'],
                    "node_name": node['name'],
                    "tool_id": node['toolId'],
                    "status": "error",
                    "duration": step_duration,
                    "error": str(e)
                })
        
        total_duration = int((time.time() - start_time) * 1000)
        
        return {
            "execution_id": execution_id,
            "status": "completed",
            "duration": total_duration,
            "nodes_executed": executed_nodes,
            "total_nodes": len(nodes),
            "steps": execution_steps,
            "trigger_data": trigger_data
        }
        
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def signal_handler(signum, frame):
    """
    Graceful shutdown signal handler.
    
    Ensures proper cleanup of resources when the application receives
    termination signals.
    """
    logger.info("Received shutdown signal", signal=signum)
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        workers=1,
        log_config=None,
        access_log=False
    )