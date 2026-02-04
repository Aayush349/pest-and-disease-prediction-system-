#!/usr/bin/env python3

"""

AgroGuard Configuration Manager

Master config with Gemini + YOLO + All LLMs + Security

Pydantic v2 + .env structure

"""



import os

from pathlib import Path

from pydantic_settings import BaseSettings

from pydantic import Field, validator

from typing import List, Optional, Dict, Any



# Base directory

BASE_DIR = Path(__file__).parent.parent



class Settings(BaseSettings):

    """Application settings - Fully Integrated for AgroGuard Hybrid Engine"""

   

    # ============================================================

    # 🌟 Environment & Server

    # ============================================================

    ENVIRONMENT: str = "production"  # development/production

    DEBUG: bool = False

    API_HOST: str = "0.0.0.0"

    API_PORT: int = 8000

    API_TITLE: str = "🌾 AgroGuard AI"

    API_VERSION: str = "2.0.0"

    API_DESCRIPTION: str = "Hybrid AI Engine: Gemini Vision (95%+) + Local YOLO"

    API_PREFIX: str = "/api/v1"

   

    # ============================================================

    # 🚀 HYBRID AI ENGINE - Master Switch Configuration

    # ============================================================

   

    # 🔥 GEMINI VISION (Primary - Online Mode)

    GEMINI_API_KEY: str = ""

    GEMINI_MODEL: str = "gemini-pro"

    GEMINI_VISION_ENABLED: bool = False

    GEMINI_CONFIDENCE_THRESHOLD: float = 0.85

   
