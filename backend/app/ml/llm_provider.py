"""
LLM Provider with fallback chain
Primary: OpenAI
Fallbacks: AIPipe, OpenRouter, DeepSeek
"""

import requests
from openai import OpenAI
from ..config import get_settings
from ..utils.logger import Logger

logger = Logger(__name__)
settings = get_settings()


class LLMProvider:
    """Multi-LLM provider with fallback chain"""

    def __init__(self):
        self.providers = {
            "openai": self._query_openai,
            "aipipe": self._query_aipipe,
            "openrouter": self._query_openrouter,
            "deepseek": self._query_deepseek,
        }

    def query(self, user_message: str, system_prompt: str = None):

        # Build messages structure
        messages = (
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]
            if system_prompt
            else [{"role": "user", "content": user_message}]
        )

        provider_chain = [
            settings.DEFAULT_LLM,  # openai by default
            "aipipe",
            "openrouter",
            "deepseek",
        ]

        for provider in provider_chain:
            logger.info(f"Trying {provider}...")
            try:
                result = self.providers[provider](messages)
                if result.get("success"):
                    logger.success(f"✓ {provider} responded")
                    return result
            except Exception as e:
                logger.warning(f"{provider} error: {e}")

        logger.error("❌ All LLM providers failed!")
        return {
            "text": "Unable to reach AI services right now.",
            "provider": "none",
            "success": False,
        }

    # ============================================================
    # OpenAI (NEW SDK)
    # ============================================================
    def _query_openai(self, messages):

        if not settings.OPENAI_API_KEY:
            return {"success": False, "error": "Missing OpenAI API key"}

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )

            return {
                "text": response.choices[0].message["content"],
                "provider": "openai",
                "tokens": response.usage.total_tokens,
                "success": True,
            }

        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================
    # AIPipe API
    # ============================================================
    def _query_aipipe(self, messages):

        if not settings.AIPIPE_API_KEY:
            return {"success": False}

        try:
            response = requests.post(
                settings.AIPIPE_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {settings.AIPIPE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.AIPIPE_MODEL,
                    "messages": messages,
                    "temperature": settings.LLM_TEMPERATURE,
                    "max_tokens": settings.LLM_MAX_TOKENS,
                },
                timeout=15,
            )

            if response.status_code != 200:
                return {"success": False}

            data = response.json()

            return {
                "text": data["choices"][0]["message"]["content"],
                "provider": "aipipe",
                "success": True,
                "tokens": data.get("usage", {}).get("total_tokens", 0),
            }

        except Exception as e:
            logger.error(f"AIPipe error: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================
    # OpenRouter API
    # ============================================================
    def _query_openrouter(self, messages):

        if not settings.OPENROUTER_API_KEY:
            return {"success": False}

        try:
            response = requests.post(
                settings.OPENROUTER_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": messages,
                    "temperature": settings.LLM_TEMPERATURE,
                    "max_tokens": settings.LLM_MAX_TOKENS,
                },
                timeout=15,
            )

            if response.status_code != 200:
                return {"success": False}

            data = response.json()

            return {
                "text": data["choices"][0]["message"]["content"],
                "provider": "openrouter",
                "success": True,
                "tokens": data.get("usage", {}).get("total_tokens", 0),
            }

        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================
    # DeepSeek (FREE)
    # ============================================================
    def _query_deepseek(self, messages):

        try:
            response = requests.post(
                settings.DEEPSEEK_ENDPOINT,
                headers={"Content-Type": "application/json"},
                json={
                    "model": settings.DEEPSEEK_MODEL,
                    "messages": messages,
                    "temperature": settings.LLM_TEMPERATURE,
                    "max_tokens": settings.LLM_MAX_TOKENS,
                },
                timeout=15,
            )

            if response.status_code != 200:
                return {"success": False}

            data = response.json()

            return {
                "text": data["choices"][0]["message"]["content"],
                "provider": "deepseek",
                "success": True,
                "tokens": data.get("usage", {}).get("total_tokens", 0),
            }

        except Exception as e:
            logger.error(f"DeepSeek error: {e}")
            return {"success": False, "error": str(e)}


