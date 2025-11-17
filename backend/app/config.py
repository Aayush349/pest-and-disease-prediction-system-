from pydantic_settings import BaseSettings
from functools import lru_cache
import logging
from pathlib import Path

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "AgroGuard API"
    API_VERSION: str = "1.0.0"
    
    # ============================================
    # PRIMARY LLM (OpenAI / OpenRouter)
    # ============================================
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS: int = 300
    OPENAI_TEMPERATURE: float = 0.7
    
    # ============================================
    # FALLBACK LLM 1: AIPipe
    # ============================================
    AIPIPE_API_KEY: str = ""
    AIPIPE_MODEL: str = "gpt-4"
    AIPIPE_ENDPOINT: str = "https://api.aipipe.io/v1/chat/completions"
    
    # ============================================
    # FALLBACK LLM 2: OpenRouter
    # ============================================
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-3.5-turbo"
    OPENROUTER_ENDPOINT: str = "https://openrouter.ai/api/v1/chat/completions"
    
    # ============================================
    # FALLBACK LLM 3: DeepSeek (FREE!)
    # ============================================
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_ENDPOINT: str = "https://api.deepseek.com/v1/chat/completions"
    
    # ML Models
    YOLO_MODEL_PATH: str = "../ml/models/yolo/disease_detector_v1/weights/best.pt"
    VIT_MODEL_PATH: str = "../ml/models/vit/model.pth"
    LSTM_MODEL_PATH: str = "../ml/models/lstm/forecaster.pth"
    KNOWLEDGE_BASE_PATH: str = "../ml/knowledge_base"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173"
    ]
    
    # File Upload
    MAX_FILE_SIZE: int = 10485760
    UPLOAD_DIR: str = "./uploads"
    ALLOWED_EXTENSIONS: list = ["jpg", "jpeg", "png", "gif"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

def setup_logging():
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()