# 🏗️ DUAL-CORE YOLO (Micro-Level Engine)
    YOLO_MODEL_V1_PATH: str = "app/ml/models/model_v1.pt"
    YOLO_MODEL_V2_PATH: str = "app/ml/models/model_v2.pt"
    KNOWLEDGE_BASE_FILE: str = "ml/knowledge_base/diseases.json"
    YOLO_MODEL_PATH: str = "app/ml/models/model_v2.pt"

    # Validators ko bhi update karein taaki paths absolute ho jayein
    @validator("YOLO_MODEL_V1_PATH", "YOLO_MODEL_V2_PATH", pre=True)
    def validate_yolo_paths(cls, v):
        root = Path(__file__).parent.parent.parent # Root directory tak pahuncho
        return str(root / v)


    # 🏗️ LOCAL YOLO (Fallback - Offline Mode)

    YOLO_MODEL_PATH: str = "ml/yolo_classification/weights/best.pt"

    MODEL_PATH: str = "ml/models/yolo_classification/disease_classifier_v1/weights/best.pt"

    YOLO_CONFIDENCE_THRESHOLD: float = 0.4

    YOLO_FALLBACK_MODEL: str = "yolov8n.pt"

   

    # 📚 KNOWLEDGE BASE

    KNOWLEDGE_BASE_PATH: str = "ml/data/knowledge_base"

    KNOWLEDGE_BASE_FILE: str = "diseases.json"

    KB_PATH: str = "ml/knowledge_base/diseases.json"

    # ============================================================

    # 💬 LLM CHATBOT - Multi-Provider Fallback Chain

    # ============================================================

   

    # Chain Order (first to last)

    LLM_PROVIDER_CHAIN: List[str] = ["openai", "gemini", "deepseek", "openrouter"]

    DEFAULT_LLM: str = "openai"

   

    # Shared LLM Settings

    LLM_MODEL: str = "gpt-3.5-turbo"

    LLM_TEMPERATURE: float = 0.7

    LLM_MAX_TOKENS: int = 500

    LLM_TIMEOUT: int = 30

   

    # 🤖 OpenAI

    OPENAI_API_KEY: Optional[str] = ""

    OPENAI_MODEL: str = "gpt-4o-mini"

    OPENAI_ORGANIZATION: Optional[str] = ""

   

    # 🤖 Gemini (Text)

    GEMINI_TEXT_MODEL: str = "gemini-1.5-flash"

   

    # 🤖 DeepSeek

    DEEPSEEK_API_KEY: Optional[str] = ""

    DEEPSEEK_MODEL: str = "deepseek-chat"

    DEEPSEEK_ENDPOINT: str = "https://api.deepseek.com/v1/chat/completions"

   

    # 🤖 OpenRouter

    OPENROUTER_API_KEY: Optional[str] = "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"

    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"


    OPENROUTER_ENDPOINT: str = "https://openrouter.ai/api/v1/chat/completions"

   

    # 🤖 AIPipe (Legacy Support)

    AIPIPE_API_KEY: Optional[str] = ""

    AIPIPE_MODEL: str = "gpt-3.5-turbo"

    AIPIPE_ENDPOINT: str = "https://api.aipipe.io/v1/chat/completions"

   

    # ============================================================

    # 🗄️ Database & Storage

    # ============================================================

    DATABASE_URL: str = "sqlite:///./agroguard.db"

    SQLALCHEMY_ECHO: bool = False

    DATABASE_POOL_SIZE: int = 20

    DATABASE_MAX_OVERFLOW: int = 40

   

    # ============================================================

    # 🔐 Security & Authentication

    # ============================================================

    SECRET_KEY: str = Field(

        default="agroguard-secure-key-2024-change-in-production",

        min_length=32

    )

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    PASSWORD_HASH_ALGORITHM: str = "bcrypt"

   

    # ============================================================

    # 🌐 CORS & Security Headers

    # ============================================================

    CORS_ORIGINS: List[str] = Field(

        default_factory=lambda: [

            "http://localhost:3000",

            "http://localhost:5173",

            "http://localhost:8000",

            "http://127.0.0.1:3000",

            "http://127.0.0.1:5173",

            "https://agroguard.app",

            "https://*.agroguard.app",

        ]

    )

   

    CORS_ALLOW_CREDENTIALS: bool = True

    CORS_ALLOW_METHODS: List[str] = ["*"]

    CORS_ALLOW_HEADERS: List[str] = ["*"]

   

    # Security Headers

    SECURE_HEADERS: Dict[str, str] = {

        "X-Frame-Options": "DENY",

        "X-Content-Type-Options": "nosniff",

        "X-XSS-Protection": "1; mode=block",

        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",

    }

   

    # ============================================================

    # 📁 File Uploads & Storage

    # ============================================================

    UPLOAD_DIR: str = "./uploads"

    MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20 MB

    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp", "bmp"]

    ALLOWED_VIDEO_EXTENSIONS: List[str] = ["mp4", "avi", "mov", "mkv"]

   

    # Image Processing

    IMAGE_MAX_WIDTH: int = 1920

    IMAGE_MAX_HEIGHT: int = 1080

    THUMBNAIL_SIZE: tuple = (300, 300)

   

    # ============================================================

    # 📊 Logging & Monitoring

    # ============================================================

    LOG_LEVEL: str = "INFO"

    LOG_FILE: str = "./logs/agroguard.log"

    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

   

    # Sentry (Optional)

    SENTRY_DSN: Optional[str] = ""

    SENTRY_TRACES_SAMPLE_RATE: float = 1.0

   

    # ============================================================

    # 🚀 Performance & Caching

    # ============================================================

    CACHE_ENABLED: bool = True

    CACHE_TTL: int = 300  # 5 minutes

    CACHE_TYPE: str = "memory"  # memory/redis

    REDIS_URL: Optional[str] = ""

   

    # Request Rate Limiting

    RATE_LIMIT_ENABLED: bool = True

    RATE_LIMIT_REQUESTS: int = 100  # per minute

    RATE_LIMIT_PERIOD: int = 60  # seconds

   

    # ============================================================

    # 📱 Mobile & API Clients

    # ============================================================

    APP_NAME: str = "AgroGuard"

    APP_VERSION: str = "2.0.0"

    APP_CONTACT_EMAIL: str = "support@agroguard.ai"

   

    # API Rate Limits for different tiers

    API_TIERS: Dict[str, Dict[str, int]] = {

        "free": {"requests_per_day": 100, "max_image_size": 5 * 1024 * 1024},

        "premium": {"requests_per_day": 1000, "max_image_size": 20 * 1024 * 1024},

        "enterprise": {"requests_per_day": 10000, "max_image_size": 50 * 1024 * 1024},

    }

   

    # ============================================================

    # 🌍 Agricultural Specific Settings

    # ============================================================

    # Supported crops

    SUPPORTED_CROPS: List[str] = [

        "Tomato", "Potato", "Rice", "Wheat", "Corn",

        "Sugarcane", "Cotton", "Soybean", "Chili", "Brinjal"

    ]

   

    # Supported languages

    SUPPORTED_LANGUAGES: List[str] = ["en", "hi", "ta", "te", "mr", "bn"]

    DEFAULT_LANGUAGE: str = "en"

   

    # Agricultural APIs

    WEATHER_API_KEY: Optional[str] = ""

    SOIL_API_KEY: Optional[str] = ""

    MARKET_PRICE_API_KEY: Optional[str] = ""

   

    # ============================================================

    # ⚙️ System Configuration

    # ============================================================

    # Worker threads for YOLO

    YOLO_WORKERS: int = 4

    YOLO_BATCH_SIZE: int = 8

   

    # Gemini retry settings

    GEMINI_MAX_RETRIES: int = 3

    GEMINI_RETRY_DELAY: int = 2

   

    # Health check endpoints

    HEALTH_CHECK_PATH: str = "/health"

    READINESS_PATH: str = "/ready"

    LIVENESS_PATH: str = "/alive"

   

    # ============================================================

    # 🔧 Validators & Post-Processing

    # ============================================================

   

    @validator("YOLO_MODEL_PATH", pre=True)

    def validate_yolo_path(cls, v):

        """Ensure YOLO model path is absolute"""

        if not v:

            return str(BASE_DIR / "ml/models/yolo_classification/disease_classifier_v1/weights/best.pt")

       

        path = Path(v)

        if not path.is_absolute():

            return str(BASE_DIR / v)

        return str(path)

   

    @validator("KNOWLEDGE_BASE_PATH", pre=True)

    def validate_kb_path(cls, v):

        """Ensure knowledge base path is absolute"""

        if not v:

            return str(BASE_DIR / "ml/knowledge_base")

       

        path = Path(v)

        if not path.is_absolute():

            return str(BASE_DIR / v)

        return str(path)

   

    @validator("UPLOAD_DIR", pre=True)

    def validate_upload_dir(cls, v):

        """Ensure upload directory exists"""

        path = Path(v)

        if not path.is_absolute():

            path = BASE_DIR / v

       

        path.mkdir(parents=True, exist_ok=True)

        return str(path)

   

    @validator("GEMINI_API_KEY")

    def validate_gemini_key(cls, v, values):

        """Warn if Gemini key is missing but vision is enabled"""

        if values.get("GEMINI_VISION_ENABLED") and not v:

            print("⚠️  WARNING: GEMINI_API_KEY is empty but GEMINI_VISION_ENABLED=True")

        return v

   

    @validator("OPENAI_API_KEY")

    def validate_openai_key(cls, v, values):

        """Warn if OpenAI key is missing but it's default LLM"""

        if values.get("DEFAULT_LLM") == "openai" and not v:

            print("⚠️  WARNING: OPENAI_API_KEY is empty but DEFAULT_LLM=openai")

        return v

   



    # Validators ko ".." (parent directory) use karne ko bolein



    @validator("MODEL_PATH", pre=True)



    def validate_model_path(cls, v):



        # BASE_DIR is 'backend'. ML is sibling to backend.



        # So we go to backend/../ml/...



        return str(BASE_DIR.parent / v)







    @validator("KNOWLEDGE_BASE_PATH", pre=True)



    def validate_kb_path(cls, v):



        return str(BASE_DIR.parent / v)

   

   

    @validator("MODEL_PATH", "KB_PATH", pre=True)

    def make_absolute(cls, v):

        # BASE_DIR (app) -> parent (backend) -> parent (AgroGuard Root)

        root = Path(__file__).parent.parent.parent

        return str(root / v)

   

    # ============================================================

    # 💡 Property Methods

    # ============================================================

   

    @property

    def knowledge_base_file(self) -> str:

        """Get full path to diseases.json"""

        return str(Path(self.KNOWLEDGE_BASE_PATH) / self.KNOWLEDGE_BASE_FILE)

   

    @property

    def is_development(self) -> bool:

        """Check if running in development mode"""

        return self.ENVIRONMENT.lower() in ["dev", "development", "local"]

   

    @property

    def is_production(self) -> bool:

        """Check if running in production mode"""

        return self.ENVIRONMENT.lower() in ["prod", "production"]

   

    @property

    def full_model_path(self) -> str:

        """Get absolute path to YOLO model"""

        path = Path(self.YOLO_MODEL_PATH)

        if not path.exists():

            # Check in BASE_DIR

            alt_path = BASE_DIR / self.YOLO_MODEL_PATH

            if alt_path.exists():

                return str(alt_path)

        return str(path)

   

    @property

    def allowed_extensions(self) -> List[str]:

        """Get all allowed file extensions"""

        return self.ALLOWED_IMAGE_EXTENSIONS + self.ALLOWED_VIDEO_EXTENSIONS

   

    @property

    def cors_origins(self) -> List[str]:

        """Get CORS origins with environment-specific additions"""

        origins = self.CORS_ORIGINS.copy()

       

        if self.is_development:

            origins.extend([

                "http://localhost:8080",

                "http://localhost:8081",

                "http://localhost:3001",

            ])

       

        # Remove duplicates

        return list(set(origins))

   

    @property

    def database_url(self) -> str:

        """Get database URL with absolute path for SQLite"""

        if self.DATABASE_URL.startswith("sqlite"):

            # Ensure SQLite path is absolute

            db_path = self.DATABASE_URL.replace("sqlite:///", "")

            if not db_path.startswith("/"):

                db_path = str(BASE_DIR / db_path)

            return f"sqlite:///{db_path}"

        return self.DATABASE_URL

   

    class Config:

        env_file = ".env"

        env_file_encoding = "utf-8"

        case_sensitive = True

        extra = "ignore"  # Ignore extra env vars

       

        # Environment variable prefix (optional)

        # env_prefix = "AGROGUARD_"





