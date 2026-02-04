from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import edge_tts
import uuid
from pathlib import Path
from ..config import get_settings
from ..utils.logger import Logger

# ================= INIT =================
router = APIRouter(prefix="/api/tts", tags=["Text to Speech"])
settings = get_settings()
logger = Logger(__name__)

# 📂 Audio will live here: uploads/audio/
AUDIO_DIR = Path(settings.UPLOAD_DIR) / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ================= VOICE MAP =================
VOICE_MAP = {
    "hi": "hi-IN-SwaraNeural",     # Hindi (best)
    "mr": "mr-IN-AarohiNeural",    # Marathi
    "ta": "ta-IN-PallaviNeural",   # Tamil
    "te": "te-IN-ShrutiNeural",    # Telugu
    "kn": "kn-IN-SapnaNeural",     # Kannada
    "en": "en-IN-NeerjaNeural",    # Indian English
}

def add_natural_pauses(text: str) -> str:
    """
    Makes speech sound human (breathing + pauses)
    """
    text = text.replace(". ", "... ")
    text = text.replace("\n", "... ")
    return text

# ================= API =================
@router.post("/speak")
async def text_to_speech(text: str, language: str = "en"):
    """
    🔊 Converts advisory text → natural audio
    """
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text is required for TTS")

    try:
        # 1️⃣ Language → voice
        lang_code = language[:2].lower()
        voice = VOICE_MAP.get(lang_code, VOICE_MAP["en"])

        # 2️⃣ Human-like pauses
        final_text = add_natural_pauses(text)

        # 3️⃣ Generate file
        filename = f"advice_{uuid.uuid4().hex[:8]}.mp3"
        output_path = AUDIO_DIR / filename

        communicate = edge_tts.Communicate(final_text, voice)
        await communicate.save(str(output_path))

        logger.success(f"🔊 Audio generated: {output_path}")

        return FileResponse(
            output_path,
            media_type="audio/mpeg",
            filename=filename
        )

    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail="Audio generation failed")
