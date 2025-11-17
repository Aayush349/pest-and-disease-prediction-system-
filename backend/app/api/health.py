from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AgroGuard API",
        "version": "1.0.0"
    }

@router.get("/ready")
async def readiness_check():
    """Readiness check - all systems ready?"""
    return {
        "ready": True,
        "components": {
            "ml_models": "ready",
            "chatbot": "ready",
            "knowledge_base": "ready"
        }
    }