# Global settings instance

settings = Settings()





def get_settings() -> Settings:

    """Get settings singleton instance"""

    return settings





# Helper function to get config for specific components

def get_llm_config() -> Dict[str, Any]:

    """Get LLM-specific configuration"""

    return {

        "default_provider": settings.DEFAULT_LLM,

        "providers": settings.LLM_PROVIDER_CHAIN,

        "temperature": settings.LLM_TEMPERATURE,

        "max_tokens": settings.LLM_MAX_TOKENS,

        "timeout": settings.LLM_TIMEOUT,

        "openai": {

            "api_key": settings.OPENAI_API_KEY,

            "model": settings.OPENAI_MODEL,

        },

        "gemini": {

            "api_key": settings.GEMINI_API_KEY,

            "vision_model": settings.GEMINI_MODEL,

            "text_model": settings.GEMINI_TEXT_MODEL,

        },

        "deepseek": {

            "api_key": settings.DEEPSEEK_API_KEY,

            "model": settings.DEEPSEEK_MODEL,

            "endpoint": settings.DEEPSEEK_ENDPOINT,

        },

        "openrouter": {

            "api_key": settings.OPENROUTER_API_KEY,

            "model": settings.OPENROUTER_MODEL,

            "endpoint": settings.OPENROUTER_ENDPOINT,

        },

    }





def get_ml_config() -> Dict[str, Any]:

    """Get ML-specific configuration"""

    return {

        "hybrid_mode": settings.GEMINI_VISION_ENABLED,

        "gemini": {

            "enabled": settings.GEMINI_VISION_ENABLED,

            "confidence_threshold": settings.GEMINI_CONFIDENCE_THRESHOLD,

            "max_retries": settings.GEMINI_MAX_RETRIES,

        },

        "yolo": {

            "model_path": settings.full_model_path,

            "confidence_threshold": settings.YOLO_CONFIDENCE_THRESHOLD,

            "fallback_model": settings.YOLO_FALLBACK_MODEL,

            "workers": settings.YOLO_WORKERS,

            "batch_size": settings.YOLO_BATCH_SIZE,

        },

        "knowledge_base": {

            "path": settings.KNOWLEDGE_BASE_PATH,

            "file": settings.knowledge_base_file,

        }

    }





def get_security_config() -> Dict[str, Any]:

    """Get security configuration"""

    return {

        "cors_origins": settings.cors_origins,

        "rate_limiting": {

            "enabled": settings.RATE_LIMIT_ENABLED,

            "requests_per_minute": settings.RATE_LIMIT_REQUESTS,

        },

        "jwt": {

            "secret_key": settings.SECRET_KEY,

            "algorithm": settings.ALGORITHM,

            "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,

        }

    }





# Print configuration summary on import