llm_provider = LLMProvider()


def query_llm(user_message: str, system_prompt: str = None):
    return llm_provider.query(user_message, system_prompt)





# """
# LLM Provider with fallback chain
# Primary: OpenAI
# Fallbacks: AIPipe, OpenRouter, DeepSeek
# """

# import requests
# from openai import OpenAI
# from ..config import get_settings
# from ..utils.logger import Logger

# logger = Logger(__name__)
# settings = get_settings()


# class LLMProvider:
#     """Multi-LLM provider with fallback chain"""

#     def __init__(self):
#         self.providers = {
#             "openai": self._query_openai,
#             "aipipe": self._query_aipipe,
#             "openrouter": self._query_openrouter,
#             "deepseek": self._query_deepseek,
#         }

#     def query(self, user_message: str, system_prompt: str = None):

#         # Build message list
#         if system_prompt:
#             messages = [
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_message}
#             ]
#         else:
#             messages = [{"role": "user", "content": user_message}]

#         provider_chain = [
#             settings.DEFAULT_LLM,
#             "aipipe",
#             "openrouter",
#             "deepseek",
#         ]

#         for provider in provider_chain:
#             logger.info(f"Trying {provider}...")

#             try:
#                 result = self.providers[provider](messages)

#                 if result.get("success"):
#                     logger.success(f"✓ {provider} responded")
#                     return result

#             except Exception as e:
#                 logger.warning(f"{provider} error: {e}")

#         logger.error("❌ All LLM providers failed!")

#         return {
#             "text": "Unable to reach AI services right now.",
#             "provider": "none",
#             "success": False
#         }

#     # ============================================================
#     # OpenAI (NEW SDK)
#     # ============================================================
#     def _query_openai(self, messages):

#         if not settings.OPENAI_API_KEY:
#             return {"success": False, "error": "Missing OpenAI API key"}

#         try:
#             client = OpenAI(api_key=settings.OPENAI_API_KEY)

#             response = client.chat.completions.create(
#                 model=settings.OPENAI_MODEL,
#                 messages=messages,
#                 temperature=settings.OPENAI_TEMPERATURE,
#                 max_tokens=settings.OPENAI_MAX_TOKENS,
#             )

#             return {
#                 "text": response.choices[0].message["content"],
#                 "tokens": response.usage.total_tokens,
#                 "provider": "openai",
#                 "success": True
#             }

#         except Exception as e:
#             logger.error(f"OpenAI error: {e}")
#             return {"success": False, "error": str(e)}

#     # ============================================================
#     # AIPipe
#     # ============================================================
#     def _query_aipipe(self, messages):

#         if not settings.AIPIPE_API_KEY:
#             return {"success": False}

#         try:
#             response = requests.post(
#                 settings.AIPIPE_ENDPOINT,
#                 headers={
#                     "Authorization": f"Bearer {settings.AIPIPE_API_KEY}",
#                     "Content-Type": "application/json"
#                 },
#                 json={
#                     "model": settings.AIPIPE_MODEL,
#                     "messages": messages,
#                     "temperature": settings.OPENAI_TEMPERATURE,
#                     "max_tokens": settings.OPENAI_MAX_TOKENS
#                 },
#                 timeout=20
#             )

#             if response.status_code != 200:
#                 return {"success": False}

#             data = response.json()

#             return {
#                 "text": data["choices"][0]["message"]["content"],
#                 "provider": "aipipe",
#                 "success": True,
#                 "tokens": data.get("usage", {}).get("total_tokens", 0)
#             }

#         except Exception as e:
#             logger.error(f"AIPipe error: {e}")
#             return {"success": False, "error": str(e)}

#     # ============================================================
#     # OpenRouter
#     # ============================================================
#     def _query_openrouter(self, messages):

