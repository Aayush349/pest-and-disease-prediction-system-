#!/usr/bin/env python3
"""
🌾 AgroGuard Backend API
AI-powered pest/disease detection + farmer advisory chatbot
Merged + Improved Version (Stable + Full Features)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path

# Import configuration
from .config import get_settings
from .utils.logger import Logger

# Import routers
from .routers import health, disease, chat

# Initialize
settings = get_settings()
logger = Logger(__name__)

# ============== FastAPI App ==============
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============== Middleware ==============
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# ============== Create Upload Directory ==============
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(exist_ok=True)
logger.success(f"✓ Upload directory ready: {upload_dir}")

# ============== Startup Event ==============
@app.on_event("startup")
async def startup_event():
    logger.success("=" * 70)
    logger.success("🚀 AgroGuard Backend Starting")
    logger.success("=" * 70)

    logger.info(f"API Version: {settings.API_VERSION}")
    logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")

    # Database Info
    if '@' in settings.DATABASE_URL:
        db_info = settings.DATABASE_URL.split('@')[1]
    else:
        db_info = "N/A"
    logger.info(f"Database: {db_info}")

    # GPU Check (Real Torch Check)
    try:
        import torch
        gpu_available = torch.cuda.is_available()
    except Exception:
        gpu_available = False

    logger.info(f"GPU Available: {'Yes' if gpu_available else 'No'}")
    logger.success("✓ All systems ready!")
    logger.success("=" * 70)

# ============== Shutdown Event ==============
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down AgroGuard Backend")

# ============== Include Routers ==============
app.include_router(health.router)
app.include_router(disease.router,prefix="/api/disease")  # contains prefix="/api/disease"
app.include_router(chat.router)      # contains prefix="/api/chat"

# ============== Root Endpoint ==============
@app.get("/")
async def root():
    """
    Detailed API information with features
    """
    return {
        "message": "🌾 Welcome to AgroGuard API",
        "version": settings.API_VERSION,
        "description": "AI-powered pest/disease detection + farmer advisory chatbot",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "disease_prediction": "/api/disease/predict",
            "chat_text": "/api/chat/message",
            "chat_image": "/api/chat/with-image"
        },
        "features": [
            "🎯 99.31% disease classification accuracy",
            "🌿 51 supported disease/pest classes",
            "🤖 Context-aware AI chatbot",
            "🔄 Multi-LLM fallback (OpenAI + AIPipe + OpenRouter + DeepSeek)",
            "🧠 Local knowledge base + Smart reasoning",
            "💾 Chat history support",
            "⚡ Fast inference (YOLO classification – <1 ms)",
            "📱 Farmer-friendly interface",
        ]
    }

# ============== Detailed API Info Endpoint ==============
@app.get("/api/info")
async def api_info():
    """
    Complete backend, model & environment metadata.
    Useful for frontend diagnostics & system dashboard.
    """
    return {
        "api_title": settings.API_TITLE,
        "api_version": settings.API_VERSION,
        "api_description": settings.API_DESCRIPTION,

        "models": {
            "disease_classifier": {
                "model": "YOLOv8 Classification",
                "accuracy": "99.31%",
                "classes_supported": 51,
                "image_size": "224x224",
                "framework": "PyTorch",
                "inference_time_ms": 0.3
            }
        },

        "llm_providers": [
            "OpenAI GPT",
            "AIPipe",
            "OpenRouter",
            "DeepSeek",
        ],

        "supported_formats": ["JPG", "PNG"],
        "max_file_size_MB": settings.MAX_FILE_SIZE / 1024 / 1024,

        "database": {
            "engine": "PostgreSQL",
            "connection": settings.DATABASE_URL,
        },

        "deployment": {
            "backend": "FastAPI + Uvicorn",
            "environment": "production" if not settings.DEBUG else "development",
            "recommended_hosts": ["Render", "Railway", "AWS EC2"],
        }
    }

# ============== Error Handlers ==============
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "path": request.url.path,
            "message": "Endpoint not found. Visit /docs for available endpoints."
        },
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    # logger.error(f"Internal Server Error: {exc}", exc_info=True)
    logger.error(f"Internal Server Error: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Something went wrong. Please try again later."
        },
    )

# ============== Development Server ==============
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1,
        log_level=settings.LOG_LEVEL.lower()
    )




# #!/usr/bin/env python3
# """
# 🌾 AgroGuard Backend API
# Main application entry point
# """

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from starlette.middleware.gzip import GZipMiddleware
# from fastapi.responses import JSONResponse
# from pathlib import Path

