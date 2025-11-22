from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import edge_tts
import uuid
import os

router = APIRouter()
AUDIO_DIR = "temp_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

@router.post("/speak", tags=["TTS"])
async def text_to_speech(text: str, language: str = "hindi"):
    """
    Converts text to audio using Microsoft Edge Neural Voices
    """
    try:
        # Auto-Select Best Neural Voice
        voice = "hi-IN-SwaraNeural" # Default Hindi Female
        
        lang_lower = language.lower()
        if "tamil" in lang_lower: voice = "ta-IN-PallaviNeural"
        elif "telugu" in lang_lower: voice = "te-IN-ShrutiNeural"
        elif "marathi" in lang_lower: voice = "mr-IN-AarohiNeural"
        elif "english" in lang_lower: voice = "en-IN-NeerjaNeural"
        
        # Generate Audio
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filepath)
        
        return FileResponse(filepath, media_type="audio/mpeg", filename="advice.mp3")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))