#         if not settings.OPENROUTER_API_KEY:
#             return {"success": False}

#         try:
#             response = requests.post(
#                 settings.OPENROUTER_ENDPOINT,
#                 headers={
#                     "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
#                     "Content-Type": "application/json",
#                 },
#                 json={
#                     "model": settings.OPENROUTER_MODEL,
#                     "messages": messages,
#                     "temperature": settings.OPENAI_TEMPERATURE,
#                     "max_tokens": settings.OPENAI_MAX_TOKENS,
#                 },
#                 timeout=20
#             )

#             if response.status_code != 200:
#                 return {"success": False}

#             data = response.json()

#             return {
#                 "text": data["choices"][0]["message"]["content"],
#                 "provider": "openrouter",
#                 "success": True,
#                 "tokens": data.get("usage", {}).get("total_tokens", 0),
#             }

#         except Exception as e:
#             logger.error(f"OpenRouter error: {e}")
#             return {"success": False, "error": str(e)}

#     # ============================================================
#     # DeepSeek (FREE)
#     # ============================================================
#     def _query_deepseek(self, messages):

#         try:
#             payload = {
#                 "model": settings.DEEPSEEK_MODEL,
#                 "messages": messages,
#                 "temperature": settings.OPENAI_TEMPERATURE,
#                 "max_tokens": settings.OPENAI_MAX_TOKENS,
#             }

#             response = requests.post(
#                 settings.DEEPSEEK_ENDPOINT,
#                 json=payload,
#                 headers={"Content-Type": "application/json"},
#                 timeout=20
#             )

#             if response.status_code != 200:
#                 return {"success": False}

#             data = response.json()

#             return {
#                 "text": data["choices"][0]["message"]["content"],
#                 "provider": "deepseek",
#                 "tokens": data.get("usage", {}).get("total_tokens", 0),
#                 "success": True
#             }

#         except Exception as e:
#             logger.error(f"DeepSeek error: {e}")
#             return {"success": False, "error": str(e)}


# # Singleton
# llm_provider = LLMProvider()


# def query_llm(user_message: str, system_prompt: str = None):
#     return llm_provider.query(user_message, system_prompt)






# """
# LLM Provider with fallback chain
# Primary: OpenAI
# Fallbacks: AIPipe, OpenRouter, DeepSeek
# """

# import openai
# import requests
# from ..config import get_settings
# from ..utils.logger import Logger

# logger = Logger(__name__)
# settings = get_settings()

# class LLMProvider:
#     """Multi-LLM provider with fallback chain"""
    
#     def __init__(self):
#         self.providers = {
#             "openai": self._query_openai,
#             "aipipe": self._query_aipipe,
#             "openrouter": self._query_openrouter,
#             "deepseek": self._query_deepseek
#         }
    
#     def query(self, user_message: str, system_prompt: str = None):
#         """
#         Query LLM with fallback chain
        
#         Returns: {
#             "text": "response",
#             "provider": "openai",
#             "tokens": 150,
#             "success": True
#         }
#         """
        
#         # Build full prompt
#         if system_prompt:
#             messages = [
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_message}
#             ]
#         else:
#             messages = [{"role": "user", "content": user_message}]
        
#         # Try providers in order
#         providers_to_try = [
#             settings.DEFAULT_LLM,
#             "aipipe",
#             "openrouter",
#             "deepseek"
#         ]
        
#         for provider in providers_to_try:
#             try:
#                 logger.info(f"Trying {provider}...")
#                 result = self.providers[provider](messages)
                
#                 if result.get("success"):
#                     logger.success(f"✓ {provider} responded")
#                     return result
#                 else:
#                     logger.warning(f"✗ {provider} failed, trying next...")
            
#             except Exception as e:
#                 logger.warning(f"✗ {provider} error: {str(e)}, trying next...")
#                 continue
        
#         # All failed
#         logger.error("All LLM providers failed!")
#         return {
#             "text": "Unable to reach AI services. Please try again later.",
#             "provider": "error",
#             "success": False
#         }
    
