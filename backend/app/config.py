#!/usr/bin/env python3
"""
Configuration management for AgroGuard
Compatible with Pydantic v2 + .env structure
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings"""

    # ============================================================
    # Environment & Server
    # ============================================================
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "🌾 AgroGuard API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "AI-powered disease detection + chatbot for farmers"

    # ============================================================
    # 🔥 LLM — Unified Config (REQUIRED BY llm_provider.py)
    # ============================================================

    # Default provider
    DEFAULT_LLM: str = "openai"

    # Shared settings used by all LLM providers
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 400

    # ------------------------
    # OpenAI
    # ------------------------
    OPENAI_API_KEY: Optional[str] = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    # ------------------------
    # AIPipe
    # ------------------------
    AIPIPE_API_KEY: Optional[str] = ""
    AIPIPE_MODEL: str = "gpt-3.5-turbo"
    AIPIPE_ENDPOINT: str = "https://api.aipipe.io/v1/chat/completions"

    # ------------------------
    # OpenRouter
    # ------------------------
    OPENROUTER_API_KEY: Optional[str] = ""
    OPENROUTER_MODEL: str = "openai/gpt-3.5-turbo"
    OPENROUTER_ENDPOINT: str = "https://openrouter.ai/api/v1/chat/completions"

    # ------------------------
    # DeepSeek
    # ------------------------
    DEEPSEEK_API_KEY: Optional[str] = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_ENDPOINT: str = "https://api.deepseek.com/v1/chat/completions"

    # Provider list (for fallback chain)
    LLM_PROVIDERS: list = ["openai", "aipipe", "openrouter", "deepseek"]

    # ============================================================
    # ML Models & Data
    # ============================================================
    MODEL_PATH: str = "ml/models/yolo_classification/disease_classifier_v1/weights/best.pt"
    KB_PATH: str = "ml/knowledge_base/diseases.json"

    # ============================================================
    # Database
    # ============================================================
    DATABASE_URL: str = "sqlite:///./agroguard.db"
    SQLALCHEMY_ECHO: bool = False

    # ============================================================
    # CORS
    # ============================================================
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ])

    # ============================================================
    # File Uploads
    # ============================================================
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png"]

    # ============================================================
    # Security
    # ============================================================
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ============================================================
    # Logging
    # ============================================================
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"   # IMPORTANT: avoids crashes from unexpected env vars


# Singleton
settings = Settings()

def get_settings() -> Settings:
    return settings






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
