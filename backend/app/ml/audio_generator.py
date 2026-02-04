# backend/app/ml/audio_generator.py
"""
Hybrid Audio Generator (PRODUCTION READY)

✔ Edge-TTS (Primary – Natural Voice)
✔ gTTS (Fallback – Reliable)
✔ Config-based paths
✔ Language-safe voice mapping
✔ Natural pause enhancement
"""

import edge_tts
from gtts import gTTS
import uuid
from pathlib import Path
from ..config import get_settings

# ================= CONFIG =================
settings = get_settings()
AUDIO_DIR = Path(settings.UPLOAD_DIR) / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ================= VOICE MAPS =================

# 🎯 Edge-TTS (Natural voices)
EDGE_VOICE_MAP = {
    "en": "en-IN-NeerjaNeural",
    "en-US": "en-IN-NeerjaNeural",
    "en-IN": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-ShrutiNeural",
    "mr": "mr-IN-AarohiNeural",
    "bn": "bn-IN-TanishaaNeural",
    "kn": "kn-IN-SapnaNeural",
    "ml": "ml-IN-SobhanaNeural",
}

# 🎯 Google TTS fallback
GOOGLE_LANG_MAP = {
    "en": "en",
    "en-US": "en",
    "en-IN": "en",
    "hi": "hi",
    "ta": "ta",
    "te": "te",
    "mr": "mr",
    "bn": "bn",
    "kn": "kn",
    "ml": "ml",
}

# ================= HELPERS =================

def add_natural_pauses(text: str) -> str:
    """
    Makes audio sound less robotic by forcing pauses.
    """
    return (
        text.replace(". ", "... ")
            .replace(":", "... ")
            .replace("\n", "... ")
    )

# ================= MAIN GENERATOR =================

async def generate_audio_response(text: str, language: str = "en") -> str:
    """
    Hybrid Audio Generator:
    1️⃣ Edge-TTS (Primary – Natural)
    2️⃣ gTTS (Fallback – Reliable)

    Returns:
        filename (str) or "" if failed
    """

    # Clean + enhance text
    final_text = add_natural_pauses(text)

    # File naming (clean + short)
    filename = f"audio_{uuid.uuid4().hex[:8]}.mp3"
    output_path = AUDIO_DIR / filename

    # ---------------- PLAN A: EDGE-TTS ----------------
    try:
        print(f"🎤 Trying Edge-TTS for lang: {language}")

        lang_key = language[:2].lower()
        voice = EDGE_VOICE_MAP.get(
            lang_key,
            EDGE_VOICE_MAP.get(language, "en-IN-NeerjaNeural")
        )

        communicate = edge_tts.Communicate(final_text, voice)
        await communicate.save(str(output_path))

        print("✅ Edge-TTS Success")
        return filename

    except Exception as e:
        print(f"⚠️ Edge-TTS Failed: {e}")
        print("🔄 Switching to Google TTS fallback...")

    # ---------------- PLAN B: GOOGLE TTS ----------------
    try:
        g_lang = GOOGLE_LANG_MAP.get(language[:2], "en")
        tld = "co.in" if language in ["hi", "en-IN"] else "com"

        tts = gTTS(
            text=final_text,
            lang=g_lang,
            tld=tld,
            slow=False
        )
        tts.save(str(output_path))

        print("✅ Google-TTS Success (Fallback)")
        return filename

    except Exception as g_e:
        print(f"❌ CRITICAL: Both TTS engines failed: {g_e}")
        return ""



# # backend/app/ml/audio_generator.py

# import edge_tts
# from gtts import gTTS
# import uuid
# import os
# from pathlib import Path
# from ..config import get_settings
# settings = get_settings()
# # 🎯 VOICE MAPPING (For Edge-TTS - Natural)
# EDGE_VOICE_MAP = {
#     "en": "en-US-AriaNeural",
#     "en-US": "en-US-AriaNeural",
#     "en-IN": "en-IN-NeerjaNeural",
#     "hi": "hi-IN-SwaraNeural",
#     "ta": "ta-IN-PallaviNeural",
#     "te": "te-IN-MohanNeural",
#     "mr": "mr-IN-AarohiNeural",
#     "bn": "bn-IN-TanishaaNeural",
#     "kn": "kn-IN-GaganNeural",
#     "ml": "ml-IN-SobhanaNeural"
# }
# def add_natural_pauses(text: str) -> str:
#     return text.replace(". ", "... ").replace(":", "... ").replace("\n", "... ")

# # 🎯 GOOGLE MAPPING (Backup - Robotic but Reliable)
# GOOGLE_LANG_MAP = {
#     "en": "en", "en-US": "en", "en-IN": "en",
#     "hi": "hi", "ta": "ta", "te": "te",
#     "mr": "mr", "bn": "bn", "kn": "kn", "ml": "ml"
# }

# async def generate_audio_response(text: str, language: str = "en") -> str:
#     """
#     Hybrid Audio Generator:
#     1. Tries Edge-TTS (Best Quality)
#     2. Falls back to gTTS (Best Reliability) if Edge fails
#     """
    
#     filename = f"speech_{uuid.uuid4()}.mp3"
#     upload_dir = Path(settings.UPLOAD_DIR) / "audio"
#     upload_dir.mkdir(parents=True, exist_ok=True)
#     output_path = upload_dir / filename

#     # --- PLAN A: EDGE-TTS (Natural Voice) ---
#     try:
#         print(f"🎤 Trying Edge-TTS for lang: {language}...")
#         lang_key = language[:2]
#         voice = EDGE_VOICE_MAP.get(lang_key, EDGE_VOICE_MAP.get(language, "en-US-AriaNeural"))
#         communicate = edge_tts.Communicate(text, voice)
#         await communicate.save(str(output_path))
#         print("✅ Edge-TTS Success!")
#         return filename

#     except Exception as e:
#         print(f"⚠️ Edge-TTS Failed: {e}")
#         print("🔄 Switching to Plan B: Google TTS...")

#         # --- PLAN B: GOOGLE TTS (Backup) ---
#         try:
#             g_lang = GOOGLE_LANG_MAP.get(language, "en")
#             # 'tld' can be set to 'co.in' for Indian accent in Google too
#             tld = 'co.in' if language in ['en-IN', 'hi'] else 'com'
            
#             tts = gTTS(text=text, lang=g_lang, tld=tld, slow=False)
#             tts.save(str(output_path))
#             print("✅ Google-TTS Success! (Backup used)")
#             return filename
            
#         except Exception as g_e:
#             print(f"❌ CRITICAL: Both TTS engines failed. {g_e}")
#             return None