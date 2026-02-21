#!/usr/bin/env python3
"""
🌾 AgroGuard Backend API
AI-powered disease detection + farmer advisory chatbot + Smart Weather + TTS
Version: 3.0 (Integrated OpenRouter & EdgeTTS)
"""


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from .routers import news  # <--- Import news
from .routers import health, disease, chat, analytics, weather, tts, news, voice, mandi  # <--- Add mandi
from fastapi.staticfiles import StaticFiles # <--- Import
from .routers import risk
from .routers import nutrient_advisor
from .routers import auth # <-- Import the new router
from .routers import farmer  # <-- Farmer profile & fields router
from .routers import pest_forecast  # <-- Pest & Disease Forecast

# Import configuration
from .config import get_settings
from .utils.logger import Logger

# Import all routers (Added 'weather' and 'tts')
from .routers import health, disease, chat, analytics, weather, tts

from .database import engine, Base
# Ye line add karte hi server start hote hi tables ban jayengi!
Base.metadata.create_all(bind=engine)

# Initialize
settings = get_settings()
logger = Logger(__name__)

# ============== FastAPI App ==============
app = FastAPI(
    title=settings.API_TITLE,
    version="3.0.0",
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

# ============== Load Model Metrics (Dynamic) ==============
def get_model_metrics():
    """
    Load actual model metrics from evaluation results
    """
    try:
        eval_file = Path("ml/evaluation/results.json")
        
        if eval_file.exists():
            import json
            with open(eval_file, 'r') as f:
                eval_data = json.load(f)
                return {
                    "accuracy": f"{eval_data.get('top1_accuracy', 0)*100:.2f}%",
                    "top5_accuracy": f"{eval_data.get('top5_accuracy', 0)*100:.2f}%",
                    "classes": eval_data.get('num_classes', 51),
                    "inference_time_ms": eval_data.get('inference_time_ms', 0.3)
                }
        else:
            # Fallback
            return {
                "accuracy": "98.5% (Estimated)",
                "classes": 51,
                "inference_time_ms": 0.3
            }
    except Exception as e:
        logger.warning(f"Could not load model metrics: {e}")
        return {"accuracy": "N/A", "classes": 51, "inference_time_ms": 0.3}

# ============== Startup Event ==============
@app.on_event("startup")
async def startup_event():
    logger.success("=" * 70)
    logger.success("🚀 AgroGuard Backend Starting")
    logger.success("=" * 70)

    logger.info(f"API Version: {settings.API_VERSION}")
    
    # Database Info
    db_info = settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else "SQLite (Local)"
    logger.info(f"Database: {db_info}")

    # GPU Check
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        logger.info(f"GPU Available: {'Yes (' + torch.cuda.get_device_name(0) + ')' if gpu_available else 'No (Using CPU)'}")
    except Exception:
        logger.info("GPU Check: PyTorch not found or CPU only")
    
    logger.success("✓ All systems ready!")
    logger.success("=" * 70)

# ============== Shutdown Event ==============
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down AgroGuard Backend")

# ============== Include Routers ==============
# Core
app.include_router(health.router)

# Weapon 1: Disease Detection
app.include_router(disease.router, prefix="/api/disease", tags=["Disease Detection"]) 

# Weapon 2: Chatbot (Text & Image)
app.include_router(chat.router, tags=["Chatbot"])

# Weapon 3: Smart Weather & Advisory (New)
app.include_router(weather.router, prefix="/api/weather", tags=["Smart Weather Advisory"])

# Analytics & Tools
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(tts.router, prefix="/api/tts", tags=["Text to Speech"])

app.include_router(news.router, prefix="/api/news", tags=["News Ticker"])

# ... baki routers ...
# app.include_router(news.router, prefix="/api/news", tags=["News Ticker"]) # <--- Ye line add karo

app.include_router(tts.router, prefix="/api/tts", tags=["Output: Speaker"]) 

app.include_router(voice.router, prefix="/api/voice", tags=["Input: Microphone"]) # NEW

app.include_router(risk.router, prefix="/api/risk", tags=["Risk Prediction"])

app.include_router(nutrient_advisor.router, prefix="/api/nutrients", tags=["Weapon 6: NPK Advisor"])

app.include_router(auth.router, prefix="/api", tags=["Auth & Security"])

app.include_router(farmer.router, prefix="/api", tags=["Farmer Profile"])

app.include_router(mandi.router, prefix="/api/mandi", tags=["Mandi Bhav"])

app.include_router(pest_forecast.router, prefix="/api/pest", tags=["Pest & Disease Forecast"])

# ============== Static File Mounts ==============
app.mount("/uploads/images", StaticFiles(directory="uploads/images"), name="images")
app.mount("/uploads/pdfs", StaticFiles(directory="uploads/pdfs"), name="pdfs")
app.mount("/uploads/audio", StaticFiles(directory="uploads/audio"), name="audio")

# ============== Root Endpoint ==============
@app.get("/")
async def root():
    """
    Detailed API information with features
    """
    metrics = get_model_metrics()
    
    return {
        "message": "🌾 Welcome to AgroGuard API",
        "version": "3.0.0",
        "description": "AI-powered disease detection + farmer advisory chatbot",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "disease_predict": "/api/disease/predict",
            "chat": "/api/chat/message",
            "weather": "/api/weather/advisory",
            "tts": "/api/tts/speak"
        },
        "features": [
            f"🎯 {metrics['accuracy']} Accuracy Disease Detection",
            "🤖 AI Chatbot (OpenRouter/AIPipe Integration)",
            "🌦️ Real-time Weather & Spray Advisory (Location Based)",
            "🗣️ Microsoft Edge Neural TTS (Natural Hindi/Regional Voice)",
            "🌍 Multi-language Support"
        ]
    }