if __name__ == "config":

    print(f"✅ AgroGuard Configuration Loaded")

    print(f"   Environment: {settings.ENVIRONMENT}")

    print(f"   API: {settings.API_HOST}:{settings.API_PORT}")

    print(f"   Gemini Vision: {'✅ Enabled' if settings.GEMINI_VISION_ENABLED else '❌ Disabled'}")

    print(f"   Default LLM: {settings.DEFAULT_LLM}")

    print(f"   YOLO Model: {Path(settings.YOLO_MODEL_PATH).name}")

    print(f"   Knowledge Base: {len(settings.SUPPORTED_CROPS)} crops supported")






# #!/usr/bin/env python3
# """
# AgroGuard Configuration Manager
# Master config with Gemini + YOLO + All LLMs + Security
# Pydantic v2 + .env structure
# """

# import os
# from pathlib import Path
# from pydantic_settings import BaseSettings
# from pydantic import Field, validator
# from typing import List, Optional, Dict, Any

# # Base directory
# BASE_DIR = Path(__file__).parent.parent

# class Settings(BaseSettings):
#     """Application settings - Fully Integrated for AgroGuard Hybrid Engine"""
    
#     # ============================================================
#     # 🌟 Environment & Server
#     # ============================================================
#     ENVIRONMENT: str = "production"  # development/production
#     DEBUG: bool = False
#     API_HOST: str = "0.0.0.0"
#     API_PORT: int = 8000
#     API_TITLE: str = "🌾 AgroGuard AI"
#     API_VERSION: str = "2.0.0"
#     API_DESCRIPTION: str = "Hybrid AI Engine: Gemini Vision (95%+) + Local YOLO"
#     API_PREFIX: str = "/api/v1"
    
#     # ============================================================
#     # 🚀 HYBRID AI ENGINE - Master Switch Configuration
#     # ============================================================
    
#     # 🔥 GEMINI VISION (Primary - Online Mode)
#     GEMINI_API_KEY: str = ""
#     GEMINI_MODEL: str = "gemini-1.5-flash"
#     GEMINI_VISION_ENABLED: bool = True
#     GEMINI_CONFIDENCE_THRESHOLD: float = 0.85
    
#     # 🏗️ LOCAL YOLO (Fallback - Offline Mode)
#     YOLO_MODEL_PATH: str = "ml/yolo_classification/weights/best.pt"
#     MODEL_PATH: str = "ml/models/yolo_classification/disease_classifier_v1/weights/best.pt"
#     YOLO_CONFIDENCE_THRESHOLD: float = 0.4
#     YOLO_FALLBACK_MODEL: str = "yolov8n.pt"
    
#     # 📚 KNOWLEDGE BASE
#     KNOWLEDGE_BASE_PATH: str = "ml/data/knowledge_base"
#     KNOWLEDGE_BASE_FILE: str = "diseases.json"
#     KB_PATH: str = "ml/knowledge_base/diseases.json"
#     # ============================================================
#     # 💬 LLM CHATBOT - Multi-Provider Fallback Chain
#     # ============================================================
    
#     # Chain Order (first to last)
#     LLM_PROVIDER_CHAIN: List[str] = ["openai", "gemini", "deepseek", "openrouter"]
#     DEFAULT_LLM: str = "openai"
    
#     # Shared LLM Settings
#     LLM_MODEL: str = "gpt-3.5-turbo"
#     LLM_TEMPERATURE: float = 0.7
#     LLM_MAX_TOKENS: int = 500
#     LLM_TIMEOUT: int = 30
    
#     # 🤖 OpenAI
#     OPENAI_API_KEY: Optional[str] = ""
#     OPENAI_MODEL: str = "gpt-4o-mini"
#     OPENAI_ORGANIZATION: Optional[str] = ""
    
#     # 🤖 Gemini (Text)
#     GEMINI_TEXT_MODEL: str = "gemini-1.5-flash"
    
#     # 🤖 DeepSeek
#     DEEPSEEK_API_KEY: Optional[str] = ""
#     DEEPSEEK_MODEL: str = "deepseek-chat"
#     DEEPSEEK_ENDPOINT: str = "https://api.deepseek.com/v1/chat/completions"
    
#     # 🤖 OpenRouter
#     OPENROUTER_API_KEY: Optional[str] = ""
#     OPENROUTER_MODEL: str = "openai/gpt-3.5-turbo"
#     OPENROUTER_ENDPOINT: str = "https://openrouter.ai/api/v1/chat/completions"
    
#     # 🤖 AIPipe (Legacy Support)
#     AIPIPE_API_KEY: Optional[str] = ""
#     AIPIPE_MODEL: str = "gpt-3.5-turbo"
#     AIPIPE_ENDPOINT: str = "https://api.aipipe.io/v1/chat/completions"
    
#     # ============================================================
#     # 🗄️ Database & Storage
#     # ============================================================
#     DATABASE_URL: str = "sqlite:///./agroguard.db"
#     SQLALCHEMY_ECHO: bool = False
#     DATABASE_POOL_SIZE: int = 20
#     DATABASE_MAX_OVERFLOW: int = 40
    
#     # ============================================================
#     # 🔐 Security & Authentication
#     # ============================================================
#     SECRET_KEY: str = Field(
#         default="agroguard-secure-key-2024-change-in-production",
#         min_length=32
#     )
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
#     REFRESH_TOKEN_EXPIRE_DAYS: int = 7
#     PASSWORD_HASH_ALGORITHM: str = "bcrypt"
    
#     # ============================================================
#     # 🌐 CORS & Security Headers
#     # ============================================================
#     CORS_ORIGINS: List[str] = Field(
#         default_factory=lambda: [
#             "http://localhost:3000",
#             "http://localhost:5173",
#             "http://localhost:8000",
#             "http://127.0.0.1:3000",
#             "http://127.0.0.1:5173",
#             "https://agroguard.app",
#             "https://*.agroguard.app",
#         ]
#     )
    