#     def _query_openai(self, messages):
#         """Query OpenAI GPT"""
#         try:
#             if not settings.OPENAI_API_KEY:
#                 return {"success": False, "error": "No API key"}
            
#             client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
#             response = client.chat.completions.create(
#                 model=settings.LLM_MODEL,
#                 messages=messages,
#                 temperature=settings.LLM_TEMPERATURE,
#                 max_tokens=settings.LLM_MAX_TOKENS
#             )
            
#             return {
#                 "text": response.choices[0].message.content,
#                 "provider": "openai",
#                 "tokens": response.usage.total_tokens,
#                 "success": True
#             }
        
#         except Exception as e:
#             logger.error(f"OpenAI error: {e}")
#             return {"success": False, "error": str(e)}
    
#     def _query_aipipe(self, messages):
#         """Query AIPipe API"""
#         try:
#             if not settings.AIPIPE_API_KEY:
#                 return {"success": False, "error": "No API key"}
            
#             response = requests.post(
#                 "https://api.aipipe.io/v1/chat/completions",
#                 headers={
#                     "Authorization": f"Bearer {settings.AIPIPE_API_KEY}",
#                     "Content-Type": "application/json"
#                 },
#                 json={
#                     "model": "gpt-3.5-turbo",
#                     "messages": messages,
#                     "temperature": settings.LLM_TEMPERATURE,
#                     "max_tokens": settings.LLM_MAX_TOKENS
#                 },
#                 timeout=30
#             )
            
#             if response.status_code == 200:
#                 data = response.json()
#                 return {
#                     "text": data['choices'][0]['message']['content'],
#                     "provider": "aipipe",
#                     "tokens": data.get('usage', {}).get('total_tokens', 0),
#                     "success": True
#                 }
#             else:
#                 return {"success": False, "error": response.text}
        
#         except Exception as e:
#             logger.error(f"AIPipe error: {e}")
#             return {"success": False, "error": str(e)}
    
#     def _query_openrouter(self, messages):
#         """Query OpenRouter"""
#         try:
#             if not settings.OPENROUTER_API_KEY:
#                 return {"success": False, "error": "No API key"}
            
#             response = requests.post(
#                 "https://openrouter.ai/api/v1/chat/completions",
#                 headers={
#                     "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
#                     "Content-Type": "application/json"
#                 },
#                 json={
#                     "model": "openai/gpt-3.5-turbo",
#                     "messages": messages,
#                     "temperature": settings.LLM_TEMPERATURE,
#                     "max_tokens": settings.LLM_MAX_TOKENS
#                 },
#                 timeout=30
#             )
            
#             if response.status_code == 200:
#                 data = response.json()
#                 return {
#                     "text": data['choices'][0]['message']['content'],
#                     "provider": "openrouter",
#                     "tokens": data.get('usage', {}).get('total_tokens', 0),
#                     "success": True
#                 }
#             else:
#                 return {"success": False, "error": response.text}
        
#         except Exception as e:
#             logger.error(f"OpenRouter error: {e}")
#             return {"success": False, "error": str(e)}
    
#     def _query_deepseek(self, messages):
#         """Query DeepSeek (FREE!)"""
#         try:
#             response = requests.post(
#                 "https://api.deepseek.com/chat/completions",
#                 headers={"Content-Type": "application/json"},
#                 json={
#                     "model": "deepseek-chat",
#                     "messages": messages,
#                     "temperature": settings.LLM_TEMPERATURE,
#                     "max_tokens": settings.LLM_MAX_TOKENS
#                 },
#                 timeout=30
#             )
            
#             if response.status_code == 200:
#                 data = response.json()
#                 return {
#                     "text": data['choices'][0]['message']['content'],
#                     "provider": "deepseek",
#                     "tokens": 0,
#                     "success": True
#                 }
#             else:
#                 return {"success": False, "error": response.text}
        