# ============== Detailed API Info Endpoint ==============
@app.get("/api/info")
async def api_info():
    return {
        "api": "AgroGuard Backend",
        "status": "Online",
        "services": {
            "disease_detection": "Active (YOLOv8)",
            "chatbot": "Active (OpenRouter/AIPipe)",
            "weather": "Active (OpenWeatherMap)",
            "tts": "Active (Microsoft Edge TTS)"
        }
    }

# ============== Error Handlers ==============
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": "Not Found", "message": "Endpoint does not exist."})

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal Server Error: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal Server Error", "message": "Something went wrong."})

# ============== Development Server ==============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        workers=1,
        log_level="info"
    )









# #!/usr/bin/env python3
# """
# 🌾 AgroGuard Backend API
# AI-powered disease detection + farmer advisory chatbot
# Version: Dynamic (NO hardcoded metrics)
# """
# from .routers import disease, chat, health, analytics
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

# # ============== Load Model Metrics (Dynamic) ==============
# def get_model_metrics():
#     """
#     Load actual model metrics from evaluation results
#     NO HARDCODING!
#     """
#     try:
#         # Try to load from evaluation results file
#         eval_file = Path("ml/evaluation/results.json")
        
#         if eval_file.exists():
#             import json
#             with open(eval_file, 'r') as f:
#                 eval_data = json.load(f)
#                 return {
#                     "accuracy": f"{eval_data.get('top1_accuracy', 0)*100:.2f}%",
#                     "top5_accuracy": f"{eval_data.get('top5_accuracy', 0)*100:.2f}%",
#                     "classes": eval_data.get('num_classes', 51),
#                     "inference_time_ms": eval_data.get('inference_time_ms', 0.3)
#                 }
#         else:
#             # Fallback: Get from classifier directly
#             from .ml.disease_classifier import classifier
#             if classifier and classifier.is_ready:
#                 return {
#                     "accuracy": "Trained Model (See evaluation results)",
#                     "top5_accuracy": "99%+",
#                     "classes": 51,
#                     "inference_time_ms": 0.3
#                 }
#             else:
#                 return {
#                     "accuracy": "Model loading...",
#                     "classes": 51,
#                     "inference_time_ms": 0.3
#                 }
#     except Exception as e:
#         logger.warning(f"Could not load model metrics: {e}")
#         return {
#             "accuracy": "See evaluation results",
#             "classes": 51,
#             "inference_time_ms": 0.3
#         }

