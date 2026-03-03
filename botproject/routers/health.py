"""
Health Check Router - HTTP Endpoints
Uses HealthService for business logic

Phase 3 Refactored: Thin router with service layer separation
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

# Import health service
from services.health_service import HealthService

# Create router
router = APIRouter(tags=["Health"])

# Initialize service
health_service = HealthService()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint

    Returns:
        JSONResponse: Basic health status
    """
    result = health_service.get_basic_health()
    return JSONResponse(result)


@router.get("/enhanced-health")
async def enhanced_health_check():
    """
    Enhanced health check with service availability

    Returns:
        JSONResponse: Enhanced health status including service availability
    """
    result = health_service.get_enhanced_health()
    return JSONResponse(result)


@router.get("/enhanced-health-with-memory")
async def enhanced_health_with_memory():
    """
    Health check including memory system statistics

    Returns:
        JSONResponse: Complete health status with memory statistics
    """
    result = health_service.get_health_with_memory()
    return JSONResponse(result)



@router.get("/files_features")
def get_features():
    """Returns the status of all features"""
    return {
        "camera": False,
        "files": True,
        "gallery": False,
    }