#     CORS_ALLOW_CREDENTIALS: bool = True
#     CORS_ALLOW_METHODS: List[str] = ["*"]
#     CORS_ALLOW_HEADERS: List[str] = ["*"]
    
#     # Security Headers
#     SECURE_HEADERS: Dict[str, str] = {
#         "X-Frame-Options": "DENY",
#         "X-Content-Type-Options": "nosniff",
#         "X-XSS-Protection": "1; mode=block",
#         "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
#     }
    
#     # ============================================================
#     # 📁 File Uploads & Storage
#     # ============================================================
#     UPLOAD_DIR: str = "./uploads"
#     MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20 MB
#     ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp", "bmp"]
#     ALLOWED_VIDEO_EXTENSIONS: List[str] = ["mp4", "avi", "mov", "mkv"]
    
#     # Image Processing
#     IMAGE_MAX_WIDTH: int = 1920
#     IMAGE_MAX_HEIGHT: int = 1080
#     THUMBNAIL_SIZE: tuple = (300, 300)
    
#     # ============================================================
#     # 📊 Logging & Monitoring
#     # ============================================================
#     LOG_LEVEL: str = "INFO"
#     LOG_FILE: str = "./logs/agroguard.log"
#     LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
#     # Sentry (Optional)
#     SENTRY_DSN: Optional[str] = ""
#     SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    
#     # ============================================================
#     # 🚀 Performance & Caching
#     # ============================================================
#     CACHE_ENABLED: bool = True
#     CACHE_TTL: int = 300  # 5 minutes
#     CACHE_TYPE: str = "memory"  # memory/redis
#     REDIS_URL: Optional[str] = ""
    
#     # Request Rate Limiting
#     RATE_LIMIT_ENABLED: bool = True
#     RATE_LIMIT_REQUESTS: int = 100  # per minute
#     RATE_LIMIT_PERIOD: int = 60  # seconds
    
#     # ============================================================
#     # 📱 Mobile & API Clients
#     # ============================================================
#     APP_NAME: str = "AgroGuard"
#     APP_VERSION: str = "2.0.0"
#     APP_CONTACT_EMAIL: str = "support@agroguard.ai"
    
#     # API Rate Limits for different tiers
#     API_TIERS: Dict[str, Dict[str, int]] = {
#         "free": {"requests_per_day": 100, "max_image_size": 5 * 1024 * 1024},
#         "premium": {"requests_per_day": 1000, "max_image_size": 20 * 1024 * 1024},
#         "enterprise": {"requests_per_day": 10000, "max_image_size": 50 * 1024 * 1024},
#     }
    
#     # ============================================================
#     # 🌍 Agricultural Specific Settings
#     # ============================================================
#     # Supported crops
#     SUPPORTED_CROPS: List[str] = [
#         "Tomato", "Potato", "Rice", "Wheat", "Corn", 
#         "Sugarcane", "Cotton", "Soybean", "Chili", "Brinjal"
#     ]
    
#     # Supported languages
#     SUPPORTED_LANGUAGES: List[str] = ["en", "hi", "ta", "te", "mr", "bn"]
#     DEFAULT_LANGUAGE: str = "en"
    
#     # Agricultural APIs
#     WEATHER_API_KEY: Optional[str] = ""
#     SOIL_API_KEY: Optional[str] = ""
#     MARKET_PRICE_API_KEY: Optional[str] = ""
    
#     # ============================================================
#     # ⚙️ System Configuration
#     # ============================================================
#     # Worker threads for YOLO
#     YOLO_WORKERS: int = 4
#     YOLO_BATCH_SIZE: int = 8
    
#     # Gemini retry settings
#     GEMINI_MAX_RETRIES: int = 3
#     GEMINI_RETRY_DELAY: int = 2
    
#     # Health check endpoints
#     HEALTH_CHECK_PATH: str = "/health"
#     READINESS_PATH: str = "/ready"
#     LIVENESS_PATH: str = "/alive"
    
#     # ============================================================
#     # 🔧 Validators & Post-Processing
#     # ============================================================
    
#     @validator("YOLO_MODEL_PATH", pre=True)
#     def validate_yolo_path(cls, v):
#         """Ensure YOLO model path is absolute"""
#         if not v:
#             return str(BASE_DIR / "ml/models/yolo_classification/disease_classifier_v1/weights/best.pt")
        
#         path = Path(v)
#         if not path.is_absolute():
#             return str(BASE_DIR / v)
#         return str(path)
    
#     @validator("KNOWLEDGE_BASE_PATH", pre=True)
#     def validate_kb_path(cls, v):
#         """Ensure knowledge base path is absolute"""
#         if not v:
#             return str(BASE_DIR / "ml/knowledge_base")
        
#         path = Path(v)
#         if not path.is_absolute():
#             return str(BASE_DIR / v)
#         return str(path)
    
#     @validator("UPLOAD_DIR", pre=True)
#     def validate_upload_dir(cls, v):
#         """Ensure upload directory exists"""
#         path = Path(v)
#         if not path.is_absolute():
#             path = BASE_DIR / v
        
#         path.mkdir(parents=True, exist_ok=True)
#         return str(path)
    
#     @validator("GEMINI_API_KEY")
#     def validate_gemini_key(cls, v, values):
#         """Warn if Gemini key is missing but vision is enabled"""
#         if values.get("GEMINI_VISION_ENABLED") and not v:
#             print("⚠️  WARNING: GEMINI_API_KEY is empty but GEMINI_VISION_ENABLED=True")
#         return v
    