# # ============== Startup Event ==============
# @app.on_event("startup")
# async def startup_event():
#     logger.success("=" * 70)
#     logger.success("🚀 AgroGuard Backend Starting")
#     logger.success("=" * 70)

#     logger.info(f"API Version: {settings.API_VERSION}")
#     logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")

#     # Database Info
#     if '@' in settings.DATABASE_URL:
#         db_info = settings.DATABASE_URL.split('@')[1]
#     else:
#         db_info = "SQLite (Local)"
#     logger.info(f"Database: {db_info}")

#     # GPU Check
#     try:
#         import torch
#         gpu_available = torch.cuda.is_available()
#         if gpu_available:
#             logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
#     except Exception:
#         gpu_available = False

#     logger.info(f"GPU Available: {'Yes' if gpu_available else 'No (Using CPU)'}")
    
#     # Load model metrics
#     metrics = get_model_metrics()
#     logger.info(f"Model Accuracy: {metrics['accuracy']}")
#     logger.info(f"Supported Classes: {metrics['classes']}")
    
#     logger.success("✓ All systems ready!")
#     logger.success("=" * 70)

# # ============== Shutdown Event ==============
# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info("🛑 Shutting down AgroGuard Backend")

# # ============== Include Routers ==============
# app.include_router(health.router)
# app.include_router(disease.router,prefix="/api/disease")  # ✅ FIXED: No double prefix
# app.include_router(chat.router)
# app.include_router(analytics.router, prefix="/api/analytics")

# # ============== Root Endpoint ==============
# @app.get("/")
# async def root():
#     """
#     Detailed API information with features
#     """
#     metrics = get_model_metrics()  # ✅ Dynamic metrics
    
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
#             f"🎯 {metrics['accuracy']} disease classification accuracy",  # ✅ Dynamic
#             f"🌿 {metrics['classes']} supported disease classes",  # ✅ Dynamic
#             "🤖 Context-aware AI chatbot",
#             "🔄 Multi-LLM fallback (OpenAI + AIPipe + OpenRouter + DeepSeek)",
#             "🧠 Local knowledge base + Smart reasoning",
#             "💾 Chat history support",
#             f"⚡ Fast inference (~{metrics['inference_time_ms']}ms)",  # ✅ Dynamic
#             "📱 Farmer-friendly interface",
#             "🌍 Multi-language support (English, Hindi, Regional)"
#         ]
#     }

# # ============== Detailed API Info Endpoint ==============
# @app.get("/api/info")
# async def api_info():
#     """
#     Complete backend, model & environment metadata
#     """
#     metrics = get_model_metrics()  # ✅ Dynamic metrics
    
#     return {
#         "api_title": settings.API_TITLE,
#         "api_version": settings.API_VERSION,
#         "api_description": settings.API_DESCRIPTION,

#         "models": {
#             "disease_classifier": {
#                 "model": "YOLOv8 Classification",
#                 "accuracy": metrics["accuracy"],  # ✅ Dynamic
#                 "top5_accuracy": metrics.get("top5_accuracy", "99%+"),  # ✅ Dynamic
#                 "classes_supported": metrics["classes"],  # ✅ Dynamic
#                 "image_size": "224x224",
#                 "framework": "PyTorch",
#                 "inference_time_ms": metrics["inference_time_ms"],  # ✅ Dynamic
#                 "training_images": 118965,
#                 "training_epochs": 100,
#                 "device": "CUDA" if settings.DEBUG else "Auto-detect"
#             }
#         },

#         "llm_providers": [
#             "OpenAI GPT-3.5/4",
#             "AIPipe",
#             "OpenRouter",
#             "DeepSeek (Free)"
#         ],

#         "supported_formats": ["JPG", "PNG"],
#         "max_file_size_MB": settings.MAX_FILE_SIZE / 1024 / 1024,

#         "database": {
#             "engine": "PostgreSQL / SQLite",
#             "connection": "Connected" if settings.DATABASE_URL else "None"
#         },

#         "deployment": {
#             "backend": "FastAPI + Uvicorn",
#             "environment": "production" if not settings.DEBUG else "development",
#             "recommended_hosts": ["Render", "Railway", "AWS EC2", "Vercel"]
#         },
        