#         except Exception as e:
#             logger.error(f"DeepSeek error: {e}")
#             return {"success": False, "error": str(e)}

# # Singleton
# llm_provider = LLMProvider()

# def query_llm(user_message: str, system_prompt: str = None):
#     """Easy function to use LLM"""
#     return llm_provider.query(user_message, system_prompt)





# def analyze_uncertain_prediction(top5_predictions: list, confidence: float):
#     """
#     Analyze uncertain predictions using AI
    
#     Args:
#         top5_predictions: List of top 5 predictions from model
#         confidence: Top confidence score
    
#     Returns: {
#         "text": "AI analysis...",
#         "suggestions": [...],
#         "success": True
#     }
#     """
    
#     # Build prompt for AI
#     predictions_text = "\n".join([
#         f"{i+1}. {p['disease']} ({p['probability']*100:.1f}%)"
#         for i, p in enumerate(top5_predictions)
#     ])
    
#     system_prompt = f"""
# You are an agricultural disease expert analyzing uncertain model predictions.

# MODEL'S TOP PREDICTIONS:
# {predictions_text}

# Top confidence: {confidence*100:.1f}%

# The model is uncertain (confidence below 60%). This could mean:
# 1. Image quality is poor (blurry, bad lighting, wrong angle)
# 2. Symptoms are in early/late stage and unclear
# 3. Multiple diseases look similar
# 4. Disease is not in training data

# Your task:
# 1. Analyze the top predictions and find patterns
# 2. Identify if predictions are from same crop or different crops
# 3. If multiple crops detected, explain image might be ambiguous
# 4. Give practical advice to farmer on what to do next
# 5. Suggest how to take better photos if needed

# Be specific, practical, and farmer-friendly.
# """
    
#     user_message = f"""
# The model detected these diseases but with low confidence. What should the farmer do?

# Top predictions:
# {predictions_text}

# Please provide:
# 1. Analysis of why model is uncertain
# 2. Practical next steps for the farmer
# 3. How to improve photo quality
# 4. Whether to consult an expert
# """
    
#     try:
#         response = llm_provider.query(user_message, system_prompt)
        
#         if response.get("success"):
#             return {
#                 "text": response["text"],
#                 "provider": response["provider"],
#                 "tokens": response.get("tokens", 0),
#                 "success": True
#             }
#         else:
#             # Fallback if LLM fails
#             return {
#                 "text": _generate_fallback_uncertain_advice(top5_predictions, confidence),
#                 "provider": "fallback",
#                 "success": True
#             }
    
#     except Exception as e:
#         logger.error(f"AI analysis error: {str(e)}")
#         return {
#             "text": _generate_fallback_uncertain_advice(top5_predictions, confidence),
#             "provider": "fallback",
#             "success": True
#         }

# def _generate_fallback_uncertain_advice(top5_predictions: list, confidence: float):
#     """Generate fallback advice when LLM fails"""
    
#     # Extract crop types from predictions
#     crops = set()
#     for pred in top5_predictions:
#         disease_name = pred['disease']
#         if '___' in disease_name:
#             crop = disease_name.split('___')[0]
#             crops.add(crop)
    
#     advice = f"""
# ⚠️  The model detected your image with {confidence*100:.1f}% confidence, which is below our 60% threshold.

# TOP PREDICTIONS:
# """
    
#     for i, pred in enumerate(top5_predictions[:3]):
#         advice += f"\n{i+1}. {pred['disease']} ({pred['probability']*100:.1f}%)"
    
#     if len(crops) > 1:
#         advice += f"""

# 🔍 ISSUE DETECTED: Multiple crop types detected ({', '.join(crops)}).
# This suggests the image might be unclear or showing multiple plants.
# """
    
#     advice += """

# 📸 RECOMMENDED ACTIONS:

# 1. RETAKE PHOTO:
#    - Use good lighting (natural daylight preferred)
#    - Focus clearly on the diseased leaf
#    - Take photo from 6-12 inches away
#    - Ensure affected area fills most of the frame
#    - Avoid shadows and blur