#     @validator("OPENAI_API_KEY")
#     def validate_openai_key(cls, v, values):
#         """Warn if OpenAI key is missing but it's default LLM"""
#         if values.get("DEFAULT_LLM") == "openai" and not v:
#             print("⚠️  WARNING: OPENAI_API_KEY is empty but DEFAULT_LLM=openai")
#         return v
    

#     # Validators ko ".." (parent directory) use karne ko bolein

#     @validator("MODEL_PATH", pre=True)

#     def validate_model_path(cls, v):

#         # BASE_DIR is 'backend'. ML is sibling to backend.

#         # So we go to backend/../ml/...

#         return str(BASE_DIR.parent / v)



#     @validator("KNOWLEDGE_BASE_PATH", pre=True)

#     def validate_kb_path(cls, v):

#         return str(BASE_DIR.parent / v)
    
    
#     @validator("MODEL_PATH", "KB_PATH", pre=True)
#     def make_absolute(cls, v):
#         # BASE_DIR (app) -> parent (backend) -> parent (AgroGuard Root)
#         root = Path(__file__).parent.parent.parent 
#         return str(root / v)
    
#     # ============================================================
#     # 💡 Property Methods
#     # ============================================================
    
#     @property
#     def knowledge_base_file(self) -> str:
#         """Get full path to diseases.json"""
#         return str(Path(self.KNOWLEDGE_BASE_PATH) / self.KNOWLEDGE_BASE_FILE)
    
#     @property
#     def is_development(self) -> bool:
#         """Check if running in development mode"""
#         return self.ENVIRONMENT.lower() in ["dev", "development", "local"]
    
#     @property
#     def is_production(self) -> bool:
#         """Check if running in production mode"""
#         return self.ENVIRONMENT.lower() in ["prod", "production"]
    
#     @property
#     def full_model_path(self) -> str:
#         """Get absolute path to YOLO model"""
#         path = Path(self.YOLO_MODEL_PATH)
#         if not path.exists():
#             # Check in BASE_DIR
#             alt_path = BASE_DIR / self.YOLO_MODEL_PATH
#             if alt_path.exists():
#                 return str(alt_path)
#         return str(path)
    
#     @property
#     def allowed_extensions(self) -> List[str]:
#         """Get all allowed file extensions"""
#         return self.ALLOWED_IMAGE_EXTENSIONS + self.ALLOWED_VIDEO_EXTENSIONS
    
#     @property
#     def cors_origins(self) -> List[str]:
#         """Get CORS origins with environment-specific additions"""
#         origins = self.CORS_ORIGINS.copy()
        
#         if self.is_development:
#             origins.extend([
#                 "http://localhost:8080",
#                 "http://localhost:8081",
#                 "http://localhost:3001",
#             ])
        
#         # Remove duplicates
#         return list(set(origins))
    
#     @property
#     def database_url(self) -> str:
#         """Get database URL with absolute path for SQLite"""
#         if self.DATABASE_URL.startswith("sqlite"):
#             # Ensure SQLite path is absolute
#             db_path = self.DATABASE_URL.replace("sqlite:///", "")
#             if not db_path.startswith("/"):
#                 db_path = str(BASE_DIR / db_path)
#             return f"sqlite:///{db_path}"
#         return self.DATABASE_URL
    
#     class Config:
#         env_file = ".env"
#         env_file_encoding = "utf-8"
#         case_sensitive = True
#         extra = "ignore"  # Ignore extra env vars
        
#         # Environment variable prefix (optional)
#         # env_prefix = "AGROGUARD_"


# # Global settings instance
# settings = Settings()


# def get_settings() -> Settings:
#     """Get settings singleton instance"""
#     return settings


# # Helper function to get config for specific components
# def get_llm_config() -> Dict[str, Any]:
#     """Get LLM-specific configuration"""
#     return {
#         "default_provider": settings.DEFAULT_LLM,
#         "providers": settings.LLM_PROVIDER_CHAIN,
#         "temperature": settings.LLM_TEMPERATURE,
#         "max_tokens": settings.LLM_MAX_TOKENS,
#         "timeout": settings.LLM_TIMEOUT,
#         "openai": {
#             "api_key": settings.OPENAI_API_KEY,
#             "model": settings.OPENAI_MODEL,
#         },
#         "gemini": {
#             "api_key": settings.GEMINI_API_KEY,
#             "vision_model": settings.GEMINI_MODEL,
#             "text_model": settings.GEMINI_TEXT_MODEL,
#         },
#         "deepseek": {
#             "api_key": settings.DEEPSEEK_API_KEY,
#             "model": settings.DEEPSEEK_MODEL,
#             "endpoint": settings.DEEPSEEK_ENDPOINT,
#         },
#         "openrouter": {
#             "api_key": settings.OPENROUTER_API_KEY,
#             "model": settings.OPENROUTER_MODEL,
#             "endpoint": settings.OPENROUTER_ENDPOINT,
#         },
#     }


# def get_ml_config() -> Dict[str, Any]:
#     """Get ML-specific configuration"""
#     return {
#         "hybrid_mode": settings.GEMINI_VISION_ENABLED,
#         "gemini": {
#             "enabled": settings.GEMINI_VISION_ENABLED,
#             "confidence_threshold": settings.GEMINI_CONFIDENCE_THRESHOLD,
#             "max_retries": settings.GEMINI_MAX_RETRIES,
#         },
#         "yolo": {
#             "model_path": settings.full_model_path,
#             "confidence_threshold": settings.YOLO_CONFIDENCE_THRESHOLD,
#             "fallback_model": settings.YOLO_FALLBACK_MODEL,
#             "workers": settings.YOLO_WORKERS,
#             "batch_size": settings.YOLO_BATCH_SIZE,
#         },
#         "knowledge_base": {
#             "path": settings.KNOWLEDGE_BASE_PATH,
#             "file": settings.knowledge_base_file,
#         }
#     }