# # Import configuration
# from .config import get_settings
# from .utils.logger import Logger

# # Import routers
# from .routers import health, disease, chat

# # Initialize
# settings = get_settings()
# logger = Logger(__name__)

# # ============== FastAPI App ==============
# app = FastAPI(
#     title=settings.API_TITLE,
#     version=settings.API_VERSION,
#     description=settings.API_DESCRIPTION,
#     docs_url="/docs",
#     redoc_url="/redoc",
#     openapi_url="/openapi.json"
# )

# # ============== Middleware ==============
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.add_middleware(GZipMiddleware, minimum_size=1000)

# # ============== Create Upload Directory ==============
# upload_dir = Path(settings.UPLOAD_DIR)
# upload_dir.mkdir(exist_ok=True)
# logger.success(f"✓ Upload directory ready: {upload_dir}")

# # ============== Startup Event ==============
# @app.on_event("startup")
# async def startup_event():
#     logger.success("=" * 70)
#     logger.success("🚀 AgroGuard Backend Starting")
#     logger.success("=" * 70)

#     logger.info(f"API Version: {settings.API_VERSION}")
#     logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")

#     # DB Info
#     if '@' in settings.DATABASE_URL:
#         db_info = settings.DATABASE_URL.split('@')[1]
#     else:
#         db_info = "N/A"
#     logger.info(f"Database: {db_info}")

#     # GPU Check
#     try:
#         import torch
#         gpu_available = torch.cuda.is_available()
#     except Exception:
#         gpu_available = False

#     logger.info(f"GPU Available: {'Yes' if gpu_available else 'No'}")
#     logger.success("✓ All systems ready!")
#     logger.success("=" * 70)

# # ============== Shutdown Event ==============
# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info("🛑 Shutting down AgroGuard Backend")

# # ============== Include Routers (NO DOUBLE PREFIX!) ==============

# # Health check
# app.include_router(health.router)

# # Disease prediction (router already has prefix="/api/disease")
# app.include_router(disease.router)

# # Chat (router already has prefix="/api/chat")
# app.include_router(chat.router)

# # ============== Root Endpoint ==============
# @app.get("/")
# async def root():
#     return {
#         "message": "🌾 Welcome to AgroGuard API",
#         "version": settings.API_VERSION,
#         "docs": "/docs"
#     }

# # ============== Error Handlers ==============
# @app.exception_handler(404)
# async def not_found_handler(request, exc):
#     return JSONResponse(
#         status_code=404,
#         content={
#             "error": "Not Found",
#             "path": request.url.path,
#             "message": "Endpoint not found. Visit /docs for available endpoints."
#         },
#     )

# @app.exception_handler(500)
# async def internal_error_handler(request, exc):
#     logger.error(f"Internal Server Error: {exc}", exc_info=True)
#     return JSONResponse(
#         status_code=500,
#         content={
#             "error": "Internal Server Error",
#             "message": "Something went wrong. Please try again later."
#         },
#     )

# # ============== Development Server ==============
# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(
#         "app.main:app",
#         host=settings.HOST,
#         port=settings.PORT,
#         reload=settings.DEBUG
#     )





# #!/usr/bin/env python3
# """
# 🌾 AgroGuard Backend API
# AI-powered pest detection + farmer advisory chatbot

# Main application entry point
# """

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from starlette.middleware.gzip import GZipMiddleware
# from pathlib import Path


# # Import configuration
# from .config import get_settings
# from .utils.logger import Logger

# # Import routers
# from .routers import health, disease, chat

# # Initialize
# settings = get_settings()
# logger = Logger(__name__)

# # ============== FastAPI App ==============
# app = FastAPI(
#     title=settings.API_TITLE,
#     version=settings.API_VERSION,
#     description=settings.API_DESCRIPTION,
#     docs_url="/docs",
#     redoc_url="/redoc",
#     openapi_url="/openapi.json"
# )

# # ============== Middleware ==============

# # CORS - Allow frontend connections
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # GZIP Compression
# app.add_middleware(GZipMiddleware, minimum_size=1000)