# 2. MULTIPLE ANGLES:
#    - Take 2-3 photos from different angles
#    - Include close-up of diseased spots
#    - Show full leaf for context

# 3. EXPERT CONSULTATION:
#    - Share photos with local agricultural extension officer
#    - Visit nearest Krishi Vigyan Kendra (KVK)
#    - Compare symptoms with online disease databases

# 4. MONITOR SYMPTOMS:
#    - Take photos daily to track progression
#    - Note any new symptoms or spread pattern
#    - This helps experts identify the disease

# The model's top guesses are shown above. Compare these with online images to narrow down possibilities.
# """
    
#     return advice





# import openai
# import requests
# import json
# from ..config import get_settings
# from ..utils.logger import Logger

# settings = get_settings()
# logger = Logger(__name__)

# class LLMProvider:
#     """
#     Multi-provider LLM wrapper with automatic fallback
#     Primary: OpenAI
#     Fallback 1: AIPipe
#     Fallback 2: OpenRouter
#     Fallback 3: DeepSeek
#     Fallback 4: Professional template
#     """
    
#     def __init__(self):
#         self.openai_key = settings.OPENAI_API_KEY
#         self.aipipe_key = settings.AIPIPE_API_KEY
#         self.openrouter_key = settings.OPENROUTER_API_KEY
#         self.deepseek_key = settings.DEEPSEEK_API_KEY
    
#     def query(self, prompt: str, system_prompt: str = None) -> dict:
#         """Query LLM with automatic fallback chain"""
        
#         try:
#             # Try OpenAI first (most reliable)
#             logger.info("Trying OpenAI API...")
#             return self._query_openai(prompt, system_prompt)
#         except Exception as e:
#             logger.warning(f"OpenAI failed: {str(e)}")
#             pass
        
#         try:
#             # Fallback 1: AIPipe (you have $5!)
#             logger.info("Trying AIPipe API...")
#             return self._query_aipipe(prompt, system_prompt)
#         except Exception as e:
#             logger.warning(f"AIPipe failed: {str(e)}")
#             pass
        
#         try:
#             # Fallback 2: OpenRouter
#             logger.info("Trying OpenRouter API...")
#             return self._query_openrouter(prompt, system_prompt)
#         except Exception as e:
#             logger.warning(f"OpenRouter failed: {str(e)}")
#             pass
        
#         try:
#             # Fallback 3: DeepSeek (FREE!)
#             logger.info("Trying DeepSeek API...")
#             return self._query_deepseek(prompt, system_prompt)
#         except Exception as e:
#             logger.warning(f"DeepSeek failed: {str(e)}")
#             pass
        
#         # Final fallback: Professional template
#         logger.warning("All APIs failed - using professional fallback")
#         return self._generic_fallback(prompt)
    
#     def _query_openai(self, prompt: str, system_prompt: str = None) -> dict:
#         """Query OpenAI API"""
#         openai.api_key = self.openai_key
        
#         messages = []
#         if system_prompt:
#             messages.append({"role": "system", "content": system_prompt})
#         messages.append({"role": "user", "content": prompt})
        
#         response = openai.ChatCompletion.create(
#             model=settings.OPENAI_MODEL,
#             messages=messages,
#             max_tokens=settings.OPENAI_MAX_TOKENS,
#             temperature=settings.OPENAI_TEMPERATURE
#         )
        
#         return {
#             "success": True,
#             "provider": "OpenAI",
#             "text": response.choices[0].message.content
#         }
    
#     def _query_aipipe(self, prompt: str, system_prompt: str = None) -> dict:
#         """Query AIPipe API (your $5 credit!)"""
#         headers = {
#             "Authorization": f"Bearer {self.aipipe_key}",
#             "Content-Type": "application/json"
#         }
        
#         messages = []
#         if system_prompt:
#             messages.append({"role": "system", "content": system_prompt})
#         messages.append({"role": "user", "content": prompt})
        