# def get_security_config() -> Dict[str, Any]:
#     """Get security configuration"""
#     return {
#         "cors_origins": settings.cors_origins,
#         "rate_limiting": {
#             "enabled": settings.RATE_LIMIT_ENABLED,
#             "requests_per_minute": settings.RATE_LIMIT_REQUESTS,
#         },
#         "jwt": {
#             "secret_key": settings.SECRET_KEY,
#             "algorithm": settings.ALGORITHM,
#             "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
#         }
#     }


# # Print configuration summary on import
# if __name__ == "config":
#     print(f"✅ AgroGuard Configuration Loaded")
#     print(f"   Environment: {settings.ENVIRONMENT}")
#     print(f"   API: {settings.API_HOST}:{settings.API_PORT}")
#     print(f"   Gemini Vision: {'✅ Enabled' if settings.GEMINI_VISION_ENABLED else '❌ Disabled'}")
#     print(f"   Default LLM: {settings.DEFAULT_LLM}")
#     print(f"   YOLO Model: {Path(settings.YOLO_MODEL_PATH).name}")
#     print(f"   Knowledge Base: {len(settings.SUPPORTED_CROPS)} crops supported")

# #!/usr/bin/env python3
# """
# Configuration management for AgroGuard
# Compatible with Pydantic v2 + .env structure
# """

# from pydantic_settings import BaseSettings
# from pydantic import Field
# from typing import List, Optional

# class Settings(BaseSettings):
#     """Application settings"""

#     # ============================================================
#     # Environment & Server
#     # ============================================================
#     ENVIRONMENT: str = "production"
#     DEBUG: bool = False
#     API_HOST: str = "0.0.0.0"
#     API_PORT: int = 8000
#     API_TITLE: str = "🌾 AgroGuard API"
#     API_VERSION: str = "1.0.0"
#     API_DESCRIPTION: str = "AI-powered disease detection + chatbot for farmers"

#     # ============================================================
#     # 🔥 LLM — Unified Config (REQUIRED BY llm_provider.py)
#     # ============================================================

#     # Default provider
#     DEFAULT_LLM: str = "openai"

#     # Shared settings used by all LLM providers
#     LLM_MODEL: str = "gpt-3.5-turbo"
#     LLM_TEMPERATURE: float = 0.7
#     LLM_MAX_TOKENS: int = 400

#     # ------------------------
#     # OpenAI
#     # ------------------------
#     OPENAI_API_KEY: Optional[str] = ""
#     OPENAI_MODEL: str = "gpt-3.5-turbo"

#     # ------------------------
#     # AIPipe
#     # ------------------------
#     AIPIPE_API_KEY: Optional[str] = ""
#     AIPIPE_MODEL: str = "gpt-3.5-turbo"
#     AIPIPE_ENDPOINT: str = "https://api.aipipe.io/v1/chat/completions"

#     # ------------------------
#     # OpenRouter
#     # ------------------------
#     OPENROUTER_API_KEY: Optional[str] = ""
#     OPENROUTER_MODEL: str = "openai/gpt-3.5-turbo"
#     OPENROUTER_ENDPOINT: str = "https://openrouter.ai/api/v1/chat/completions"

#     # ------------------------
#     # DeepSeek
#     # ------------------------
#     DEEPSEEK_API_KEY: Optional[str] = ""
#     DEEPSEEK_MODEL: str = "deepseek-chat"
#     DEEPSEEK_ENDPOINT: str = "https://api.deepseek.com/v1/chat/completions"

#     # Provider list (for fallback chain)
#     LLM_PROVIDERS: list = ["openai", "aipipe", "openrouter", "deepseek"]

#     # ============================================================
#     # ML Models & Data
#     # ============================================================
#     MODEL_PATH: str = "ml/models/yolo_classification/disease_classifier_v1/weights/best.pt"
#     KB_PATH: str = "ml/knowledge_base/diseases.json"
#     # KB_PATH: str = "../../../ml/knowledge_base/diseases.json"

#     # ============================================================
#     # Database
#     # ============================================================
#     DATABASE_URL: str = "sqlite:///./agroguard.db"
#     SQLALCHEMY_ECHO: bool = False

#     # ============================================================
#     # CORS
#     # ============================================================
#     CORS_ORIGINS: List[str] = Field(default_factory=lambda: [
#         "http://localhost:3000",
#         "http://localhost:5173",
#         "http://127.0.0.1:3000",
#         "http://127.0.0.1:5173",
#     ])

#     # ============================================================
#     # File Uploads
#     # ============================================================
#     UPLOAD_DIR: str = "./uploads"
#     MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
#     ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png"]

#     # ============================================================
#     # Security
#     # ============================================================
#     SECRET_KEY: str = "your-secret-key-here"
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

#     # ============================================================
#     # Logging
#     # ============================================================
#     LOG_LEVEL: str = "INFO"

#     class Config:
#         env_file = ".env"
#         env_file_encoding = "utf-8"
#         case_sensitive = True
#         extra = "ignore"   # IMPORTANT: avoids crashes from unexpected env vars


# # Singleton
# settings = Settings()

# def get_settings() -> Settings:
#     return settings






# #!/usr/bin/env python3
# """
# Configuration management for AgroGuard
# Compatible with Pydantic v2 + .env structure
# """

# from pydantic_settings import BaseSettings
# from pydantic import Field
# from typing import List, Optional

# class Settings(BaseSettings):
#     """Application settings"""
    
#     # =========================
#     # Environment & Server
#     # =========================
#     ENVIRONMENT: str = "production"
#     DEBUG: bool = False
#     API_HOST: str = "0.0.0.0"
#     API_PORT: int = 8000
#     API_TITLE: str = "🌾 AgroGuard API"
#     API_VERSION: str = "1.0.0"
#     API_DESCRIPTION: str = "AI-powered disease detection + chatbot for farmers"
    
