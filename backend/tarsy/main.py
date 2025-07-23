"""
Tarsy-bot - FastAPI Application
Main entry point for the tarsy backend service.
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from tarsy.config.settings import get_settings
from tarsy.controllers.history_controller import router as history_router
from tarsy.database.init_db import get_database_info, initialize_database
from tarsy.models.alert import Alert, AlertResponse, ProcessingStatus
from tarsy.services.alert_service import AlertService
from tarsy.services.websocket_manager import WebSocketManager
from tarsy.utils.logger import get_module_logger, setup_logging

# Setup logger for this module
logger = get_module_logger(__name__)

# Global state for processing status tracking
processing_status: Dict[str, ProcessingStatus] = {}
alert_service: AlertService = None
websocket_manager: WebSocketManager = None
alert_processing_semaphore: asyncio.Semaphore = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global alert_service, websocket_manager, alert_processing_semaphore
    
    # Initialize services
    settings = get_settings()
    
    # Setup logging
    setup_logging(settings.log_level)
    
    # Initialize concurrency control
    alert_processing_semaphore = asyncio.Semaphore(settings.max_concurrent_alerts)
    logger.info(f"Alert processing concurrency limit: {settings.max_concurrent_alerts}")
    
    # Initialize database for history service
    db_init_success = initialize_database()
    if not db_init_success and settings.history_enabled:
        logger.warning("History database initialization failed - continuing with history service disabled")
    
    alert_service = AlertService(settings)
    websocket_manager = WebSocketManager()
    
    # Startup
    await alert_service.initialize()
    logger.info("Tarsy started successfully!")
    
    # Log history service status
    db_info = get_database_info()
    if db_info.get("enabled"):
        logger.info(f"History service: ENABLED (Database: {db_info.get('database_name', 'unknown')})")
    else:
        logger.info("History service: DISABLED")
    
    yield
    
    # Shutdown
    logger.info("Tarsy shutting down...")
    await alert_service.close()
    logger.info("Tarsy shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Tarsy-bot",
    description="Automated incident response agent using AI and MCP servers",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(history_router, tags=["history"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Tarsy is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Get basic service status
        health_status = {
            "status": "healthy",
            "service": "tarsy",
            "timestamp": "2024-12-19T12:00:00Z",  # This will be updated by actual timestamp
        }
        
        # Add history service status
        db_info = get_database_info()
        history_status = "disabled"
        if db_info.get("enabled"):
            if db_info.get("connection_test"):
                history_status = "healthy"
            else:
                history_status = "unhealthy"
                health_status["status"] = "degraded"  # Overall status degraded if history fails
        
        health_status["services"] = {
            "alert_processing": "healthy",
            "history_service": history_status,
            "database": {
                "enabled": db_info.get("enabled", False),
                "connected": db_info.get("connection_test", False) if db_info.get("enabled") else None,
                "retention_days": db_info.get("retention_days") if db_info.get("enabled") else None
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "tarsy",
            "error": str(e)
        }


@app.get("/alert-types", response_model=List[str])
async def get_alert_types():
    """Get supported alert types for the development/testing web interface.
    
    This endpoint returns a list of alert types used only for dropdown selection
    in the development/testing web interface. In production, external clients
    (like Alert Manager) can submit any alert type. The system analyzes all
    alert types using the provided runbook and available agent-specific MCP tools.
    """
    return alert_service.agent_registry.get_supported_alert_types()


@app.post("/alerts", response_model=AlertResponse)
async def submit_alert(alert: Alert):
    """Submit a new alert for processing."""
    # Generate unique alert ID
    alert_id = str(uuid.uuid4())
    
    # Initialize processing status
    processing_status[alert_id] = ProcessingStatus(
        alert_id=alert_id,
        status="queued",
        progress=0,
        current_step="Alert received",
        current_agent=None,
        assigned_mcp_servers=None,
        result=None,
        error=None
    )
    
    # Start background processing
    asyncio.create_task(process_alert_background(alert_id, alert))
    
    return AlertResponse(
        alert_id=alert_id,
        status="queued",
        message="Alert submitted for processing"
    )


@app.get("/processing-status/{alert_id}", response_model=ProcessingStatus)
async def get_processing_status(alert_id: str):
    """Get processing status for an alert."""
    if alert_id not in processing_status:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return processing_status[alert_id]


@app.websocket("/ws/{alert_id}")
async def websocket_endpoint(websocket: WebSocket, alert_id: str):
    """WebSocket endpoint for real-time progress updates."""
    try:
        await websocket_manager.connect(websocket, alert_id)
        
        # Send initial status if available
        if alert_id in processing_status:
            await websocket_manager.send_status_update(
                alert_id, processing_status[alert_id]
            )
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for any message from client (ping/pong or actual data)
                message = await websocket.receive_text()
                # Echo back or handle client messages if needed
                # For now, we just receive and continue
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for alert {alert_id}: {str(e)}")
    finally:
        websocket_manager.disconnect(websocket, alert_id)


async def process_alert_background(alert_id: str, alert: Alert):
    """Background task to process an alert with concurrency control."""
    async with alert_processing_semaphore:
        try:
            # Update status: processing started
            await update_processing_status(
                alert_id, "processing", 10, "Starting alert processing"
            )
            
            # Process the alert using AlertService
            # The orchestrator sends progress as a dict with agent information
            def progress_handler(progress, step):
                # Handle both simple (progress, step) and dict-based callbacks
                if isinstance(progress, dict):
                    # New format from agent callbacks
                    agent_info = progress
                    return asyncio.create_task(
                        update_processing_status(
                            alert_id,
                            agent_info.get('status', 'processing'),
                            agent_info.get('progress', 50),
                            agent_info.get('message', step),
                            current_agent=agent_info.get('agent'),
                            assigned_mcp_servers=agent_info.get('assigned_mcp_servers')
                        )
                    )
                else:
                    # Legacy format (progress, step)
                    return asyncio.create_task(
                        update_processing_status(alert_id, "processing", progress, step)
                    )
            
            result = await alert_service.process_alert(alert, progress_callback=progress_handler)
            
            # Update status: completed
            await update_processing_status(
                alert_id, "completed", 100, "Processing completed", result
            )
            
        except Exception as e:
            # Update status: error
            await update_processing_status(
                alert_id, "error", 0, "Processing failed", None, str(e)
            )


async def update_processing_status(
    alert_id: str, 
    status: str, 
    progress: int, 
    current_step: str,
    result: str = None,
    error: str = None,
    current_agent: str = None,
    assigned_mcp_servers: List[str] = None
):
    """Update processing status and notify WebSocket clients."""
    processing_status[alert_id] = ProcessingStatus(
        alert_id=alert_id,
        status=status,
        progress=progress,
        current_step=current_step,
        current_agent=current_agent,
        assigned_mcp_servers=assigned_mcp_servers,
        result=result,
        error=error
    )
    
    # Send update via WebSocket
    if websocket_manager:
        await websocket_manager.send_status_update(
            alert_id, processing_status[alert_id]
        )


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "tarsy.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    ) 