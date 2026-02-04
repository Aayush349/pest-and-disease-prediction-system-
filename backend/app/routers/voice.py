# backend/app/routers/voice.py

from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid
from pathlib import Path
from ..config import get_settings
from ..utils.logger import Logger

# Try importing Whisper safely (Production Safety)
try:
    import whisper
    model = whisper.load_model("base")
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ OpenAI Whisper not installed. Voice input will not work.")

router = APIRouter()
settings = get_settings()
logger = Logger(__name__)

TEMP_DIR = Path("temp_audio")
TEMP_DIR.mkdir(exist_ok=True)

@router.post("/transcribe", tags=["Voice Input"])
async def transcribe_voice(file: UploadFile = File(...)):
    """
    🎤 Microphone Input: Converts User Voice -> Text (Speech-to-Text)
    """
    if not WHISPER_AVAILABLE:
        raise HTTPException(status_code=500, detail="Voice recognition module not initialized")

    try:
        # Save temp file
        file_ext = file.filename.split(".")[-1]
        temp_filename = f"{uuid.uuid4()}.{file_ext}"
        temp_path = TEMP_DIR / temp_filename
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Transcribe
        logger.info(f"Transcribing voice file: {temp_filename}")
        result = model.transcribe(str(temp_path))
        
        # Cleanup
        if temp_path.exists():
            os.remove(temp_path)
            
        return {
            "success": True,
            "text": result["text"], # Ye text Chatbot ko jayega
            "language": result.get("language", "en")
        }

    except Exception as e:
        logger.error(f"Transcribe Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))