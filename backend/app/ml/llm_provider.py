import openai
import requests
import json
from ..config import get_settings
from ..utils.logger import Logger

settings = get_settings()
logger = Logger(__name__)

class LLMProvider:
    """
    Multi-provider LLM wrapper with automatic fallback
    Primary: OpenAI
    Fallback 1: AIPipe
    Fallback 2: OpenRouter
    Fallback 3: DeepSeek
    Fallback 4: Professional template
    """
    
    def __init__(self):
        self.openai_key = settings.OPENAI_API_KEY
        self.aipipe_key = settings.AIPIPE_API_KEY
        self.openrouter_key = settings.OPENROUTER_API_KEY
        self.deepseek_key = settings.DEEPSEEK_API_KEY
    
    def query(self, prompt: str, system_prompt: str = None) -> dict:
        """Query LLM with automatic fallback chain"""
        
        try:
            # Try OpenAI first (most reliable)
            logger.info("Trying OpenAI API...")
            return self._query_openai(prompt, system_prompt)
        except Exception as e:
            logger.warning(f"OpenAI failed: {str(e)}")
            pass
        
        try:
            # Fallback 1: AIPipe (you have $5!)
            logger.info("Trying AIPipe API...")
            return self._query_aipipe(prompt, system_prompt)
        except Exception as e:
            logger.warning(f"AIPipe failed: {str(e)}")
            pass
        
        try:
            # Fallback 2: OpenRouter
            logger.info("Trying OpenRouter API...")
            return self._query_openrouter(prompt, system_prompt)
        except Exception as e:
            logger.warning(f"OpenRouter failed: {str(e)}")
            pass
        
        try:
            # Fallback 3: DeepSeek (FREE!)
            logger.info("Trying DeepSeek API...")
            return self._query_deepseek(prompt, system_prompt)
        except Exception as e:
            logger.warning(f"DeepSeek failed: {str(e)}")
            pass
        
        # Final fallback: Professional template
        logger.warning("All APIs failed - using professional fallback")
        return self._generic_fallback(prompt)
    
    def _query_openai(self, prompt: str, system_prompt: str = None) -> dict:
        """Query OpenAI API"""
        openai.api_key = self.openai_key
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=settings.OPENAI_TEMPERATURE
        )
        
        return {
            "success": True,
            "provider": "OpenAI",
            "text": response.choices[0].message.content
        }
    
    def _query_aipipe(self, prompt: str, system_prompt: str = None) -> dict:
        """Query AIPipe API (your $5 credit!)"""
        headers = {
            "Authorization": f"Bearer {self.aipipe_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": settings.AIPIPE_MODEL,
            "messages": messages,
            "max_tokens": settings.OPENAI_MAX_TOKENS,
            "temperature": settings.OPENAI_TEMPERATURE
        }
        
        response = requests.post(
            settings.AIPIPE_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"AIPipe error: {response.text}")
        
        data = response.json()
        
        return {
            "success": True,
            "provider": "AIPipe",
            "text": data["choices"][0]["message"]["content"]
        }
    
    def _query_openrouter(self, prompt: str, system_prompt: str = None) -> dict:
        """Query OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": messages,
            "max_tokens": settings.OPENAI_MAX_TOKENS,
            "temperature": settings.OPENAI_TEMPERATURE
        }
        
        response = requests.post(
            settings.OPENROUTER_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter error: {response.text}")
        
        data = response.json()
        
        return {
            "success": True,
            "provider": "OpenRouter",
            "text": data["choices"][0]["message"]["content"]
        }
    
    def _query_deepseek(self, prompt: str, system_prompt: str = None) -> dict:
        """Query DeepSeek API (FREE!)"""
        headers = {
            "Authorization": f"Bearer {self.deepseek_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        response = requests.post(
            settings.DEEPSEEK_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"DeepSeek error: {response.text}")
        
        data = response.json()
        
        return {
            "success": True,
            "provider": "DeepSeek",
            "text": data["choices"][0]["message"]["content"]
        }
    
    def _generic_fallback(self, prompt: str) -> dict:
        """Professional fallback (only if all APIs fail)"""
        logger.warning("Using professional fallback response")
        
        fallback_response = """
Based on visual analysis of your crop:

**Diagnosis:** Unable to identify specific disease (AI services currently unavailable)

**Recommended Actions:**
1. Contact your local agricultural extension office
2. Document symptoms with clear photos
3. Avoid spreading potential pathogens
4. Implement quarantine measures

**Temporary Prevention:**
- Improve air circulation around plants
- Reduce overhead watering
- Maintain crop hygiene
- Monitor nearby plants
- Increase spacing

This response was generated offline. Please try again when services are available.
        """
        
        return {
            "success": True,
            "provider": "FALLBACK",
            "text": fallback_response,
            "note": "All APIs unavailable - using professional template"
        }

# Singleton
llm_provider = LLMProvider()

def get_llm_response(prompt: str, system_prompt: str = None) -> dict:
    """Easy function to call from anywhere"""
    return llm_provider.query(prompt, system_prompt)
