#!/usr/bin/env python3
"""
Multi-language translation support
Translates responses to Hindi and other Indian languages
FIXED: Uses deep-translator to avoid httpcore/httpx conflicts
"""

from deep_translator import GoogleTranslator
from ..config import get_settings
from ..utils.logger import Logger

logger = Logger(__name__)
settings = get_settings()

# Language codes
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "mr": "Marathi (मराठी)",
    "bn": "Bengali (বাংলা)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ml": "Malayalam (മലയാളം)"
}

# Common farming terms dictionary (Useful for UI later)
FARMING_TERMS = {
    "en": {
        "disease": "Disease",
        "treatment": "Treatment",
        "prevention": "Prevention",
        "confidence": "Confidence"
    },
    "hi": {
        "disease": "रोग",
        "treatment": "उपचार",
        "prevention": "रोकथाम",
        "confidence": "विश्वास स्तर"
    }
}

def translate_response(text: str, target_language: str = "en"):
    """
    Translate response to target language using Deep Translator
    
    Args:
        text: English text to translate
        target_language: Target language code (en, hi, ta, etc.)
    
    Returns:
        Translated text
    """
    
    # 1. Skip if English or empty
    if not text or target_language == "en":
        return text
    
    try:
        # 2. Use Deep Translator (Stable & Compatible)
        # source='auto' automatically detects that input is English
        translator = GoogleTranslator(source='auto', target=target_language)
        result = translator.translate(text)
        return result
    
    except Exception as e:
        logger.warning(f"Deep-translator failed: {e}. Trying LLM fallback...")
        return translate_with_llm(text, target_language)

def translate_with_llm(text: str, target_language: str):
    """
    Translate using LLM as fallback if standard translation API fails
    """
    # Avoid circular import issues by importing inside function
    try:
        from .llm_provider import query_llm
        
        lang_name = SUPPORTED_LANGUAGES.get(target_language, "Hindi")
        
        prompt = f"""
        Translate the following agricultural advice to {lang_name}.
        Keep technical terms accurate but simple for a farmer.
        Do not add any extra conversational text, just the translation.

        Original text: "{text}"

        Translation:
        """
        
        result = query_llm(prompt, system_prompt="You are an expert translator for agricultural content.")
        
        # Handle different return types from your LLM provider
        if isinstance(result, dict) and result.get("success"):
            return result.get("text", text) # Return text key or original
        elif isinstance(result, str):
            return result
        else:
            return text
            
    except Exception as e:
        logger.error(f"LLM translation also failed: {e}")
        return text # Return original English text if everything fails

def get_supported_languages():
    """Get list of supported languages"""
    return SUPPORTED_LANGUAGES





# #!/usr/bin/env python3
# """
# Multi-language translation support
# Translates responses to Hindi and other Indian languages
# """

# from ..config import get_settings
# from ..utils.logger import Logger

# logger = Logger(__name__)
# settings = get_settings()

# # Language codes
# SUPPORTED_LANGUAGES = {
#     "en": "English",
#     "hi": "Hindi (हिंदी)",
#     "ta": "Tamil (தமிழ்)",
#     "te": "Telugu (తెలుగు)",
#     "mr": "Marathi (मराठी)",
#     "bn": "Bengali (বাংলা)",
#     "kn": "Kannada (ಕನ್ನಡ)",
#     "ml": "Malayalam (മലയാളം)"
# }

# # Common farming terms dictionary
# FARMING_TERMS = {
#     "en": {
#         "disease": "Disease",
#         "treatment": "Treatment",
#         "prevention": "Prevention",
#         "confidence": "Confidence",
#         "apply": "Apply",
#         "spray": "Spray",
#         "remove": "Remove",
#         "plant": "Plant",
#         "leaf": "Leaf",
#         "fungicide": "Fungicide",
#         "pesticide": "Pesticide"
#     },
#     "hi": {
#         "disease": "रोग",
#         "treatment": "उपचार",
#         "prevention": "रोकथाम",
#         "confidence": "विश्वास स्तर",
#         "apply": "लगाएं",
#         "spray": "स्प्रे करें",
#         "remove": "हटाएं",
#         "plant": "पौधा",
#         "leaf": "पत्ता",
#         "fungicide": "फफूंदनाशक",
#         "pesticide": "कीटनाशक"
#     }
# }

# def translate_response(text: str, target_language: str = "en"):
#     """
#     Translate response to target language
    
#     Args:
#         text: English text to translate
#         target_language: Target language code (en, hi, ta, etc.)
    
#     Returns:
#         Translated text
#     """
    
#     if target_language == "en":
#         return text
    
#     try:
#         # Option 1: Use Google Translate API (Free tier available)
#         from googletrans import Translator
#         translator = Translator()
#         result = translator.translate(text, dest=target_language)
#         return result.text
    
#     except ImportError:
#         logger.warning("googletrans not installed, using LLM translation")
#         return translate_with_llm(text, target_language)
    
#     except Exception as e:
#         logger.error(f"Translation error: {e}")
#         return text  # Return original if translation fails

# def translate_with_llm(text: str, target_language: str):
#     """
#     Translate using LLM as fallback
#     """
#     from .llm_provider import query_llm
    
#     lang_name = SUPPORTED_LANGUAGES.get(target_language, "Hindi")
    
#     prompt = f"""
# Translate the following agricultural advice to {lang_name}.
# Keep technical terms accurate and farmer-friendly.

# Original text:
# {text}

# Translation:
# """
    
#     try:
#         result = query_llm(prompt, system_prompt="You are a translator specializing in agricultural terminology.")
#         if result.get("success"):
#             return result["text"]
#         else:
#             return text
#     except Exception as e:
#         logger.error(f"LLM translation failed: {e}")
#         return text

# def get_supported_languages():
#     """Get list of supported languages"""
#     return SUPPORTED_LANGUAGES