#         payload = {
#             "model": settings.AIPIPE_MODEL,
#             "messages": messages,
#             "max_tokens": settings.OPENAI_MAX_TOKENS,
#             "temperature": settings.OPENAI_TEMPERATURE
#         }
        
#         response = requests.post(
#             settings.AIPIPE_ENDPOINT,
#             headers=headers,
#             json=payload,
#             timeout=30
#         )
        
#         if response.status_code != 200:
#             raise Exception(f"AIPipe error: {response.text}")
        
#         data = response.json()
        
#         return {
#             "success": True,
#             "provider": "AIPipe",
#             "text": data["choices"][0]["message"]["content"]
#         }
    
#     def _query_openrouter(self, prompt: str, system_prompt: str = None) -> dict:
#         """Query OpenRouter API"""
#         headers = {
#             "Authorization": f"Bearer {self.openrouter_key}",
#             "Content-Type": "application/json"
#         }
        
#         messages = []
#         if system_prompt:
#             messages.append({"role": "system", "content": system_prompt})
#         messages.append({"role": "user", "content": prompt})
        
#         payload = {
#             "model": settings.OPENROUTER_MODEL,
#             "messages": messages,
#             "max_tokens": settings.OPENAI_MAX_TOKENS,
#             "temperature": settings.OPENAI_TEMPERATURE
#         }
        
#         response = requests.post(
#             settings.OPENROUTER_ENDPOINT,
#             headers=headers,
#             json=payload,
#             timeout=30
#         )
        
#         if response.status_code != 200:
#             raise Exception(f"OpenRouter error: {response.text}")
        
#         data = response.json()
        
#         return {
#             "success": True,
#             "provider": "OpenRouter",
#             "text": data["choices"][0]["message"]["content"]
#         }
    
#     def _query_deepseek(self, prompt: str, system_prompt: str = None) -> dict:
#         """Query DeepSeek API (FREE!)"""
#         headers = {
#             "Authorization": f"Bearer {self.deepseek_key}",
#             "Content-Type": "application/json"
#         }
        
#         messages = []
#         if system_prompt:
#             messages.append({"role": "system", "content": system_prompt})
#         messages.append({"role": "user", "content": prompt})
        
#         payload = {
#             "model": "deepseek-chat",
#             "messages": messages,
#             "max_tokens": 300,
#             "temperature": 0.7
#         }
        
#         response = requests.post(
#             settings.DEEPSEEK_ENDPOINT,
#             headers=headers,
#             json=payload,
#             timeout=30
#         )
        
#         if response.status_code != 200:
#             raise Exception(f"DeepSeek error: {response.text}")
        
#         data = response.json()
        
#         return {
#             "success": True,
#             "provider": "DeepSeek",
#             "text": data["choices"][0]["message"]["content"]
#         }
    
#     def _generic_fallback(self, prompt: str) -> dict:
#         """Professional fallback (only if all APIs fail)"""
#         logger.warning("Using professional fallback response")
        
#         fallback_response = """
# Based on visual analysis of your crop:

# **Diagnosis:** Unable to identify specific disease (AI services currently unavailable)

# **Recommended Actions:**
# 1. Contact your local agricultural extension office
# 2. Document symptoms with clear photos
# 3. Avoid spreading potential pathogens
# 4. Implement quarantine measures

# **Temporary Prevention:**
# - Improve air circulation around plants
# - Reduce overhead watering
# - Maintain crop hygiene
# - Monitor nearby plants
# - Increase spacing

# This response was generated offline. Please try again when services are available.
#         """
        
#         return {
#             "success": True,
#             "provider": "FALLBACK",
#             "text": fallback_response,
#             "note": "All APIs unavailable - using professional template"
#         }

# # Singleton
# llm_provider = LLMProvider()

# def get_llm_response(prompt: str, system_prompt: str = None) -> dict:
#     """Easy function to call from anywhere"""
#     return llm_provider.query(prompt, system_prompt)
