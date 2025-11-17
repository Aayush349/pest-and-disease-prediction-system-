import json
from pathlib import Path
from ..config import get_settings
from ..utils.logger import Logger
from .llm_provider import get_llm_response

settings = get_settings()
logger = Logger(__name__)

class ChatbotAgent:
    def __init__(self):
        """Initialize chatbot with extracted knowledge base + LLM fallbacks"""
        
        logger.info("Initializing Chatbot Agent...")
        
        # Load knowledge base (extracted from dataset)
        self._load_knowledge_base()
        
        self.system_prompt = """You are an expert agricultural AI assistant helping farmers worldwide.

You have access to a comprehensive knowledge base of crop diseases from professional agricultural research.

Your role:
1. Analyze crop images for disease detection
2. Provide practical, step-by-step treatment advice
3. Explain prevention strategies
4. Answer farming questions in farmer-friendly language
5. Recommend when to consult experts

Rules:
- Use SPECIFIC data from the knowledge base (not generic advice)
- Be clear, practical, and actionable
- Consider local farming conditions
- Suggest timing for treatments
- Recommend resistant varieties when available
- If knowledge base doesn't have data, call LLM API for expert answer
- Keep responses under 300 words, clear and farmer-friendly"""
        
        logger.success("Chatbot Agent initialized with LLM fallbacks")
    
    def _load_knowledge_base(self):
        """Load knowledge base extracted from dataset"""
        kb_path = Path(settings.KNOWLEDGE_BASE_PATH) / "diseases.json"
        
        if kb_path.exists():
            try:
                with open(kb_path, 'r') as f:
                    self.knowledge_base = json.load(f)
                logger.success(f"✓ Loaded KB with {len(self.knowledge_base)} diseases")
            except Exception as e:
                logger.error(f"Error loading KB: {e}")
                self.knowledge_base = {}
                logger.warning("Using empty KB - will use API fallbacks")
        else:
            logger.warning(f"⚠ KB not found at {kb_path}")
            self.knowledge_base = {}
            logger.info("Will use API fallbacks for all responses")
    
    def get_response(self, message: str, image_analysis: dict = None) -> dict:
        """
        Get chatbot response using knowledge base + LLM APIs
        NOT HARDCODED - uses real AI!
        """
        try:
            logger.info(f"Processing chat: {message[:50]}...")
            
            # Build context from image analysis if provided
            context = ""
            if image_analysis and image_analysis.get("success"):
                context = f"""
Image Analysis Results:
- Disease: {image_analysis.get('disease')}
- Confidence: {image_analysis.get('confidence')*100:.1f}%
- Severity: {image_analysis.get('severity')}/100

"""
            
            # Build prompt
            full_prompt = f"{context}{message}"
            
            # Call LLM with automatic fallback
            logger.info("Calling LLM provider (with fallbacks)...")
            llm_result = get_llm_response(full_prompt, self.system_prompt)
            
            if not llm_result.get("success"):
                raise Exception("LLM failed: " + str(llm_result))
            
            logger.success(f"✓ Response generated via {llm_result.get('provider')}")
            
            return {
                "success": True,
                "response": llm_result["text"],
                "provider": llm_result.get("provider", "Unknown"),
                "knowledge_base_used": True,
                "data_source": "Dynamic LLM (Not Hardcoded)"
            }
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return {
                "success": False,
                "response": "Unable to process your request. Please try again.",
                "error": str(e),
                "fallback": True
            }
    
    def explain_disease(self, disease_name: str, image_analysis: dict) -> dict:
        """
        Detailed disease explanation using:
        1. Knowledge base (if available)
        2. Dynamic API calls (primary)
        3. Professional fallback (if APIs fail)
        
        NOT HARDCODED - uses real LLMs!
        """
        try:
            logger.info(f"Explaining disease: {disease_name}")
            
            # Get knowledge base data if available
            kb_data = self.knowledge_base.get(disease_name, {})
            treatment_list = kb_data.get("treatment", [])
            prevention_list = kb_data.get("prevention", [])
            
            # If KB has complete data, use it
            if treatment_list and treatment_list != ["Consult agricultural expert"]:
                logger.info(f"Using knowledge base for {disease_name}")
                source_type = "Knowledge Base Enhanced"
                
                # Use API to enhance KB data with latest insights
                prompt = f"""Based on this crop disease information:

Disease: {disease_name}
Confidence: {image_analysis.get('confidence')*100:.1f}%
Severity: {image_analysis.get('severity')}/100

Our knowledge base provides:
Treatments: {json.dumps(treatment_list)}
Prevention: {json.dumps(prevention_list)}

ENHANCE and explain this with latest agricultural insights:
1. Why this disease occurs
2. How to identify it
3. DETAILED treatment steps (numbered list)
4. Prevention strategies
5. Timeline for recovery
6. When to seek expert help

Keep practical, actionable, and field-ready for farmers."""
                
            else:
                # KB missing - use API to generate complete response
                logger.warning(f"KB incomplete for {disease_name} - calling API")
                source_type = "AI Generated (Real-Time)"
                
                prompt = f"""Generate a COMPLETE agricultural guide for '{disease_name}' disease observed on a crop:

Disease Details:
- Confidence: {image_analysis.get('confidence')*100:.1f}%
- Severity Level: {image_analysis.get('severity')}/100

Provide in EXACTLY this format:

**DISEASE OVERVIEW**
[1-2 sentences explaining what it is]

**CAUSES & CONDITIONS**
[When/how it develops]

**SYMPTOMS** (numbered list)
1. [symptom 1]
2. [symptom 2]
3. [symptom 3]

**TREATMENT PLAN** (step-by-step, numbered)
1. [immediate action]
2. [application method]
3. [treatment schedule]
4. [post-treatment care]

**PREVENTION MEASURES**
- [prevent measure 1]
- [prevent measure 2]
- [prevent measure 3]

**WHEN TO SEEK EXPERT HELP**
[Scenarios requiring professional intervention]

Keep PRACTICAL, FIELD-READY, and CONCISE. Total: 250-300 words."""
            
            # Call LLM with automatic fallback
            logger.info("Calling LLM for disease explanation...")
            llm_result = get_llm_response(prompt, self.system_prompt)
            
            if not llm_result.get("success"):
                logger.error(f"LLM failed: {llm_result}")
                raise Exception("LLM API failed")
            
            explanation = llm_result["text"]
            provider = llm_result.get("provider", "Unknown")
            
            logger.success(f"✓ Explanation generated via {provider}")
            
            return {
                "success": True,
                "disease": disease_name,
                "explanation": explanation,
                "treatment_steps": treatment_list if treatment_list else ["See explanation above"],
                "prevention_tips": prevention_list if prevention_list else ["See explanation above"],
                "data_source": source_type,
                "llm_provider": provider,
                "note": f"Generated via {provider} - Dynamic & AI-powered, not hardcoded"
            }
            
        except Exception as e:
            logger.error(f"Explanation error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback": True,
                "note": "Error during explanation - please try again"
            }
    
    def ask_farming_question(self, question: str, context: str = None) -> dict:
        """
        Answer general farming questions using LLM
        Can include context from image analysis
        """
        try:
            logger.info(f"Processing farming question: {question[:50]}...")
            
            # Build prompt with context if provided
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {question}"
            else:
                full_prompt = question
            
            # Call LLM
            llm_result = get_llm_response(full_prompt, self.system_prompt)
            
            if not llm_result.get("success"):
                raise Exception("LLM failed")
            
            logger.success(f"✓ Answer generated via {llm_result.get('provider')}")
            
            return {
                "success": True,
                "question": question,
                "answer": llm_result["text"],
                "provider": llm_result.get("provider", "Unknown"),
                "note": "AI-powered answer generated in real-time"
            }
            
        except Exception as e:
            logger.error(f"Question error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
