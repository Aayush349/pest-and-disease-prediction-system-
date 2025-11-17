from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from .config import get_settings
from .api import predict, chatbot, health
from .utils.logger import Logger

# Get settings
settings = get_settings()
logger = Logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="AgroGuard - AI-Powered Crop Disease Detection & Advisory System",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
uploads_path = Path(settings.UPLOAD_DIR)
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(health.router, prefix="/api/health")
app.include_router(predict.router, prefix="/api/predict")
app.include_router(chatbot.router, prefix="/api/chat")

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "AgroGuard API",
        "version": settings.API_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "documentation": "/docs"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.success("✓ AgroGuard Backend Started")
    logger.success("✓ ML Models Loaded")
    logger.success("✓ Knowledge Base Ready")
    logger.success("✓ Chatbot Agent Active")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("AgroGuard Backend Shutting Down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