# # ============== Create Upload Directory ==============
# upload_dir = Path(settings.UPLOAD_DIR)
# upload_dir.mkdir(exist_ok=True)
# logger.success(f"✓ Upload directory ready: {upload_dir}")

# # ============== Startup Event ==============
# @app.on_event("startup")
# async def startup_event():
#     """Run on application startup"""
#     logger.success("="*70)
#     logger.success("🚀 AgroGuard Backend Starting")
#     logger.success("="*70)
#     logger.info(f"API Version: {settings.API_VERSION}")
#     logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
#     logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'N/A'}")
#     logger.info(f"GPU Available: {'Yes' if True else 'No'}")  # Will check torch
#     logger.success("✓ All systems ready!")
#     logger.success("="*70)

# # ============== Shutdown Event ==============
# @app.on_event("shutdown")
# async def shutdown_event():
#     """Run on application shutdown"""
#     logger.info("🛑 Shutting down AgroGuard Backend")

# # ============== Include Routers ==============

# # Health check
# app.include_router(health.router)

# # Disease prediction
# app.include_router(disease.router)

# # Chat
# app.include_router(chat.router)

# # ============== Root Endpoints ==============

# @app.get("/")
# async def root():
#     """
#     Root endpoint with API information
#     """
#     return {
#         "message": "🌾 Welcome to AgroGuard API",
#         "version": settings.API_VERSION,
#         "description": "AI-powered disease detection + farmer advisory chatbot",
#         "endpoints": {
#             "docs": "/docs",
#             "redoc": "/redoc",
#             "health": "/health",
#             "disease_prediction": "/api/disease/predict",
#             "chat_text": "/api/chat/message",
#             "chat_image": "/api/chat/with-image"
#         },
#         "features": [
#             "🎯 99.31% disease classification accuracy",
#             "💬 AI-powered chatbot with context awareness",
#             "🔄 Multi-LLM fallback (OpenAI + AIPipe + OpenRouter + DeepSeek)",
#             "📱 Farmer-friendly interface",
#             "💾 Chat history storage",
#             "🌱 51 disease classes supported"
#         ]
#     }

# @app.get("/api/info")
# async def api_info():
#     """
#     Get detailed API information
#     """
#     return {
#         "api_title": settings.API_TITLE,
#         "api_version": settings.API_VERSION,
#         "api_description": settings.API_DESCRIPTION,
#         "models": {
#             "disease_classifier": {
#                 "model": "YOLO Classification",
#                 "accuracy": "99.31%",
#                 "classes": 51,
#                 "image_size": "224x224",
#                 "inference_time": "0.3ms",
#                 "framework": "PyTorch"
#             }
#         },
#         "llm_providers": [
#             "OpenAI (GPT-3.5-turbo)",
#             "AIPipe",
#             "OpenRouter",
#             "DeepSeek"
#         ],
#         "supported_formats": ["JPG", "PNG"],
#         "max_file_size": f"{settings.MAX_FILE_SIZE / 1024 / 1024}MB",
#         "database": "PostgreSQL with SQLAlchemy",
#         "deployment": {
#             "backend": "FastAPI + Uvicorn",
#             "recommended_host": "Render or Railway",
#             "environment": "production" if not settings.DEBUG else "development"
#         }
#     }

# # ============== Error Handlers ==============

# @app.exception_handler(404)
# async def not_found(request, exc):
#     """Handle 404 errors"""
#     return {
#         "error": "Not Found",
#         "path": request.url.path,
#         "message": f"Endpoint not found. Visit /docs for available endpoints"
#     }

# @app.exception_handler(500)
# async def internal_error(request, exc):
#     """Handle 500 errors"""
#     logger.error(f"Internal Server Error: {str(exc)}")
#     return {
#         "error": "Internal Server Error",
#         "message": "Something went wrong. Please try again later."
#     }

# # ============== Development Server ==============

# if __name__ == "__main__":
#     import uvicorn
    
#     uvicorn.run(
#         "app.main:app",
#         host=settings.HOST,
#         port=settings.PORT,
#         workers=settings.WORKERS if not settings.DEBUG else 1,
#         reload=settings.DEBUG,
#         log_level=settings.LOG_LEVEL.lower()
#     )
