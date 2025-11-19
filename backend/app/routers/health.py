"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime
from ..config import get_settings
from ..models.schemas import HealthResponse

router = APIRouter(tags=["health"])
settings = get_settings()

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Check if API is running"""
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "🌾 AgroGuard API",
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "disease_prediction": "/api/disease/predict",
            "chat": "/api/chat"
        }
    }