#     # =========================
#     # LLM KEYS + Settings
#     # =========================
#     OPENAI_API_KEY: Optional[str] = ""
#     OPENAI_MODEL: str = "gpt-3.5-turbo"
#     OPENAI_MAX_TOKENS: int = 300
#     OPENAI_TEMPERATURE: float = 0.7

#     AIPIPE_API_KEY: Optional[str] = ""
#     AIPIPE_MODEL: str = "gpt-4"
#     AIPIPE_ENDPOINT: str = "https://api.aipipe.io/v1/chat/completions"

#     OPENROUTER_API_KEY: Optional[str] = ""
#     OPENROUTER_MODEL: str = "openai/gpt-3.5-turbo"
#     OPENROUTER_ENDPOINT: str = "https://openrouter.ai/api/v1/chat/completions"

#     DEEPSEEK_API_KEY: Optional[str] = ""
#     DEEPSEEK_ENDPOINT: str = "https://api.deepseek.com/v1/chat/completions"


#     DEFAULT_LLM: str = "openai"
#     LLM_PROVIDERS: list = ["openai", "aipipe", "openrouter", "deepseek"]

#     # =========================
#     # ML Models & Data Paths
#     # =========================
#     # MODEL_PATH: str = "../ml/models/yolo_classification/disease_classifier_v1/weights/best.pt"
#     MODEL_PATH: str = "ml/models/yolo_classification/disease_classifier_v1/weights/best.pt"
#     KB_PATH: str = "../ml/knowledge_base/diseases.json"
    
#     # =========================
#     # Database
#     # =========================
#     DATABASE_URL: str = "sqlite:///./agroguard.db"
#     SQLALCHEMY_ECHO: bool = False
    
#     # =========================
#     # CORS (Frontend URLs)
#     # =========================
#     CORS_ORIGINS: List[str] = Field(default_factory=lambda: [
#         "http://localhost:3000",
#         "http://localhost:5173",
#         "http://127.0.0.1:3000",
#         "http://127.0.0.1:5173",
#     ])
    
#     # =========================
#     # File Uploads
#     # =========================
#     UPLOAD_DIR: str = "./uploads"
#     MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
#     ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png"]
    
#     # =========================
#     # Security
#     # =========================
#     SECRET_KEY: str = "your-secret-key-here"
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
#     # =========================
#     # Logging
#     # =========================
#     LOG_LEVEL: str = "INFO"
    
#     class Config:
#         env_file = ".env"
#         env_file_encoding = "utf-8"
#         case_sensitive = True
#         extra = 'ignore'  # This is the line that fixes the crash

# # Singleton
# settings = Settings()

# def get_settings() -> Settings:
#     """Get settings instance"""
#     return settings




# class Settings(BaseSettings):
#     API_TITLE: str = "AgroGuard API"
#     API_VERSION: str = "1.0.0"
#     API_DESCRIPTION: str = "AI-powered agriculture assistant"

#     # Add these 3 lines ↓↓↓
#     DEFAULT_LLM: str = "openai"                # default provider
#     OPENAI_API_KEY: str = ""                  # or fetch from env
#     LLM_PROVIDERS: list = ["openai", "aipipe", "openrouter", "deepseek"]

#     UPLOAD_DIR: str = "uploads"
#     MAX_FILE_SIZE: int = 5 * 1024 * 1024
#     DEBUG: bool = True





# """
# Configuration management
# Loads from .env file and environment variables
# """

# from pydantic_settings import BaseSettings
# from pathlib import Path
# from typing import List

# class Settings(BaseSettings):
#     """Application settings"""
    
#     # API Configuration
#     API_TITLE: str = "🌾 AgroGuard API"
#     API_VERSION: str = "1.0.0"
#     API_DESCRIPTION: str = "AI-powered disease detection + chatbot for farmers"
#     DEBUG: bool = False
    
#     # Server
#     HOST: str = "0.0.0.0"
#     PORT: int = 8000
#     WORKERS: int = 4
    
#     # CORS
#     CORS_ORIGINS: List[str] = [
#         "http://localhost:3000",
#         "http://localhost:5173",
#         "http://127.0.0.1:3000",
#         "http://127.0.0.1:5173",
#     ]
    
#     # Database
#     DATABASE_URL: str = "postgresql://user:password@localhost:5432/agroguard"
#     SQLALCHEMY_ECHO: bool = False
    
#     # File Upload
#     UPLOAD_DIR: str = "./uploads"
#     MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
#     ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png"]
    
#     # ML Model Paths
#     MODEL_PATH: str = "../ml/models/yolo_classification/disease_classifier_v1/weights/best.pt"
#     KB_PATH: str = "../ml/knowledge_base/diseases.json"
    
#     # LLM Configuration
#     OPENAI_API_KEY: str = ""
#     AIPIPE_API_KEY: str = ""
#     OPENROUTER_API_KEY: str = ""
#     DEFAULT_LLM: str = "openai"  # openai, aipipe, openrouter, deepseek
#     LLM_MODEL: str = "gpt-3.5-turbo"
#     LLM_TEMPERATURE: float = 0.7
#     LLM_MAX_TOKENS: int = 500
    
#     # Security
#     SECRET_KEY: str = "your-secret-key-here"
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
#     # Logging
#     LOG_LEVEL: str = "INFO"
#     LOG_FILE: str = "./logs/app.log"
    
#     class Config:
#         env_file = ".env"
#         env_file_encoding = "utf-8"
#         case_sensitive = True
#         extra = 'ignore'

# # Singleton
# settings = Settings()

# def get_settings() -> Settings:
#     """Get settings instance"""
#     return settings