#         "languages_supported": [
#             "English",
#             "Hindi (हिंदी)",
#             "Tamil (தமிழ்)",
#             "Telugu (తెలుగు)",
#             "Marathi (मराठी)",
#             "Bengali (বাংলা)",
#             "Kannada (ಕನ್ನಡ)",
#             "Malayalam (മലയാളം)"
#         ]
#     }

# # ============== Error Handlers ==============
# @app.exception_handler(404)
# async def not_found_handler(request, exc):
#     return JSONResponse(
#         status_code=404,
#         content={
#             "error": "Not Found",
#             "path": str(request.url.path),
#             "message": "Endpoint not found. Visit /docs for available endpoints."
#         },
#     )

# @app.exception_handler(500)
# async def internal_error_handler(request, exc):
#     logger.error(f"Internal Server Error: {exc}")
    
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
#         host=settings.API_HOST,
#         port=settings.API_PORT,
#         reload=settings.DEBUG,
#         workers=settings.WORKERS if not settings.DEBUG else 1,
#         log_level=settings.LOG_LEVEL.lower()
#     )












# #!/usr/bin/env python3
# """
# 🌾 AgroGuard Backend API
# AI-powered pest/disease detection + farmer advisory chatbot
# Merged + Improved Version (Stable + Full Features)
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

#     # Database Info
#     if '@' in settings.DATABASE_URL:
#         db_info = settings.DATABASE_URL.split('@')[1]
#     else:
#         db_info = "N/A"
#     logger.info(f"Database: {db_info}")

#     # GPU Check (Real Torch Check)
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

# # ============== Include Routers ==============
# app.include_router(health.router)
# app.include_router(disease.router,prefix="/api/disease")  # contains prefix="/api/disease"
# app.include_router(chat.router)      # contains prefix="/api/chat"

# # ============== Root Endpoint ==============
# @app.get("/")
# async def root():
#     """
#     Detailed API information with features
#     """
#     return {
#         "message": "🌾 Welcome to AgroGuard API",
#         "version": settings.API_VERSION,
#         "description": "AI-powered pest/disease detection + farmer advisory chatbot",
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
#             "🌿 51 supported disease/pest classes",
#             "🤖 Context-aware AI chatbot",
#             "🔄 Multi-LLM fallback (OpenAI + AIPipe + OpenRouter + DeepSeek)",
#             "🧠 Local knowledge base + Smart reasoning",
#             "💾 Chat history support",
#             "⚡ Fast inference (YOLO classification – <1 ms)",
#             "📱 Farmer-friendly interface",
#         ]
#     }

# # ============== Detailed API Info Endpoint ==============
# @app.get("/api/info")
# async def api_info():
#     """
#     Complete backend, model & environment metadata.
#     Useful for frontend diagnostics & system dashboard.
#     """
#     return {
#         "api_title": settings.API_TITLE,
#         "api_version": settings.API_VERSION,
#         "api_description": settings.API_DESCRIPTION,

#         "models": {
#             "disease_classifier": {
#                 "model": "YOLOv8 Classification",
#                 "accuracy": "99.31%",
#                 "classes_supported": 51,
#                 "image_size": "224x224",
#                 "framework": "PyTorch",
#                 "inference_time_ms": 0.3
#             }
#         },

#         "llm_providers": [
#             "OpenAI GPT",
#             "AIPipe",
#             "OpenRouter",
#             "DeepSeek",
#         ],

#         "supported_formats": ["JPG", "PNG"],
#         "max_file_size_MB": settings.MAX_FILE_SIZE / 1024 / 1024,

#         "database": {
#             "engine": "PostgreSQL",
#             "connection": settings.DATABASE_URL,
#         },

#         "deployment": {
#             "backend": "FastAPI + Uvicorn",
#             "environment": "production" if not settings.DEBUG else "development",
#             "recommended_hosts": ["Render", "Railway", "AWS EC2"],
#         }
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
#     # logger.error(f"Internal Server Error: {exc}", exc_info=True)
#     logger.error(f"Internal Server Error: {exc}")

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
#         reload=settings.DEBUG,
#         workers=settings.WORKERS if not settings.DEBUG else 1,
#         log_level=settings.LOG_LEVEL.lower()
#     )




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
