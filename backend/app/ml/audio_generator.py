# backend/app/ml/audio_generator.py

import edge_tts
from gtts import gTTS
import uuid
import os
from pathlib import Path

# 🎯 VOICE MAPPING (For Edge-TTS - Natural)
EDGE_VOICE_MAP = {
    "en": "en-US-AriaNeural",
    "en-US": "en-US-AriaNeural",
    "en-IN": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-MohanNeural",
    "mr": "mr-IN-AarohiNeural",
    "bn": "bn-IN-TanishaaNeural",
    "kn": "kn-IN-GaganNeural",
    "ml": "ml-IN-SobhanaNeural"
}

# 🎯 GOOGLE MAPPING (Backup - Robotic but Reliable)
GOOGLE_LANG_MAP = {
    "en": "en", "en-US": "en", "en-IN": "en",
    "hi": "hi", "ta": "ta", "te": "te",
    "mr": "mr", "bn": "bn", "kn": "kn", "ml": "ml"
}

async def generate_audio_response(text: str, language: str = "en") -> str:
    """
    Hybrid Audio Generator:
    1. Tries Edge-TTS (Best Quality)
    2. Falls back to gTTS (Best Reliability) if Edge fails
    """
    
    filename = f"speech_{uuid.uuid4()}.mp3"
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    output_path = upload_dir / filename

    # --- PLAN A: EDGE-TTS (Natural Voice) ---
    try:
        print(f"🎤 Trying Edge-TTS for lang: {language}...")
        voice = EDGE_VOICE_MAP.get(language, "en-US-AriaNeural")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        print("✅ Edge-TTS Success!")
        return filename

    except Exception as e:
        print(f"⚠️ Edge-TTS Failed: {e}")
        print("🔄 Switching to Plan B: Google TTS...")

        # --- PLAN B: GOOGLE TTS (Backup) ---
        try:
            g_lang = GOOGLE_LANG_MAP.get(language, "en")
            # 'tld' can be set to 'co.in' for Indian accent in Google too
            tld = 'co.in' if language in ['en-IN', 'hi'] else 'com'
            
            tts = gTTS(text=text, lang=g_lang, tld=tld, slow=False)
            tts.save(str(output_path))
            print("✅ Google-TTS Success! (Backup used)")
            return filename
            
        except Exception as g_e:
            print(f"❌ CRITICAL: Both TTS engines failed. {g_e}")
            return None