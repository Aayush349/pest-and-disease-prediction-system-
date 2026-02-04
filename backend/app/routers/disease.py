#!/usr/bin/env python3
"""
API Router for Disease Prediction
WEAPON 1: Hybrid Intelligence Engine

PRIMARY:
- Dual-Core YOLO Engine (Fast, Offline-first)
- Gemini Vision (Online fallback, Crop-aware, High accuracy)

FALLBACK:
- YOLOv8 + Knowledge Base (Offline / Fail-safe)

FEATURES:
- Dynamic Advisory Switch (Fresh API → JSON fallback)
- Crop filtering with auto-detection
- Crop-stage aware prevention
- Translation
- Audio (TTS)
- PDF Prescription
- DB Analytics for both paths
- Smart fallback based on confidence & crop mismatch
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
from sqlalchemy.orm import Session
from pathlib import Path
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import asyncio

# ================= IMPORTS =================
from ..ml.disease_detector import DiseaseDetector
from ..ml.dual_classifier import dual_bot
from ..ml.translator import translate_response
from ..ml.audio_generator import generate_audio_response
from ..config import get_settings
from ..models.schemas import PredictionResponse
from ..models.sql_models import Prediction
from ..database import get_db
from ..utils.logger import Logger
from ..utils.pdf_generator import generate_prescription_pdf

# ================= INIT =================
router = APIRouter(tags=["Disease Detection"])
settings = get_settings()
logger = Logger(__name__)

detector = DiseaseDetector()

# ================= KNOWLEDGE BASE =================
knowledge_base = {}
try:
    # ✅ FIX 1: KB PATH GALAT THA - REMOVE DOUBLE CONCATENATION
    kb_path = Path(settings.KB_PATH)  # Pehle tha: Path(settings.KB_PATH) / settings.KB_PATH
    if kb_path.exists():
        with open(kb_path, encoding="utf-8") as f:
            knowledge_base = json.load(f)
        logger.success(f"✓ KB loaded from {kb_path}")
    else:
        # Try alternative paths
        alt_paths = [
            Path("ml/knowledge_base/diseases.json"),
            Path("knowledge_base/diseases.json"),
            Path("../ml/knowledge_base/diseases.json"),
        ]
        for alt_path in alt_paths:
            if alt_path.exists():
                with open(alt_path, encoding="utf-8") as f:
                    knowledge_base = json.load(f)
                logger.success(f"✓ KB loaded from alternative path: {alt_path}")
                break
        else:
            logger.warning("⚠ Knowledge base not found at any known location")
except Exception as e:
    logger.error(f"KB load error: {e}")

# ================= HELPERS =================

def get_treatment_for_disease(disease: str, lang: str = "en") -> List[str]:
    """Fetches treatment steps with language support."""
    if disease in knowledge_base:
        treatment_data = knowledge_base[disease].get("treatment", {})
        # Return language-specific treatment if available, else English
        if lang in treatment_data:
            return treatment_data[lang]
        elif "en" in treatment_data:
            return treatment_data["en"]
    return ["Consult an agricultural expert."]

def get_description_for_disease(disease: str, lang: str = "en") -> str:
    """Fetches disease description with language support."""
    if disease in knowledge_base:
        desc_data = knowledge_base[disease].get("description", {})
        if lang in desc_data:
            return desc_data[lang]
        elif "en" in desc_data:
            return desc_data["en"]
    return "Diagnosis complete, but detailed description requires internet."

def get_prevention_for_disease(disease: str, stage: str, lang: str = "en") -> List[str]:
    """Fetches prevention steps with crop-stage filtering and language support."""
    if disease in knowledge_base:
        prevention_data = knowledge_base[disease].get("prevention", {})
        
        # Get language-specific prevention
        if lang in prevention_data:
            all_preventions = prevention_data[lang]
        elif "en" in prevention_data:
            all_preventions = prevention_data["en"]
        else:
            all_preventions = ["Ensure field sanitation and consult an expert."]
        
        # Apply crop-stage filtering for sensitive stages
        if stage.lower() in ["flowering", "fruiting"]:
            return [
                p for p in all_preventions 
                if "chemical" not in p.lower() 
                and "strong fungicide" not in p.lower()
                and "harsh" not in p.lower()
            ]
        
        return all_preventions
    
    return ["Ensure field sanitation and consult an expert."]

# ✅ FIX 2: SAFE PROBABILITY EXTRACTOR HELPER
def _get_probability(value: Any) -> float:
    """Safely extract probability from value that could be dict or float."""
    if isinstance(value, dict):
        return value.get("probability", 0.0)
    elif isinstance(value, (int, float)):
        return float(value)
    else:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

def filter_predictions_by_crop(predictions: Dict[str, Any], crop_type: str) -> Dict[str, Any]:
    """Filters diseases relevant to the crop and normalizes confidence."""
    if not predictions:
        return {}
    
    target_crop = ""
    
    if crop_type and crop_type != "Unknown":
        target_crop = crop_type.lower()
    else:
        # Auto-detect crop from top prediction - SAFE VERSION
        if predictions:
            # ✅ FIX 2: USE SAFE HELPER INSTEAD OF ASSUMING predictions[k]["probability"]
            try:
                top_raw = max(predictions, key=lambda k: _get_probability(predictions[k]))
                if "___" in top_raw:
                    target_crop = top_raw.split("___")[0].lower()
                elif "_" in top_raw:
                    target_crop = top_raw.split("_")[0].lower()
                else:
                    return predictions
            except Exception as e:
                logger.warning(f"Error detecting top crop: {e}")
                return predictions

    # Filter by crop name
    filtered = {}
    for disease_name, prob_data in predictions.items():
        if target_crop and target_crop in disease_name.lower():
            filtered[disease_name] = prob_data
    
    if not filtered:
        return predictions

    # Calculate total confidence using safe helper
    total_crop_confidence = sum(_get_probability(v) for v in filtered.values())
    
    if total_crop_confidence == 0:
        return filtered

    # Normalize to sum to 1
    normalized_predictions = {}
    for disease_name, prob_data in filtered.items():
        prob = _get_probability(prob_data)
        
        # Preserve original structure if it's a dict
        if isinstance(prob_data, dict):
            normalized_predictions[disease_name] = {
                **prob_data,  # Keep all original keys
                "probability": round(prob / total_crop_confidence, 4)
            }
        else:
            # If it's just a float, create proper structure
            normalized_predictions[disease_name] = {
                "raw_name": disease_name,
                "probability": round(prob / total_crop_confidence, 4)
            }

    return normalized_predictions

async def get_fresh_advisory(disease_key: str, language: str, crop_stage: str) -> tuple:
    """
    THE DYNAMIC ADVISORY SWITCH
    Priority: Fresh LLM API → Local Knowledge Base
    """
    advisory_source = "Local Knowledge Base"
    
    # Try Fresh API Advisory first
    try:
        from ..ml.chatbot_agent import process_chat_without_image
        
        prompt = f"""Provide a concise advisory for plant disease '{disease_key}'.
        Crop Stage: {crop_stage}
        Language: {language}
        
        Return in this exact JSON format:
        {{
            "treatment": ["step1", "step2", "step3", "step4"],
            "description": "brief explanation",
            "prevention": ["tip1", "tip2", "tip3"]
        }}
        
        Keep each treatment step under 15 words."""
        
        llm_res = process_chat_without_image(prompt)
        
        if llm_res.get("success") and "reply" in llm_res:
            try:
                # Parse the LLM response
                reply_text = llm_res["reply"]
                # Extract JSON from the response (handles extra text before/after JSON)
                if "{" in reply_text and "}" in reply_text:
                    json_start = reply_text.find("{")
                    json_end = reply_text.rfind("}") + 1
                    json_str = reply_text[json_start:json_end].strip()
                    advisory_data = json.loads(json_str)
                    
                    advisory_source = "Dynamic AI Advisor"
                    logger.success(f"📝 Fresh LLM advisory loaded for {disease_key} in {language}")
                    
                    return (
                        advisory_data.get("treatment", []),
                        advisory_data.get("description", ""),
                        advisory_data.get("prevention", []),
                        advisory_source
                    )
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM JSON: {e}")
    except Exception as e:
        logger.warning(f"⚠️ Fresh advisory failed: {e}. Falling back to JSON...")
    
    # Fallback to Local Knowledge Base
    treatment = get_treatment_for_disease(disease_key, language)
    description = get_description_for_disease(disease_key, language)
    prevention = get_prevention_for_disease(disease_key, crop_stage, language)
    
    logger.info("📦 Loaded advisory from Offline JSON")
    return treatment, description, prevention, advisory_source

async def process_gemini_response(
    gemini_result: Dict[str, Any],
    crop_stage: str,
    language: str,
    file_path: str,
    farmer_id: str,
    latitude: Optional[float],
    longitude: Optional[float],
    db: Session
) -> Dict[str, Any]:
    """Process Gemini response with full feature compatibility."""
    try:
        # Extract disease info
        disease = gemini_result.get("disease", "Unknown")
        confidence = gemini_result.get("confidence", 0.0)
        
        # Get advisory using dynamic switch
        treatment, description, prevention, advisory_source = await get_fresh_advisory(
            disease_key=disease,
            language=language,
            crop_stage=crop_stage
        )
        
        # Clean disease name for display
        disease_clean = disease.replace("___", " ").replace("_", " ")
        disease_trans = disease_clean
        if language not in ["en", "en-US"]:
            disease_trans = translate_response(disease_clean, language)

        # Build unified advisory text (treatment + prevention)
        treatments_list = treatment or []
        preventions_list = prevention or []
        full_text = " ".join([str(x) for x in (treatments_list + preventions_list)])

        # Audio Generation (single-line multilingual summary)
        audio_url = None
        try:
            audio_script = f"Detected {disease_trans}. {full_text}"
            audio_filename = await generate_audio_response(audio_script, language)
            if audio_filename:
                audio_url = f"/uploads/audio/{audio_filename}"

        except Exception as audio_e:
            logger.error(f"Audio Generation Failed: {audio_e}")
        
        # Database Save
        prediction = None
        try:
            prediction = Prediction(
                farmer_id=farmer_id,
                disease=disease,
                confidence=float(confidence),
                latitude=latitude,
                longitude=longitude,
                crop_stage=crop_stage,
                top5={},
                treatment=treatment,
                prevention=prevention,
                description=description,
                image_path=str(file_path),
                knowledge_source="gemini",
                fallback_reason=gemini_result.get("fallback_reason", "Low confidence"),
                advisory_source=advisory_source
            )
            db.add(prediction)
            db.commit()
            db.refresh(prediction)
            logger.success(f"Gemini analytics saved for ID: {farmer_id}")
        except Exception as db_e:
            logger.error(f"DB Save Failed: {db_e}")
        
        # PDF Generation
        pdf_url = None
        try:
            if prediction:
                pdf_data = {
                    "farmer_id": farmer_id,
                    "disease": disease_trans,
                    "confidence": confidence,
                    "description": description,
                    "treatment": treatment,
                    "prevention": prevention,
                    "full_text": full_text,
                    "audio_url": audio_url,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "image_path": str(file_path),
                    "language": language,
                    "crop_stage": crop_stage,
                    "knowledge_source": "Gemini Vision AI",
                    "model_used": "Gemini-1.5-Flash",
                    "advisory_source": advisory_source
                }
                
                filename_base = str(prediction.id)
                pdf_url = generate_prescription_pdf(pdf_data, filename_base)
                logger.success(f"PDF Created: {pdf_url}")
        except Exception as pdf_e:
            logger.error(f"PDF Generation Failed: {pdf_e}")
        
        return {
            "disease": disease,
            "confidence": confidence,
            "description": description,
            "treatment": treatment,
            "prevention": prevention,
            "language": language,
            "audio_url": audio_url,
            "pdf_url": pdf_url,
            "crop_stage": crop_stage,
            "advisory_source": advisory_source,
            "knowledge_source": "GEMINI_VISION_AI",
            "model_used": "Gemini-1.5-Flash",
            "fallback_reason": gemini_result.get("fallback_reason", ""),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Gemini processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini processing failed: {e}")

# ================= API ENDPOINT =================

@router.post("/predict", response_model=PredictionResponse)
async def predict_disease(
    file: UploadFile = File(...),
    crop_type: str = Form("Unknown"),
    language: str = Form("en"),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    farmer_id: str = Form("guest_user"),
    crop_stage: str = Form("Vegetative"),
    db: Session = Depends(get_db),
):
    """Main disease prediction endpoint with hybrid intelligence."""
    # ---------- Validate ----------
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Only JPG/PNG images allowed")
    
    # ---------- Save Image ----------
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = upload_dir / filename
    
    try:
        with open(file_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save error: {e}")
    
    # ---------- DUAL-CORE EDGE AI DETECTION ----------
    logger.info(f"🚀 Running Dual-Core Engine. User Crop: {crop_type}")
    
    try:
        ai_result = dual_bot.predict(str(file_path))
    except Exception as e:
        logger.error(f"Dual-core engine failed: {e}")
        ai_result = {"success": False, "error": str(e)}
    
    use_gemini = False
    gemini_reason = ""
    
    # ---------- SMART FALLBACK DECISION ----------
    if not ai_result.get("success", False):
        use_gemini = True
        gemini_reason = "Edge AI failed to process"
    elif ai_result.get("confidence", 0.0) < 0.4:  # 40% confidence threshold
        use_gemini = True
        gemini_reason = f"Low Confidence ({ai_result.get('confidence', 0)*100:.1f}%)"
    else:
        # CROP MISMATCH CHECK
        predicted_disease = ai_result.get('disease', '').lower()
        user_crop_lower = crop_type.lower()
        
        # Extract crop family from prediction
        if "___" in predicted_disease:
            predicted_family = predicted_disease.split("___")[0]
        elif "_" in predicted_disease:
            predicted_family = predicted_disease.split("_")[0]
        else:
            predicted_family = predicted_disease
        
        # Check for mismatch only if user specified a crop
        if user_crop_lower != "unknown" and user_crop_lower != predicted_family:
            use_gemini = True
            gemini_reason = f"Mismatch: User said '{crop_type}', Model predicted '{predicted_family}'"
            logger.warning(f"⚠️ {gemini_reason}")
    
    # ---------- GEMINI FALLBACK PATH ----------
    if use_gemini:
        logger.info(f"🌐 Switching to Cloud AI. Reason: {gemini_reason}")
        try:
            gemini_result = await detector.predict(
                image_path=str(file_path),
                crop_type=crop_type
            )
            if gemini_result.get("success", False):
                gemini_result["fallback_reason"] = gemini_reason
                return await process_gemini_response(
                    gemini_result=gemini_result,
                    crop_stage=crop_stage,
                    language=language,
                    file_path=file_path,
                    farmer_id=farmer_id,
                    latitude=latitude,
                    longitude=longitude,
                    db=db
                )
        except Exception as gemini_error:
            logger.error(f"Gemini fallback also failed: {gemini_error}")
            # Continue with YOLO result even if Gemini fails
    
    # ---------- DUAL-CORE YOLO PATH (PRIMARY) ----------
    # Process YOLO result
    disease = ai_result.get("disease", "Unknown")
    confidence = ai_result.get("confidence", 0.0)
    all_predictions_raw = ai_result.get("all_predictions", {})
    used_model = ai_result.get("used_model", "Unknown")
    
    # Apply crop filtering
    filtered = filter_predictions_by_crop(all_predictions_raw, crop_type)
    
    # Get top prediction from filtered results - SAFE VERSION
    if filtered:
        # ✅ FIX 2: USE SAFE HELPER FOR TOP DISEASE SELECTION
        try:
            top_disease = max(filtered, key=lambda k: _get_probability(filtered[k]))
            confidence = _get_probability(filtered[top_disease])  # Extract float safely
        except Exception as e:
            logger.error(f"Error finding top disease: {e}")
            top_disease = disease
            confidence = ai_result.get("confidence", 0.0)
    elif disease != "Unknown":
        top_disease = disease
    else:
        top_disease = "Uncertain"
        confidence = 0.0
    
    disease = top_disease
    
    # ---------- DYNAMIC ADVISORY SWITCH ----------
    treatment, description, prevention, advisory_source = await get_fresh_advisory(
        disease_key=disease,
        language=language,
        crop_stage=crop_stage
    )
    
    # ---------- Translation ----------
    disease_clean = disease.replace("___", " ").replace("_", " ")
    disease_trans = disease_clean
    
    if language not in ["en", "en-US"]:
        disease_trans = translate_response(disease_clean, language)
    
    # ---------- Audio Generation ----------
    audio_url = None
    try:
        # Build unified advisory text (treatment + prevention)
        treatments_list = treatment or []
        preventions_list = prevention or []
        full_text = " ".join([str(x) for x in (treatments_list + preventions_list)])

        # Single-line multilingual summary for audio (also used in PDF)
        audio_script = f"Detected {disease_trans}. {full_text}"
        audio_file = await generate_audio_response(audio_script, language)
        if audio_file:
            audio_url = f"/uploads/audio/{audio_file}"
    except Exception as e:
        logger.error(f"TTS failed: {e}")
    
    # ---------- Database Save ----------
    prediction = None
    try:
        prediction = Prediction(
            farmer_id=farmer_id,
            disease=disease,
            confidence=float(confidence),
            latitude=latitude,
            longitude=longitude,
            crop_stage=crop_stage,
            top5=filtered,
            treatment=treatment,
            prevention=prevention,
            description=description,
            image_path=str(file_path),
            knowledge_source="dual_yolo",
            fallback_reason="" if not use_gemini else gemini_reason,
            model_used=used_model,
            advisory_source=advisory_source
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        logger.success(f"Dual-core analytics saved for ID: {farmer_id}, Model: {used_model}")
    except Exception as e:
        logger.error(f"DB save failed: {e}")
    
    # ---------- PDF Generation ----------
    pdf_url = None
    try:
        if prediction:
            pdf_data = {
                "farmer_id": farmer_id,
                "disease": disease_trans,
                "confidence": confidence,
                "description": description,
                "treatment": treatment,
                "prevention": prevention,
                "full_text": full_text,
                "audio_url": audio_url,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "image_path": str(file_path),
                "language": language,
                "crop_stage": crop_stage,
                "knowledge_source": "Dual-Core YOLO Engine",
                "model_used": used_model,
                "advisory_source": advisory_source,
                "fallback_triggered": "Yes" if use_gemini else "No"
            }
            
            pdf_url = generate_prescription_pdf(pdf_data, str(prediction.id))
            logger.success(f"PDF Created: {pdf_url}")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
    
    # ---------- FINAL RESPONSE ----------
    # Create flat dictionaries for response (Pydantic expects Dict[str, float])
    all_predictions_flat = {
        k: _get_probability(v) for k, v in all_predictions_raw.items()
    }
    
    filtered_predictions_flat = {
        k: _get_probability(v) for k, v in filtered.items()
    }
    
    return {
        "disease": disease,
        "confidence": confidence,  # This is now a float, not dict
        "description": description,
        "treatment": treatment,
        "prevention": prevention,
        "language": language,
        "audio_url": audio_url,
        "pdf_url": pdf_url,
        "crop_stage": crop_stage,
        "advisory_source": advisory_source,
        "all_predictions": all_predictions_flat,  # Dict[str, float]
        "filtered_predictions": filtered_predictions_flat,  # Dict[str, float]
        "knowledge_source": "DUAL_CORE_YOLO",
        "model_used": used_model,
        "fallback_triggered": use_gemini,
        "fallback_reason": gemini_reason if use_gemini else "",
        "success": True,
    }



# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# WEAPON 1: Hybrid Intelligence Engine

# PRIMARY:
# - Dual-Core YOLO Engine (Fast, Offline-first)
# - Gemini Vision (Online fallback, Crop-aware, High accuracy)

# FALLBACK:
# - YOLOv8 + Knowledge Base (Offline / Fail-safe)

# FEATURES:
# - Dynamic Advisory Switch (Fresh API → JSON fallback)
# - Crop filtering with auto-detection
# - Crop-stage aware prevention
# - Translation
# - Audio (TTS)
# - PDF Prescription
# - DB Analytics for both paths
# - Smart fallback based on confidence & crop mismatch
# """

# from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
# from sqlalchemy.orm import Session
# from pathlib import Path
# import json
# from typing import Dict, Any, List, Optional
# from datetime import datetime
# import uuid
# import asyncio

# # ================= IMPORTS =================
# from ..ml.disease_detector import DiseaseDetector
# from ..ml.dual_classifier import dual_bot
# from ..ml.translator import translate_response
# from ..ml.audio_generator import generate_audio_response
# from ..config import get_settings
# from ..models.schemas import PredictionResponse
# from ..models.sql_models import Prediction
# from ..database import get_db
# from ..utils.logger import Logger
# from ..utils.pdf_generator import generate_prescription_pdf

# # ================= INIT =================
# router = APIRouter(tags=["Disease Detection"])
# settings = get_settings()
# logger = Logger(__name__)

# detector = DiseaseDetector()

# # ================= KNOWLEDGE BASE =================
# knowledge_base = {}
# try:
#     kb_path = Path(settings.KB_PATH) / settings.KB_PATH
#     if kb_path.exists():
#         with open(kb_path, encoding="utf-8") as f:
#             knowledge_base = json.load(f)
#         logger.success(f"✓ KB loaded from {kb_path}")
#     else:
#         logger.warning("⚠ Knowledge base not found")
# except Exception as e:
#     logger.error(f"KB load error: {e}")

# # ================= HELPERS =================

# def get_treatment_for_disease(disease: str, lang: str = "en") -> List[str]:
#     """Fetches treatment steps with language support."""
#     if disease in knowledge_base:
#         treatment_data = knowledge_base[disease].get("treatment", {})
#         # Return language-specific treatment if available, else English
#         if lang in treatment_data:
#             return treatment_data[lang]
#         elif "en" in treatment_data:
#             return treatment_data["en"]
#     return ["Consult an agricultural expert."]

# def get_description_for_disease(disease: str, lang: str = "en") -> str:
#     """Fetches disease description with language support."""
#     if disease in knowledge_base:
#         desc_data = knowledge_base[disease].get("description", {})
#         if lang in desc_data:
#             return desc_data[lang]
#         elif "en" in desc_data:
#             return desc_data["en"]
#     return "Diagnosis complete, but detailed description requires internet."

# def get_prevention_for_disease(disease: str, stage: str, lang: str = "en") -> List[str]:
#     """Fetches prevention steps with crop-stage filtering and language support."""
#     if disease in knowledge_base:
#         prevention_data = knowledge_base[disease].get("prevention", {})
        
#         # Get language-specific prevention
#         if lang in prevention_data:
#             all_preventions = prevention_data[lang]
#         elif "en" in prevention_data:
#             all_preventions = prevention_data["en"]
#         else:
#             all_preventions = ["Ensure field sanitation and consult an expert."]
        
#         # Apply crop-stage filtering for sensitive stages
#         if stage.lower() in ["flowering", "fruiting"]:
#             return [
#                 p for p in all_preventions 
#                 if "chemical" not in p.lower() 
#                 and "strong fungicide" not in p.lower()
#                 and "harsh" not in p.lower()
#             ]
        
#         return all_preventions
    
#     return ["Ensure field sanitation and consult an expert."]

# def filter_predictions_by_crop(predictions: Dict[str, float], crop_type: str) -> Dict[str, float]:
#     """Filters diseases relevant to the crop and normalizes confidence."""
#     if not predictions:
#         return {}
    
#     target_crop = ""
    
#     if crop_type and crop_type != "Unknown":
#         target_crop = crop_type.lower()
#     else:
#         # Auto-detect crop from top prediction
#         if predictions:
#             top_raw = max(predictions, key=lambda k: predictions[k]["probability"])
#             if "___" in top_raw:
#                 target_crop = top_raw.split("___")[0].lower()
#             else:
#                 return predictions

#     filtered = {d: p for d, p in predictions.items() if target_crop in d.lower()}
    
#     if not filtered:
#         return predictions

#     total_crop_confidence = sum(filtered.values())
    
#     if total_crop_confidence == 0:
#         return filtered

#     # Normalize to sum to 1
#     normalized_predictions = {
#         d: round(p / total_crop_confidence, 4)
#         for d, p in filtered.items()
#     }

#     return normalized_predictions

# async def get_fresh_advisory(disease_key: str, language: str, crop_stage: str) -> tuple:
#     """
#     THE DYNAMIC ADVISORY SWITCH
#     Priority: Fresh LLM API → Local Knowledge Base
#     """
#     advisory_source = "Local Knowledge Base"
    
#     # Try Fresh API Advisory first
#     try:
#         from ..ml.chatbot_agent import process_chat_without_image
        
#         prompt = f"""Provide a concise advisory for plant disease '{disease_key}'.
#         Crop Stage: {crop_stage}
#         Language: {language}
        
#         Return in this exact JSON format:
#         {{
#             "treatment": ["step1", "step2", "step3", "step4"],
#             "description": "brief explanation",
#             "prevention": ["tip1", "tip2", "tip3"]
#         }}
        
#         Keep each treatment step under 15 words."""
        
#         llm_res = process_chat_without_image(prompt)
        
#         if llm_res.get("success") and "reply" in llm_res:
#             try:
#                 # Parse the LLM response
#                 reply_text = llm_res["reply"]
#                 # Extract JSON from the response (handles extra text before/after JSON)
#                 if "{" in reply_text and "}" in reply_text:
#                     json_start = reply_text.find("{")
#                     json_end = reply_text.rfind("}") + 1
#                     json_str = reply_text[json_start:json_end].strip()
#                     advisory_data = json.loads(json_str)
                    
#                     advisory_source = "Dynamic AI Advisor"
#                     logger.success(f"📝 Fresh LLM advisory loaded for {disease_key} in {language}")
                    
#                     return (
#                         advisory_data.get("treatment", []),
#                         advisory_data.get("description", ""),
#                         advisory_data.get("prevention", []),
#                         advisory_source
#                     )
#             except json.JSONDecodeError as e:
#                 logger.warning(f"Failed to parse LLM JSON: {e}")
#     except Exception as e:
#         logger.warning(f"⚠️ Fresh advisory failed: {e}. Falling back to JSON...")
    
#     # Fallback to Local Knowledge Base
#     treatment = get_treatment_for_disease(disease_key, language)
#     description = get_description_for_disease(disease_key, language)
#     prevention = get_prevention_for_disease(disease_key, crop_stage, language)
    
#     logger.info("📦 Loaded advisory from Offline JSON")
#     return treatment, description, prevention, advisory_source

# async def process_gemini_response(
#     gemini_result: Dict[str, Any],
#     crop_stage: str,
#     language: str,
#     file_path: str,
#     farmer_id: str,
#     latitude: Optional[float],
#     longitude: Optional[float],
#     db: Session
# ) -> Dict[str, Any]:
#     """Process Gemini response with full feature compatibility."""
#     try:
#         # Extract disease info
#         disease = gemini_result.get("disease", "Unknown")
#         confidence = gemini_result.get("confidence", 0.0)
        
#         # Get advisory using dynamic switch
#         treatment, description, prevention, advisory_source = await get_fresh_advisory(
#             disease_key=disease,
#             language=language,
#             crop_stage=crop_stage
#         )
        
#         # Clean disease name for display
#         disease_clean = disease.replace("___", " ").replace("_", " ")
#         disease_trans = disease_clean
        
#         if language not in ["en", "en-US"]:
#             disease_trans = translate_response(disease_clean, language)
        
#         # Audio Generation
#         audio_url = None
#         try:
#             treatment_summary = treatment[0] if treatment else "Consult expert."
#             audio_script = f"Detected {disease_trans}. {treatment_summary}"
#             audio_filename = await generate_audio_response(audio_script, language)
#             if audio_filename:
#                 audio_url = f"/uploads/{audio_filename}"
#         except Exception as audio_e:
#             logger.error(f"Audio Generation Failed: {audio_e}")
        
#         # Database Save
#         prediction = None
#         try:
#             prediction = Prediction(
#                 farmer_id=farmer_id,
#                 disease=disease,
#                 confidence=float(confidence),
#                 latitude=latitude,
#                 longitude=longitude,
#                 crop_stage=crop_stage,
#                 top5={},
#                 treatment=treatment,
#                 prevention=prevention,
#                 description=description,
#                 image_path=str(file_path),
#                 knowledge_source="gemini",
#                 fallback_reason=gemini_result.get("fallback_reason", "Low confidence"),
#                 advisory_source=advisory_source
#             )
#             db.add(prediction)
#             db.commit()
#             db.refresh(prediction)
#             logger.success(f"Gemini analytics saved for ID: {farmer_id}")
#         except Exception as db_e:
#             logger.error(f"DB Save Failed: {db_e}")
        
#         # PDF Generation
#         pdf_url = None
#         try:
#             if prediction:
#                 pdf_data = {
#                     "farmer_id": farmer_id,
#                     "disease": disease_trans,
#                     "confidence": confidence,
#                     "description": description,
#                     "treatment": treatment,
#                     "prevention": prevention,
#                     "audio_url": audio_url,
#                     "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
#                     "image_path": str(file_path),
#                     "language": language,
#                     "crop_stage": crop_stage,
#                     "knowledge_source": "Gemini Vision AI",
#                     "model_used": "Gemini-1.5-Flash",
#                     "advisory_source": advisory_source
#                 }
                
#                 filename_base = str(prediction.id)
#                 pdf_url = generate_prescription_pdf(pdf_data, filename_base)
#                 logger.success(f"PDF Created: {pdf_url}")
#         except Exception as pdf_e:
#             logger.error(f"PDF Generation Failed: {pdf_e}")
        
#         return {
#             "disease": disease,
#             "confidence": confidence,
#             "description": description,
#             "treatment": treatment,
#             "prevention": prevention,
#             "language": language,
#             "audio_url": audio_url,
#             "pdf_url": pdf_url,
#             "crop_stage": crop_stage,
#             "advisory_source": advisory_source,
#             "knowledge_source": "GEMINI_VISION_AI",
#             "model_used": "Gemini-1.5-Flash",
#             "fallback_reason": gemini_result.get("fallback_reason", ""),
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Gemini processing error: {e}")
#         raise HTTPException(status_code=500, detail=f"Gemini processing failed: {e}")

# # ================= API ENDPOINT =================

# @router.post("/predict", response_model=PredictionResponse)
# async def predict_disease(
#     file: UploadFile = File(...),
#     crop_type: str = Form("Unknown"),
#     language: str = Form("en"),
#     latitude: Optional[float] = Form(None),
#     longitude: Optional[float] = Form(None),
#     farmer_id: str = Form("guest_user"),
#     crop_stage: str = Form("Vegetative"),
#     db: Session = Depends(get_db),
# ):
#     """Main disease prediction endpoint with hybrid intelligence."""
#     # ---------- Validate ----------
#     if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
#         raise HTTPException(status_code=400, detail="Only JPG/PNG images allowed")
    
#     # ---------- Save Image ----------
#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)
    
#     filename = f"{uuid.uuid4()}_{file.filename}"
#     file_path = upload_dir / filename
    
#     try:
#         with open(file_path, "wb") as f:
#             while chunk := await file.read(1024 * 1024):
#                 f.write(chunk)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"File save error: {e}")
    
#     # ---------- DUAL-CORE EDGE AI DETECTION ----------
#     logger.info(f"🚀 Running Dual-Core Engine. User Crop: {crop_type}")
    
#     try:
#         ai_result = dual_bot.predict(str(file_path))
#     except Exception as e:
#         logger.error(f"Dual-core engine failed: {e}")
#         ai_result = {"success": False, "error": str(e)}
    
#     use_gemini = False
#     gemini_reason = ""
    
#     # ---------- SMART FALLBACK DECISION ----------
#     if not ai_result.get("success", False):
#         use_gemini = True
#         gemini_reason = "Edge AI failed to process"
#     elif ai_result.get("confidence", 0.0) < 0.4:  # 40% confidence threshold
#         use_gemini = True
#         gemini_reason = f"Low Confidence ({ai_result.get('confidence', 0)*100:.1f}%)"
#     else:
#         # CROP MISMATCH CHECK
#         predicted_disease = ai_result.get('disease', '').lower()
#         user_crop_lower = crop_type.lower()
        
#         # Extract crop family from prediction
#         if "___" in predicted_disease:
#             predicted_family = predicted_disease.split("___")[0]
#         elif "_" in predicted_disease:
#             predicted_family = predicted_disease.split("_")[0]
#         else:
#             predicted_family = predicted_disease
        
#         # Check for mismatch only if user specified a crop
#         if user_crop_lower != "unknown" and user_crop_lower != predicted_family:
#             use_gemini = True
#             gemini_reason = f"Mismatch: User said '{crop_type}', Model predicted '{predicted_family}'"
#             logger.warning(f"⚠️ {gemini_reason}")
    
#     # ---------- GEMINI FALLBACK PATH ----------
#     if use_gemini:
#         logger.info(f"🌐 Switching to Cloud AI. Reason: {gemini_reason}")
#         try:
#             gemini_result = await detector.predict(
#                 image_path=str(file_path),
#                 crop_type=crop_type
#             )
#             if gemini_result.get("success", False):
#                 gemini_result["fallback_reason"] = gemini_reason
#                 return await process_gemini_response(
#                     gemini_result=gemini_result,
#                     crop_stage=crop_stage,
#                     language=language,
#                     file_path=file_path,
#                     farmer_id=farmer_id,
#                     latitude=latitude,
#                     longitude=longitude,
#                     db=db
#                 )
#         except Exception as gemini_error:
#             logger.error(f"Gemini fallback also failed: {gemini_error}")
#             # Continue with YOLO result even if Gemini fails
    
#     # ---------- DUAL-CORE YOLO PATH (PRIMARY) ----------
#     # Process YOLO result
#     disease = ai_result.get("disease", "Unknown")
#     confidence = ai_result.get("confidence", 0.0)
#     all_predictions = ai_result.get("all_predictions", {})
#     used_model = ai_result.get("used_model", "Unknown")
    
#     # Apply crop filtering
#     filtered = filter_predictions_by_crop(all_predictions, crop_type)
    
#     # Get top prediction from filtered results
#     if filtered:
#         top_disease = max(filtered, key=lambda k: filtered[k]["probability"])
#         confidence = filtered[top_disease]
#     elif disease != "Unknown":
#         top_disease = disease
#     else:
#         top_disease = "Uncertain"
#         confidence = 0.0
    
#     disease = top_disease
    
#     # ---------- DYNAMIC ADVISORY SWITCH ----------
#     treatment, description, prevention, advisory_source = await get_fresh_advisory(
#         disease_key=disease,
#         language=language,
#         crop_stage=crop_stage
#     )
    
#     # ---------- Translation ----------
#     disease_clean = disease.replace("___", " ").replace("_", " ")
#     disease_trans = disease_clean
    
#     if language not in ["en", "en-US"]:
#         disease_trans = translate_response(disease_clean, language)
    
#     # ---------- Audio Generation ----------
#     audio_url = None
#     try:
#         treatment_summary = treatment[0] if treatment else "Consult expert."
#         audio_script = f"Detected {disease_trans}. {treatment_summary}"
#         audio_file = await generate_audio_response(audio_script, language)
#         if audio_file:
#             audio_url = f"/uploads/{audio_file}"
#     except Exception as e:
#         logger.error(f"TTS failed: {e}")
    
#     # ---------- Database Save ----------
#     prediction = None
#     try:
#         prediction = Prediction(
#             farmer_id=farmer_id,
#             disease=disease,
#             confidence=float(confidence),
#             latitude=latitude,
#             longitude=longitude,
#             crop_stage=crop_stage,
#             top5=filtered,
#             treatment=treatment,
#             prevention=prevention,
#             description=description,
#             image_path=str(file_path),
#             knowledge_source="dual_yolo",
#             fallback_reason="" if not use_gemini else gemini_reason,
#             model_used=used_model,
#             advisory_source=advisory_source
#         )
#         db.add(prediction)
#         db.commit()
#         db.refresh(prediction)
#         logger.success(f"Dual-core analytics saved for ID: {farmer_id}, Model: {used_model}")
#     except Exception as e:
#         logger.error(f"DB save failed: {e}")
    
#     # ---------- PDF Generation ----------
#     pdf_url = None
#     try:
#         if prediction:
#             pdf_data = {
#                 "farmer_id": farmer_id,
#                 "disease": disease_trans,
#                 "confidence": confidence,
#                 "description": description,
#                 "treatment": treatment,
#                 "prevention": prevention,
#                 "audio_url": audio_url,
#                 "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
#                 "image_path": str(file_path),
#                 "language": language,
#                 "crop_stage": crop_stage,
#                 "knowledge_source": "Dual-Core YOLO Engine",
#                 "model_used": used_model,
#                 "advisory_source": advisory_source,
#                 "fallback_triggered": "Yes" if use_gemini else "No"
#             }
            
#             pdf_url = generate_prescription_pdf(pdf_data, str(prediction.id))
#             logger.success(f"PDF Created: {pdf_url}")
#     except Exception as e:
#         logger.error(f"PDF generation failed: {e}")
    
#     # ---------- FINAL RESPONSE ----------
#     return {
#         "disease": disease,
#         "confidence": confidence,
#         "description": description,
#         "treatment": treatment,
#         "prevention": prevention,
#         "language": language,
#         "audio_url": audio_url,
#         "pdf_url": pdf_url,
#         "crop_stage": crop_stage,
#         "advisory_source": advisory_source,
#         "all_predictions": all_predictions,
#         "filtered_predictions": filtered,
#         "knowledge_source": "DUAL_CORE_YOLO",
#         "model_used": used_model,
#         "fallback_triggered": use_gemini,
#         "fallback_reason": gemini_reason if use_gemini else "",
#         "success": True,
#     }


# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# WEAPON 1: Hybrid Intelligence Engine

# PRIMARY:
# - Dual-Core YOLO Engine (Fast, Offline-first)
# - Gemini Vision (Online fallback, Crop-aware, High accuracy)

# FALLBACK:
# - YOLOv8 + Knowledge Base (Offline / Fail-safe)

# FEATURES:
# - Crop filtering with auto-detection
# - Crop-stage aware prevention
# - Translation
# - Audio (TTS)
# - PDF Prescription
# - DB Analytics for both Gemini and YOLO paths
# - Smart fallback based on confidence & crop mismatch
# """

# from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
# from sqlalchemy.orm import Session
# from pathlib import Path
# import json
# from typing import Dict, Any, List, Optional
# from datetime import datetime
# import uuid
# import socket  # <--- Add this at the top with other imports
# # ================= IMPORTS =================
# from ..ml.disease_detector import DiseaseDetector   # Gemini Class
# from ..ml.dual_classifier import dual_bot           # ✅ NEW: Dual Model
# from ..ml.translator import translate_response
# from ..ml.audio_generator import generate_audio_response
# from ..config import get_settings
# from ..models.schemas import PredictionResponse
# from ..models.sql_models import Prediction
# from ..database import get_db
# from ..utils.logger import Logger
# from ..utils.pdf_generator import generate_prescription_pdf

# # ================= INIT =================
# router = APIRouter(tags=["Disease Detection"])
# settings = get_settings()
# logger = Logger(__name__)

# detector = DiseaseDetector()  # Gemini Instance

# # ================= KNOWLEDGE BASE =================
# knowledge_base = {}
# try:
#     kb_path = Path(settings.KNOWLEDGE_BASE_PATH) / settings.KNOWLEDGE_BASE_FILE
#     if kb_path.exists():
#         with open(kb_path, encoding="utf-8") as f:
#             knowledge_base = json.load(f)
#         logger.success(f"✓ KB loaded from {kb_path}")
#     else:
#         logger.warning("⚠ Knowledge base not found")
# except Exception as e:
#     logger.error(f"KB load error: {e}")

# # ================= HELPERS =================

# def get_treatment_for_disease(disease: str) -> List[str]:
#     """Fetches treatment steps with fallback."""
#     if disease in knowledge_base:
#         return knowledge_base[disease].get("treatment", ["Consult an agricultural expert."])
#     return ["Treatment information currently unavailable. Please consult a local expert."]

# def get_prevention_for_disease(disease: str, stage: str) -> List[str]:
#     """
#     Fetches prevention steps with crop-stage filtering.
#     ✅ MASTERSTROKE LOGIC: Filters harsh chemicals during sensitive stages.
#     """
#     if disease in knowledge_base:
#         all_preventions = knowledge_base[disease].get("prevention", [])
        
#         # --- FINAL STAGE-BASED FILTERING LOGIC ---
#         if stage.lower() in ["flowering", "fruiting"]:
#             # Filter out harsh chemical suggestions which might damage flowers/fruit/pollen
#             return [
#                 p for p in all_preventions 
#                 if "chemical" not in p.lower() 
#                 and "strong fungicide" not in p.lower()
#                 and "harsh" not in p.lower()
#             ]
        
#         return all_preventions
    
#     # Fallback if disease not found in KB
#     return ["Ensure field sanitation and consult an expert for specific preventative steps."]

# def filter_predictions_by_crop(predictions: Dict[str, float], crop_type: str) -> Dict[str, float]:
#     """
#     MATH MAGIC: Increases accuracy by filtering diseases relevant to the crop.
#     ✅ RETAINED FROM OLD CODE: Auto-detection logic for "Unknown" crop type.
#     """
#     if not predictions:
#         return {}
    
#     target_crop = ""
    
#     if crop_type and crop_type != "Unknown":
#         target_crop = crop_type.lower()
#     else:
#         # Auto-detect crop from top prediction (FROM OLD CODE)
#         if predictions:
#             top_raw = max(predictions, key=predictions.get)
#             if "___" in top_raw:
#                 target_crop = top_raw.split("___")[0].lower()
#             else:
#                 return predictions  # Return as-is if no crop delimiter

#     filtered = {d: p for d, p in predictions.items() if target_crop in d.lower()}
    
#     if not filtered:
#         return predictions  # Fallback to original predictions

#     total_crop_confidence = sum(filtered.values())
    
#     if total_crop_confidence == 0:
#         return filtered

#     # Normalize to sum to 1
#     normalized_predictions = {
#         d: round(p / total_crop_confidence, 4)
#         for d, p in filtered.items()
#     }

#     return normalized_predictions

# async def process_gemini_response(
#     gemini_result: Dict[str, Any],
#     crop_stage: str,
#     language: str,
#     file_path: str,
#     farmer_id: str,
#     latitude: Optional[float],
#     longitude: Optional[float],
#     db: Session
# ) -> Dict[str, Any]:
#     """
#     Process Gemini response to ensure full feature compatibility.
#     This adds the missing functionality (DB, PDF, Audio, Translation) to Gemini path.
#     """
#     try:
#         # Extract disease info from Gemini
#         disease = gemini_result.get("disease", "Unknown")
#         confidence = gemini_result.get("confidence", 0.0)
#         gemini_treatment = gemini_result.get("treatment", [])
#         gemini_prevention = gemini_result.get("prevention", [])
        
#         # Use our knowledge base for treatment/prevention if Gemini doesn't provide it
#         treatment = gemini_treatment if gemini_treatment else get_treatment_for_disease(disease)
#         prevention = gemini_prevention if gemini_prevention else get_prevention_for_disease(disease, crop_stage)
        
#         # Apply crop-stage filtering to Gemini's prevention if needed
#         if not gemini_prevention:
#             prevention = get_prevention_for_disease(disease, crop_stage)
        
#         # Translation
#         disease_clean = disease.replace("___", " ").replace("_", " ")
#         disease_trans = disease_clean
        
#         if language not in ["en", "en-US"]:
#             treatment = [translate_response(t, language) for t in treatment]
#             prevention = [translate_response(p, language) for p in prevention]
#             disease_trans = translate_response(disease_clean, language)
        
#         # Audio Generation
#         audio_url = None
#         try:
#             treatment_summary = treatment[0] if treatment else "Consult expert."
#             audio_script = f"Detected {disease_trans}. {treatment_summary}"
#             audio_filename = await generate_audio_response(audio_script, language)
#             if audio_filename:
#                 audio_url = f"/uploads/{audio_filename}"
#         except Exception as audio_e:
#             logger.error(f"Audio Generation Failed for Gemini: {audio_e}")
        
#         # Database Save (CRITICAL for analytics)
#         prediction = None
#         try:
#             prediction = Prediction(
#                 farmer_id=farmer_id,
#                 disease=disease,
#                 confidence=float(confidence),
#                 latitude=latitude,
#                 longitude=longitude,
#                 crop_stage=crop_stage,
#                 top5={},  # Gemini doesn't provide multiple predictions
#                 treatment=treatment,
#                 prevention=prevention,
#                 image_path=str(file_path),
#                 knowledge_source="gemini",  # Track source
#                 fallback_reason=gemini_result.get("fallback_reason", "Low confidence")
#             )
#             db.add(prediction)
#             db.commit()
#             db.refresh(prediction)
#             logger.success(f"Gemini analytics saved for ID: {farmer_id}")
#         except Exception as db_e:
#             logger.error(f"DB Save Failed for Gemini: {db_e}")
        
#         # PDF Generation
#         pdf_url = None
#         try:
#             if prediction:
#                 pdf_data = {
#                     "farmer_id": farmer_id,
#                     "disease": disease_trans,
#                     "confidence": confidence,
#                     "treatment": treatment,
#                     "prevention": prevention,
#                     "audio_url": audio_url,
#                     "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
#                     "image_path": str(file_path),
#                     "language": language,
#                     "crop_stage": crop_stage,
#                     "knowledge_source": "Gemini Vision AI",
#                     "model_used": "Gemini-1.5-Flash"
#                 }
                
#                 filename_base = str(prediction.id)
#                 pdf_url = generate_prescription_pdf(pdf_data, filename_base)
#                 logger.success(f"Gemini PDF Created: {pdf_url}")
#         except Exception as pdf_e:
#             logger.error(f"PDF Generation Failed for Gemini: {pdf_e}")
        
#         return {
#             "disease": disease,
#             "confidence": confidence,
#             "treatment": treatment,
#             "prevention": prevention,
#             "language": language,
#             "audio_url": audio_url,
#             "pdf_url": pdf_url,
#             "crop_stage": crop_stage,
#             "all_predictions": {},
#             "filtered_predictions": {},
#             "knowledge_source": "GEMINI_VISION_AI",
#             "model_used": "Gemini-1.5-Flash",
#             "fallback_reason": gemini_result.get("fallback_reason", ""),
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Gemini processing error: {e}")
#         # Fallback to returning Gemini result as-is
#         return {
#             **gemini_result,
#             "language": language,
#             "audio_url": None,
#             "pdf_url": None,
#             "crop_stage": crop_stage,
#             "all_predictions": {},
#             "filtered_predictions": {},
#             "success": True
#         }

# # ================= API ENDPOINT =================

# @router.post("/predict", response_model=PredictionResponse)
# async def predict_disease(
#     file: UploadFile = File(...),
#     crop_type: str = Form("Unknown"),
#     language: str = Form("en"),
#     latitude: Optional[float] = Form(None),
#     longitude: Optional[float] = Form(None),
#     farmer_id: str = Form("guest_user"),
#     crop_stage: str = Form("Vegetative"),
#     db: Session = Depends(get_db),
# ):
#     # ---------- Validate ----------
#     if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
#         raise HTTPException(status_code=400, detail="Only JPG/PNG images allowed")

#     # ---------- Save Image ----------
#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)

#     filename = f"{uuid.uuid4()}_{file.filename}"
#     file_path = upload_dir / filename

#     try:
#         with open(file_path, "wb") as f:
#             while chunk := await file.read(1024 * 1024):
#                 f.write(chunk)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"File save error: {e}")

#     # ---------- DUAL-CORE EDGE AI DETECTION ----------
#     logger.info(f"🚀 Running Dual-Core Engine. User Crop: {crop_type}")
    
#     try:
#         ai_result = dual_bot.predict(str(file_path))
#     except Exception as e:
#         logger.error(f"Dual-core engine failed: {e}")
#         ai_result = {"success": False, "error": str(e)}

#     use_gemini = False
#     gemini_reason = ""
    
#     # ---------- SMART FALLBACK DECISION ----------
#     if not ai_result.get("success", False):
#         use_gemini = True
#         gemini_reason = "Edge AI failed to process"
#     elif ai_result.get("confidence", 0.0) < 0.4:  # 40% confidence threshold
#         use_gemini = True
#         gemini_reason = f"Low Confidence ({ai_result.get('confidence', 0)*100:.1f}%)"
#     else:
#         # GUARDRAIL: CROP MISMATCH CHECK
#         predicted_disease = ai_result.get('disease', '').lower()
#         user_crop_lower = crop_type.lower()
        
#         # Extract crop family from prediction (e.g., "strawberry___leaf_scorch" -> "strawberry")
#         if "___" in predicted_disease:
#             predicted_family = predicted_disease.split("___")[0]
#         elif "_" in predicted_disease:
#             predicted_family = predicted_disease.split("_")[0]
#         else:
#             predicted_family = predicted_disease
        
#         # Check for mismatch only if user specified a crop
#         if user_crop_lower != "unknown" and user_crop_lower != predicted_family:
#             use_gemini = True
#             gemini_reason = f"Mismatch: User said '{crop_type}', Model predicted '{predicted_family}'"
#             logger.warning(f"⚠️ {gemini_reason}")

#     # ---------- GEMINI FALLBACK PATH ----------
#     if use_gemini:
#         logger.info(f"🌐 Switching to Cloud AI. Reason: {gemini_reason}")
#         try:
#             gemini_result = await detector.predict(
#                 image_path=str(file_path),
#                 crop_type=crop_type
#             )
#             if gemini_result.get("success", False):
#                 gemini_result["fallback_reason"] = gemini_reason
#                 # Process & Return Gemini Result with full features
#                 return await process_gemini_response(
#                     gemini_result=gemini_result,
#                     crop_stage=crop_stage,
#                     language=language,
#                     file_path=file_path,
#                     farmer_id=farmer_id,
#                     latitude=latitude,
#                     longitude=longitude,
#                     db=db
#                 )
#         except Exception as gemini_error:
#             logger.error(f"Gemini fallback also failed: {gemini_error}")
#             # Continue with YOLO result even if Gemini fails

#     # ---------- DUAL-CORE YOLO PATH (PRIMARY) ----------
#     # Process YOLO result (Edge AI succeeded)
#     disease = ai_result.get("disease", "Unknown")
#     confidence = ai_result.get("confidence", 0.0)
#     all_predictions = ai_result.get("all_predictions", {})
#     used_model = ai_result.get("used_model", "Unknown")
    
#     # Apply crop filtering with auto-detection
#     filtered = filter_predictions_by_crop(all_predictions, crop_type)
    
#     # Get top prediction from filtered results
#     if filtered:
#         top_disease = max(filtered, key=filtered.get)
#         confidence = filtered[top_disease]
#     elif disease != "Unknown":
#         top_disease = disease
#     else:
#         top_disease = "Uncertain"
#         confidence = 0.0

#     disease = top_disease
#     treatment = get_treatment_for_disease(disease)
#     prevention = get_prevention_for_disease(disease, crop_stage)

#     # ---------- Translation ----------
#     disease_clean = disease.replace("___", " ").replace("_", " ")
#     disease_trans = disease_clean

#     if language not in ["en", "en-US"]:
#         treatment = [translate_response(t, language) for t in treatment]
#         prevention = [translate_response(p, language) for p in prevention]
#         disease_trans = translate_response(disease_clean, language)

#     # ---------- Audio Generation ----------
#     audio_url = None
#     try:
#         treatment_summary = treatment[0] if treatment else "Consult expert."
#         audio_script = f"Detected {disease_trans}. {treatment_summary}"
#         audio_file = await generate_audio_response(audio_script, language)
#         if audio_file:
#             audio_url = f"/uploads/{audio_file}"
#     except Exception as e:
#         logger.error(f"TTS failed: {e}")

#     # ---------- Database Save ----------
#     prediction = None
#     try:
#         prediction = Prediction(
#             farmer_id=farmer_id,
#             disease=disease,
#             confidence=float(confidence),
#             latitude=latitude,
#             longitude=longitude,
#             crop_stage=crop_stage,
#             top5=filtered,
#             treatment=treatment,
#             prevention=prevention,
#             image_path=str(file_path),
#             knowledge_source="dual_yolo",  # Track source
#             fallback_reason="" if not use_gemini else gemini_reason,
#             model_used=used_model
#         )
#         db.add(prediction)
#         db.commit()
#         db.refresh(prediction)
#         logger.success(f"Dual-core analytics saved for ID: {farmer_id}, Model: {used_model}")
#     except Exception as e:
#         logger.error(f"DB save failed: {e}")

#     # ---------- PDF Generation ----------
#     pdf_url = None
#     try:
#         if prediction:
#             pdf_data = {
#                 "farmer_id": farmer_id,
#                 "disease": disease_trans,
#                 "confidence": confidence,
#                 "treatment": treatment,
#                 "prevention": prevention,
#                 "audio_url": audio_url,
#                 "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
#                 "image_path": str(file_path),
#                 "language": language,
#                 "crop_stage": crop_stage,
#                 "knowledge_source": "Dual-Core YOLO Engine",
#                 "model_used": used_model,
#                 "fallback_triggered": "Yes" if use_gemini else "No"
#             }
            
#             pdf_url = generate_prescription_pdf(pdf_data, str(prediction.id))
#             logger.success(f"YOLO PDF Created: {pdf_url}")
#     except Exception as e:
#         logger.error(f"PDF generation failed: {e}")

#     # ---------- FINAL RESPONSE ----------
#     return {
#         "disease": disease,
#         "confidence": confidence,
#         "treatment": treatment,
#         "prevention": prevention,
#         "language": language,
#         "audio_url": audio_url,
#         "pdf_url": pdf_url,
#         "crop_stage": crop_stage,
#         "all_predictions": all_predictions,
#         "filtered_predictions": filtered,
#         "knowledge_source": "DUAL_CORE_YOLO",
#         "model_used": used_model,
#         "fallback_triggered": use_gemini,
#         "fallback_reason": gemini_reason if use_gemini else "",
#         "success": True,
#     }

# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# WEAPON 1: Hybrid Intelligence Engine

# PRIMARY:
# - Gemini Vision (Online, Crop-aware, High accuracy)

# FALLBACK:
# - YOLOv8 + Knowledge Base (Offline / Fail-safe)

# FEATURES:
# - Crop filtering with auto-detection
# - Crop-stage aware prevention
# - Translation
# - Audio (TTS)
# - PDF Prescription
# - DB Analytics for both Gemini and YOLO paths
# """

# from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
# from sqlalchemy.orm import Session
# from pathlib import Path
# import json
# from typing import Dict, Any, List, Optional
# from datetime import datetime
# import uuid

# # ================= IMPORTS =================
# from ..ml.disease_detector import DiseaseDetector   # ✅ HYBRID ENGINE

# from ..ml.translator import translate_response
# from ..ml.audio_generator import generate_audio_response
# from ..config import get_settings
# from ..models.schemas import PredictionResponse
# from ..models.sql_models import Prediction
# from ..database import get_db
# from ..utils.logger import Logger
# from ..utils.pdf_generator import generate_prescription_pdf

# # ================= INIT =================
# router = APIRouter(tags=["Disease Detection"])
# settings = get_settings()
# logger = Logger(__name__)

# detector = DiseaseDetector()  # ✅ SINGLETON HYBRID ENGINE

# # ================= KNOWLEDGE BASE =================
# knowledge_base = {}
# try:
#     kb_path = Path(settings.KNOWLEDGE_BASE_PATH) / settings.KNOWLEDGE_BASE_FILE
#     if kb_path.exists():
#         with open(kb_path, encoding="utf-8") as f:
#             knowledge_base = json.load(f)
#         logger.success(f"✓ KB loaded from {kb_path}")
#     else:
#         logger.warning("⚠ Knowledge base not found")
# except Exception as e:
#     logger.error(f"KB load error: {e}")

# # ================= HELPERS =================

# def get_treatment_for_disease(disease: str) -> List[str]:
#     """Fetches treatment steps with fallback."""
#     if disease in knowledge_base:
#         return knowledge_base[disease].get("treatment", ["Consult an agricultural expert."])
#     return ["Treatment information currently unavailable. Please consult a local expert."]

# def get_prevention_for_disease(disease: str, stage: str) -> List[str]:
#     """
#     Fetches prevention steps with crop-stage filtering.
#     ✅ MASTERSTROKE LOGIC: Filters harsh chemicals during sensitive stages.
#     """
#     if disease in knowledge_base:
#         all_preventions = knowledge_base[disease].get("prevention", [])
        
#         # --- FINAL STAGE-BASED FILTERING LOGIC ---
#         if stage.lower() in ["flowering", "fruiting"]:
#             # Filter out harsh chemical suggestions which might damage flowers/fruit/pollen
#             return [
#                 p for p in all_preventions 
#                 if "chemical" not in p.lower() 
#                 and "strong fungicide" not in p.lower()
#                 and "harsh" not in p.lower()
#             ]
        
#         return all_preventions
    
#     # Fallback if disease not found in KB
#     return ["Ensure field sanitation and consult an expert for specific preventative steps."]

# def filter_predictions_by_crop(predictions: Dict[str, float], crop_type: str) -> Dict[str, float]:
#     """
#     MATH MAGIC: Increases accuracy by filtering diseases relevant to the crop.
#     ✅ RETAINED FROM OLD CODE: Auto-detection logic for "Unknown" crop type.
#     """
#     if not predictions:
#         return {}
    
#     target_crop = ""
    
#     if crop_type and crop_type != "Unknown":
#         target_crop = crop_type.lower()
#     else:
#         # Auto-detect crop from top prediction (FROM OLD CODE)
#         if predictions:
#             top_raw = max(predictions, key=predictions.get)
#             if "___" in top_raw:
#                 target_crop = top_raw.split("___")[0].lower()
#             else:
#                 return predictions  # Return as-is if no crop delimiter

#     filtered = {d: p for d, p in predictions.items() if target_crop in d.lower()}
    
#     if not filtered:
#         return predictions  # Fallback to original predictions

#     total_crop_confidence = sum(filtered.values())
    
#     if total_crop_confidence == 0:
#         return filtered

#     # Normalize to sum to 1
#     normalized_predictions = {
#         d: round(p / total_crop_confidence, 4)
#         for d, p in filtered.items()
#     }

#     return normalized_predictions

# async def process_gemini_response(
#     gemini_result: Dict[str, Any],   # ✅ ADD THIS
#     crop_stage: str,
#     language: str,
#     file_path: str,
#     farmer_id: str,
#     latitude: Optional[float],
#     longitude: Optional[float],
#     db: Session
# ) -> Dict[str, Any]:
#     """
#     Process Gemini response to ensure full feature compatibility.
#     This adds the missing functionality (DB, PDF, Audio, Translation) to Gemini path.
#     """
#     try:
#         # Extract disease info from Gemini
#         disease = gemini_result.get("disease", "Unknown")
#         confidence = gemini_result.get("confidence", 0.0)
#         gemini_treatment = gemini_result.get("treatment", [])
#         gemini_prevention = gemini_result.get("prevention", [])
        
#         # Use our knowledge base for treatment/prevention if Gemini doesn't provide it
#         treatment = gemini_treatment if gemini_treatment else get_treatment_for_disease(disease)
#         prevention = gemini_prevention if gemini_prevention else get_prevention_for_disease(disease, crop_stage)
        
#         # Apply crop-stage filtering to Gemini's prevention if needed
#         if not gemini_prevention:
#             prevention = get_prevention_for_disease(disease, crop_stage)
        
#         # Translation
#         disease_clean = disease.replace("___", " ").replace("_", " ")
#         disease_trans = disease_clean
        
#         if language not in ["en", "en-US"]:
#             treatment = [translate_response(t, language) for t in treatment]
#             prevention = [translate_response(p, language) for p in prevention]
#             disease_trans = translate_response(disease_clean, language)
        
#         # Audio Generation
#         audio_url = None
#         try:
#             treatment_summary = treatment[0] if treatment else "Consult expert."
#             audio_script = f"Detected {disease_trans}. {treatment_summary}"
#             audio_filename = await generate_audio_response(audio_script, language)
#             if audio_filename:
#                 audio_url = f"/uploads/{audio_filename}"
#         except Exception as audio_e:
#             logger.error(f"Audio Generation Failed for Gemini: {audio_e}")
        
#         # Database Save (CRITICAL for analytics)
#         prediction = None
#         try:
#             prediction = Prediction(
#                 farmer_id=farmer_id,
#                 disease=disease,
#                 confidence=float(confidence),
#                 latitude=latitude,
#                 longitude=longitude,
#                 crop_stage=crop_stage,
#                 top5={},  # Gemini doesn't provide multiple predictions
#                 treatment=treatment,
#                 prevention=prevention,
#                 image_path=str(file_path),
#                 knowledge_source="gemini"  # Track source
#             )
#             db.add(prediction)
#             db.commit()
#             db.refresh(prediction)
#             logger.success(f"Gemini analytics saved for ID: {farmer_id}")
#         except Exception as db_e:
#             logger.error(f"DB Save Failed for Gemini: {db_e}")
        
#         # PDF Generation
#         pdf_url = None
#         try:
#             if prediction:
#                 pdf_data = {
#                     "farmer_id": farmer_id,
#                     "disease": disease_trans,
#                     "confidence": confidence,
#                     "treatment": treatment,
#                     "prevention": prevention,
#                     "audio_url": audio_url,
#                     "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
#                     "image_path": str(file_path),
#                     "language": language,
#                     "crop_stage": crop_stage,
#                     "knowledge_source": "Gemini Vision AI"
#                 }
                
#                 filename_base = str(prediction.id)
#                 pdf_url = generate_prescription_pdf(pdf_data, filename_base)
#                 logger.success(f"Gemini PDF Created: {pdf_url}")
#         except Exception as pdf_e:
#             logger.error(f"PDF Generation Failed for Gemini: {pdf_e}")
        
#         return {
#             "disease": disease,
#             "confidence": confidence,
#             "treatment": treatment,
#             "prevention": prevention,
#             "language": language,
#             "audio_url": audio_url,
#             "pdf_url": pdf_url,
#             "crop_stage": crop_stage,
#             "all_predictions": {},  # Gemini doesn't provide this
#             "filtered_predictions": {},
#             "knowledge_source": "GEMINI_VISION_AI",
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Gemini processing error: {e}")
#         # Fallback to returning Gemini result as-is
#         return {
#             **gemini_result,
#             "language": language,
#             "audio_url": None,
#             "pdf_url": None,
#             "crop_stage": crop_stage,
#             "all_predictions": {},
#             "filtered_predictions": {},
#             "success": True
#         }

# # ================= API ENDPOINT =================

# @router.post("/predict", response_model=PredictionResponse)
# async def predict_disease(
#     file: UploadFile = File(...),
#     crop_type: str = Form("Unknown"),
#     language: str = Form("en"),
#     latitude: Optional[float] = Form(None),
#     longitude: Optional[float] = Form(None),
#     farmer_id: str = Form("guest_user"),
#     crop_stage: str = Form("Vegetative"),
#     db: Session = Depends(get_db),
# ):
#     # ---------- Validate ----------
#     if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
#         raise HTTPException(status_code=400, detail="Only JPG/PNG images allowed")

#     # ---------- Save Image ----------
#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)

#     filename = f"{uuid.uuid4()}_{file.filename}"
#     file_path = upload_dir / filename

#     try:
#         with open(file_path, "wb") as f:
#             while chunk := await file.read(1024 * 1024):
#                 f.write(chunk)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"File save error: {e}")

#     # ---------- DUAL-CORE AI DETECTION (Primary) ----------
#     logger.info("🚀 Running Dual-Core Disease Detection Engine (Dual YOLO)")

#     try:
#         res = dual_bot.predict(str(file_path))
#     except Exception as e:
#         logger.error(f"Dual engine failed: {e}")
#         raise HTTPException(status_code=500, detail=f"AI inference failed: {e}")

#     # If dual YOLO failed or low confidence -> use Gemini fallback
#     if not res.get("success") or res.get("confidence", 0) < 0.4:
#         logger.info("Dual engine insufficient, invoking Gemini fallback")
#         try:
#             gemini_raw = await detector._run_gemini_analysis(str(file_path), crop_type)
#             full_response = await process_gemini_response(
#                 gemini_result=gemini_raw,
#                 crop_stage=crop_stage,
#                 language=language,
#                 file_path=file_path,
#                 farmer_id=farmer_id,
#                 latitude=latitude,
#                 longitude=longitude,
#                 db=db
#             )
#             return full_response
#         except Exception as e:
#             logger.error(f"Gemini fallback failed: {e}")
#             raise HTTPException(status_code=500, detail=f"AI inference failed: {e}")

#     # Map dual engine result into existing `result` shape for downstream processing
#     result = {
#         "success": True,
#         "disease": res.get("disease"),
#         "confidence": res.get("confidence"),
#         "knowledge_source": "Edge-AI"
#     }

#     # ---------- SMART ADVISORY LOGIC (TEXT LLM FOR YOLO DETECTIONS) ----------
#     # If YOLO detected -> Get smart advisory from LLM (text)
#     if result.get("knowledge_source") == "LOCAL_KNOWLEDGE_BASE" or "Edge-AI" in str(result.get("knowledge_source")):
#         disease_name = result.get("disease", "")
        
#         # ✅ SMART MOVE: Use OpenRouter for text advisory even for YOLO detections
#         try:
#             from ..ml.chatbot_agent import process_chat_without_image
#             advisory_prompt = f"Provide a short 3-step treatment for {disease_name} in {language} language."
#             llm_advisory = process_chat_without_image(advisory_prompt)
            
#             if llm_advisory.get("success"):
#                 # Use LLM's fresh advisory instead of Knowledge Base
#                 result["treatment"] = llm_advisory.get("reply")
#                 logger.success(f"📝 LLM Advisory updated for {disease_name}")
#         except Exception as e:
#             logger.warning(f"LLM advisory failed, falling back to Knowledge Base: {e}")
#             # Fallback to Knowledge Base if LLM text fails

#     # ---------- GEMINI PATH WITH FULL FEATURES ----------
#     if result.get("knowledge_source") == "GEMINI_VISION_AI":
#         logger.success("🌐 Gemini Vision response - processing with full features")
        
#         # Process Gemini response to include all features (DB, PDF, Audio, etc.)
#         full_response = await process_gemini_response(
#             gemini_result=result,
#             crop_stage=crop_stage,
#             language=language,
#             file_path=file_path,
#             farmer_id=farmer_id,
#             latitude=latitude,
#             longitude=longitude,
#             db=db
#         )
        
#         return full_response

#     # ---------- YOLO FALLBACK PATH ----------
#     if not result.get("success"):
#         # Try one more fallback: direct YOLO classification
#         logger.warning("Hybrid engine failed, trying direct YOLO...")
#         try:
#             from ..ml.disease_classifier import classify_disease
#             yolo_result = classify_disease(str(file_path))
#             if yolo_result.get("success", False):
#                 result = yolo_result
#             else:
#                 raise HTTPException(status_code=500, detail="All AI models failed")
#         except Exception as yolo_e:
#             logger.error(f"YOLO fallback also failed: {yolo_e}")
#             raise HTTPException(status_code=500, detail="AI inference failed completely")

#     # Process YOLO result
#     all_predictions = result.get("all_predictions", {})
    
#     # Apply crop filtering with auto-detection (FROM OLD CODE)
#     filtered = filter_predictions_by_crop(all_predictions, crop_type)
    
#     # Get top prediction
#     if filtered:
#         top_disease = max(filtered, key=filtered.get)
#         confidence = filtered[top_disease]
#     else:
#         top_disease = result.get("disease", "Uncertain")
#         confidence = result.get("confidence", 0.0)

#     disease = top_disease
#     treatment = get_treatment_for_disease(disease)
#     prevention = get_prevention_for_disease(disease, crop_stage)

#     # ---------- Translation ----------
#     disease_clean = disease.replace("___", " ").replace("_", " ")
#     disease_trans = disease_clean

#     if language not in ["en", "en-US"]:
#         treatment = [translate_response(t, language) for t in treatment]
#         prevention = [translate_response(p, language) for p in prevention]
#         disease_trans = translate_response(disease_clean, language)

#     # ---------- Audio ----------
#     audio_url = None
#     try:
#         treatment_summary = treatment[0] if treatment else "Consult expert."
#         audio_script = f"Detected {disease_trans}. {treatment_summary}"
#         audio_file = await generate_audio_response(audio_script, language)
#         if audio_file:
#             audio_url = f"/uploads/{audio_file}"
#     except Exception as e:
#         logger.error(f"TTS failed: {e}")

#     # ---------- DB Save ----------
#     prediction = None
#     try:
#         prediction = Prediction(
#             farmer_id=farmer_id,
#             disease=disease,
#             confidence=float(confidence),
#             latitude=latitude,
#             longitude=longitude,
#             crop_stage=crop_stage,
#             top5=filtered,
#             treatment=treatment,
#             prevention=prevention,
#             image_path=str(file_path),
#             knowledge_source="yolo"  # Track source
#         )
#         db.add(prediction)
#         db.commit()
#         db.refresh(prediction)
#         logger.success(f"YOLO analytics saved for ID: {farmer_id}")
#     except Exception as e:
#         logger.error(f"DB save failed: {e}")




#     # ---------- PDF ----------
#     pdf_url = None
#     try:
#         if prediction:
#             pdf_data = {
#                 "farmer_id": farmer_id,
#                 "disease": disease_trans,
#                 "confidence": confidence,
#                 "treatment": treatment,
#                 "prevention": prevention,
#                 "audio_url": audio_url,
#                 "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
#                 "image_path": str(file_path),
#                 "language": language,
#                 "crop_stage": crop_stage,
#                 "knowledge_source": "YOLOv8 + Knowledge Base"
#             }
            
#             pdf_url = generate_prescription_pdf(pdf_data, str(prediction.id))
#             logger.success(f"YOLO PDF Created: {pdf_url}")
#     except Exception as e:
#         logger.error(f"PDF generation failed: {e}")

#     # ---------- FINAL RESPONSE ----------
#     return {
#         "disease": disease,
#         "confidence": confidence,
#         "treatment": treatment,
#         "prevention": prevention,
#         "language": language,
#         "audio_url": audio_url,
#         "pdf_url": pdf_url,
#         "crop_stage": crop_stage,
#         "all_predictions": all_predictions,
#         "filtered_predictions": filtered,
#         "knowledge_source": "YOLOv8_FALLBACK",
#         "success": True,
#     }











# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# WEAPON 1: The Core Intelligence
# FEATURES: 
#   - AI Inference (YOLOv8)
#   - Math-Based Confidence Boosting
#   - Fallback Mechanisms (Safe defaults if DB/Audio fails)
#   - Professional PDF Prescription Generation
# """

# from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
# from sqlalchemy.orm import Session
# from pathlib import Path
# import json
# from typing import Dict, Any, List, Optional
# from datetime import datetime # ✅ Required for PDF Timestamp

# # --- Imports ---
# from ..ml.disease_classifier import classify_disease
# from ..ml.translator import translate_response
# from ..ml.audio_generator import generate_audio_response
# from ..config import get_settings
# from ..models.schemas import PredictionResponse 
# from ..models.sql_models import Prediction
# from ..database import get_db
# from ..utils.logger import Logger 
# # 👇 PDF Generator Import
# from ..utils.pdf_generator import generate_prescription_pdf

# # --- Initialization ---
# router = APIRouter(tags=["disease"]) 
# settings = get_settings()
# logger = Logger(__name__)

# # --- ROBUST PATH FINDING FOR KNOWLEDGE BASE ---
# try:
#     current_file = Path(__file__).resolve()
#     # Adjust logic to find diseases.json relative to this file
#     kb_path = current_file.parent.parent.parent.parent / "ml/knowledge_base/diseases.json"
    
#     knowledge_base = {}
    
#     if kb_path.exists():
#         with open(kb_path, encoding='utf-8') as f:
#             knowledge_base = json.load(f)
#         logger.success(f"✅ Knowledge base loaded from: {kb_path}")
#     else:
#         logger.warning(f"❌ KB File MISSING at: {kb_path}")

# except Exception as e:
#     logger.error(f"❌ Critical Path Error: {e}")

# # --- Helper Functions ---

# def get_treatment_for_disease(disease_name: str) -> List[str]:
#     """
#     Fetches treatment steps.
#     ✅ FALLBACK: Returns a default message if disease not found in JSON.
#     """
#     if disease_name in knowledge_base:
#         return knowledge_base[disease_name].get("treatment", ["Consult an agricultural expert."])
#     return ["Treatment information currently unavailable. Please consult a local expert."]

# def get_prevention_for_disease(disease_name: str, stage: str) -> List[str]:
#     """
#     Fetches prevention steps AND applies final filtering based on Crop Stage.
#     ✅ MASTERSTROKE LOGIC: Filters harsh chemicals during sensitive stages.
#     """
#     if disease_name in knowledge_base:
#         all_preventions = knowledge_base[disease_name].get("prevention", [])
        
#         # --- FINAL STAGE-BASED FILTERING LOGIC ---
#         if stage.lower() == "flowering" or stage.lower() == "fruiting":
#             # Filter: Filter out harsh chemical suggestions which might damage flowers/fruit/pollen.
#             return [p for p in all_preventions if "chemical" not in p.lower() and "strong fungicide" not in p.lower()]
        
#         return all_preventions
    
#     # Fallback if disease not found in KB
#     return ["Ensure field sanitation and consult an expert for specific preventative steps."]

# def filter_predictions_by_crop(predictions: Dict[str, float], crop_type: str) -> Dict[str, float]:
#     """
#     MATH MAGIC: Increases accuracy by filtering diseases relevant to the crop.
#     """
#     target_crop = ""
    
#     if crop_type and crop_type != "Unknown":
#         target_crop = crop_type.lower()
#     else:
#         # Auto-detect crop from top prediction
#         if predictions:
#             top_raw = max(predictions, key=predictions.get)
#             if "___" in top_raw:
#                 target_crop = top_raw.split("___")[0].lower() 
#             else:
#                 return predictions 

#     filtered = {d: p for d, p in predictions.items() if target_crop in d.lower()}
    
#     if not filtered:
#         return predictions 

#     total_crop_confidence = sum(filtered.values())
    
#     if total_crop_confidence == 0:
#         return filtered

#     normalized_predictions = {
#         d: round(p / total_crop_confidence, 4) 
#         for d, p in filtered.items()
#     }

#     return normalized_predictions

# def get_new_top_prediction(filtered_predictions: Dict[str, float]) -> Dict[str, Any]:
#     """Finds the winner after filtering"""
#     if not filtered_predictions:
#         return {"disease": "Uncertain", "confidence": 0.0}
#     top_disease = max(filtered_predictions, key=filtered_predictions.get)
#     return {"disease": top_disease, "confidence": filtered_predictions[top_disease]}

# # --- MAIN API ENDPOINT ---

# @router.post("/predict", response_model=PredictionResponse)
# async def predict_disease(
#     file: UploadFile = File(...),
#     crop_type: str = Form("Unknown"),
#     language: str = Form("en"),
#     latitude: Optional[float] = Form(None), # ✅ GPS Data
#     longitude: Optional[float] = Form(None), # ✅ GPS Data
#     farmer_id: str = Form("guest_user"), 
#     crop_stage: str = Form("Vegetative"), # ✅ NEW: Crop Stage Input
#     db: Session = Depends(get_db)
# ):
#     # 1. Validate File Type
#     if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
#         raise HTTPException(status_code=400, detail="Only JPG/PNG files allowed")

#     # 2. Save File (Permanent for History/PDF)
#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)
    
#     # Use unique name to prevent overwriting
#     import uuid
#     unique_filename = f"{uuid.uuid4()}_{file.filename}"
#     file_path = upload_dir / unique_filename
        
#     try:
#         with open(file_path, "wb") as buffer:
#             while chunk := await file.read(1024 * 1024):
#                 buffer.write(chunk)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"File save error: {e}")
        
#     try:
#         # 3. Run AI Inference
#         logger.info(f"Classifying image: {file_path}")
#         raw_result = classify_disease(str(file_path))
        
#         # ✅ FALLBACK: If AI fails, return error gracefully
#         if not raw_result.get("success", False):
#              return {
#                  "disease": "Error",
#                  "confidence": 0.0,
#                  "treatment": ["AI Model Failed to process image."],
#                  "success": False
#              }

#         # 4. Apply Math Logic
#         filtered_predictions = filter_predictions_by_crop(raw_result["all_predictions"], crop_type)
#         new_top = get_new_top_prediction(filtered_predictions)
#         final_disease = new_top["disease"]
#         final_confidence = new_top["confidence"]
        
#         # 5. Fetch Content (Stage-Aware Prevention Logic APPLIED HERE)
#         treatment = get_treatment_for_disease(final_disease)
#         # 👇 CRITICAL FIX: Prevention now uses stage logic
#         prevention = get_prevention_for_disease(final_disease, crop_stage) 
        
#         # 6. Translation
#         audio_url = None
#         final_disease_clean = final_disease.replace("___", " ").replace("_", " ")
#         final_disease_trans = final_disease_clean
        
#         if language != "en" and language != "en-US":
#             treatment = [translate_response(t, language) for t in treatment]
#             prevention = [translate_response(p, language) for p in prevention]
#             final_disease_trans = translate_response(final_disease_clean, language)

#         # 7. Generate Audio (With Try-Except Fallback)
#         try:
#             treatment_summary = treatment[0] if treatment else "Consult expert."
#             audio_script = f"Detected {final_disease_trans}. {treatment_summary}"
            
#             audio_filename = await generate_audio_response(audio_script, language)
#             if audio_filename:
#                 audio_url = f"/uploads/{audio_filename}"
                
#         except Exception as audio_e:
#             logger.error(f"Audio Generation Failed: {audio_e}")

#         # 8. Database Save (All fields saved)
#         new_prediction = None
#         try:
#             new_prediction = Prediction(
#                 farmer_id=farmer_id, 
#                 disease=final_disease,
#                 confidence=float(final_confidence),
#                 latitude=latitude,   
#                 longitude=longitude, 
#                 crop_stage=crop_stage, # ✅ Saving the Stage
#                 top5=filtered_predictions,
#                 treatment=treatment,
#                 prevention=prevention,
#                 image_path=str(file_path) 
#             )
#             db.add(new_prediction)
#             db.commit()
#             db.refresh(new_prediction) 
#             logger.success(f"Analytics data saved for ID: {farmer_id}")
#         except Exception as db_e:
#             logger.error(f"DB Save Failed: {db_e}")

#         # 9. Generate Professional PDF
#         pdf_url = None
#         try:
#             if new_prediction:
#                 pdf_data = {
#                     "farmer_id": farmer_id,
#                     "disease": final_disease_trans,
#                     "confidence": final_confidence,
#                     "treatment": treatment,
#                     "prevention": prevention, # ✅ Passed to PDF
#                     "audio_url": audio_url,
#                     "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
#                     "image_path": str(file_path),
#                     "language": language,
#                     "crop_stage": crop_stage, # ✅ Passed to PDF
#                 }
                
#                 filename_base = str(new_prediction.id)
#                 logger.info("Generating PDF Prescription...")
#                 pdf_url = generate_prescription_pdf(pdf_data, filename_base)
#                 logger.success(f"PDF Created: {pdf_url}")
                
#         except Exception as pdf_e:
#             logger.error(f"PDF Generation Failed: {pdf_e}")

#         # 10. Final Response
#         return {
#             "disease": final_disease,
#             "confidence": final_confidence,
#             "treatment": treatment,
#             "prevention": prevention,
#             "language": language,
#             "audio_url": audio_url,
#             "pdf_url": pdf_url, 
#             "crop_stage": crop_stage, # ✅ Final Response field
#             "all_predictions": raw_result["all_predictions"],
#             "filtered_predictions": filtered_predictions,
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Prediction Logic Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
    
#     finally:
#         # Final block is now clean (no file deletion)
#         pass










# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# WEAPON 1: The Core Intelligence
# FEATURES: 
#   - AI Inference (YOLOv8)
#   - Math-Based Confidence Boosting
#   - Fallback Mechanisms (Safe defaults if DB/Audio fails)
#   - Professional PDF Prescription Generation
# """
# from typing import Optional
# from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
# from sqlalchemy.orm import Session
# from pathlib import Path
# import json
# from typing import Dict, Any, List, Optional
# from datetime import datetime # ✅ Required for PDF Timestamp

# # --- Imports ---
# from ..ml.disease_classifier import classify_disease
# from ..ml.translator import translate_response
# from ..ml.audio_generator import generate_audio_response
# from ..config import get_settings
# from ..models.schemas import PredictionResponse 
# from ..models.sql_models import Prediction
# from ..database import get_db
# from ..utils.logger import Logger 
# # 👇 PDF Generator Import
# from ..utils.pdf_generator import generate_prescription_pdf

# # --- Initialization ---
# router = APIRouter(tags=["disease"]) 
# settings = get_settings()
# logger = Logger(__name__)

# # --- ROBUST PATH FINDING FOR KNOWLEDGE BASE ---
# try:
#     current_file = Path(__file__).resolve()
#     # Adjust logic to find diseases.json relative to this file
#     kb_path = current_file.parent.parent.parent.parent / "ml/knowledge_base/diseases.json"
    
#     knowledge_base = {}
    
#     if kb_path.exists():
#         with open(kb_path, encoding='utf-8') as f:
#             knowledge_base = json.load(f)
#         logger.success(f"✅ Knowledge base loaded from: {kb_path}")
#     else:
#         logger.warning(f"❌ KB File MISSING at: {kb_path}")

# except Exception as e:
#     logger.error(f"❌ Critical Path Error: {e}")

# # --- Helper Functions (With Fallbacks) ---

# def get_treatment_for_disease(disease_name: str) -> List[str]:
#     """
#     Fetches treatment steps.
#     ✅ FALLBACK: Returns a default message if disease not found in JSON.
#     """
#     if disease_name in knowledge_base:
#         return knowledge_base[disease_name].get("treatment", ["Consult an agricultural expert."])
#     return ["Treatment information currently unavailable. Please consult a local expert."]

# def get_prevention_for_disease(disease_name: str) -> List[str]:
#     # app/routers/disease.py (Helper Functions Section)

# def get_prevention_for_disease(disease_name: str, stage: str) -> List[str]:
#     """
#     Fetches prevention steps AND applies final filtering based on Crop Stage.
#     """
#     if disease_name in knowledge_base:
#         all_preventions = knowledge_base[disease_name].get("prevention", [])
        
#         # --- FINAL STAGE-BASED FILTERING ---
#         # Logic: If the crop is in a sensitive stage (Flowering/Fruiting), filter out
#         # harsh chemical suggestions which might damage the reproductive cycle.
#         if stage.lower() == "flowering" or stage.lower() == "fruiting":
#             # Filter: Check for keywords like 'chemical', 'strong', 'synthetic'
#             return [p for p in all_preventions if "chemical" not in p.lower() and "strong fungicide" not in p.lower()]
        
#         # Logic: For Vegetative/Leafy stage, all general prevention is safe.
#         return all_preventions
    
#     # Fallback if disease not found in KB
#     return ["Ensure field sanitation and consult an expert for specific preventative steps."]

# def filter_predictions_by_crop(predictions: Dict[str, float], crop_type: str) -> Dict[str, float]:
#     """
#     MATH MAGIC: Increases accuracy by filtering diseases relevant to the crop.
#     """
#     target_crop = ""
    
#     if crop_type and crop_type != "Unknown":
#         target_crop = crop_type.lower()
#     else:
#         # Auto-detect crop from top prediction
#         if predictions:
#             top_raw = max(predictions, key=predictions.get)
#             if "___" in top_raw:
#                 target_crop = top_raw.split("___")[0].lower() 
#             else:
#                 return predictions 

#     filtered = {d: p for d, p in predictions.items() if target_crop in d.lower()}
    
#     if not filtered:
#         return predictions 

#     total_crop_confidence = sum(filtered.values())
    
#     if total_crop_confidence == 0:
#         return filtered

#     normalized_predictions = {
#         d: round(p / total_crop_confidence, 4) 
#         for d, p in filtered.items()
#     }

#     return normalized_predictions

# def get_new_top_prediction(filtered_predictions: Dict[str, float]) -> Dict[str, Any]:
#     """Finds the winner after filtering"""
#     if not filtered_predictions:
#         return {"disease": "Uncertain", "confidence": 0.0}
#     top_disease = max(filtered_predictions, key=filtered_predictions.get)
#     return {"disease": top_disease, "confidence": filtered_predictions[top_disease]}

# # --- MAIN API ENDPOINT ---

# @router.post("/predict", response_model=PredictionResponse)
# async def predict_disease(
#     file: UploadFile = File(...),
#     crop_type: str = Form("Unknown"),
#     language: str = Form("en"),
#     latitude: Optional[float] = Form(None), # ✅ GPS Data
#     longitude: Optional[float] = Form(None), # ✅ GPS Data
#     farmer_id: str = Form("guest_user"),         # ✅ String ID (Safe for SQLite)
#     crop_stage: str = Form("Vegetative"),
#     db: Session = Depends(get_db)
# ):
#     # 1. Validate File Type
#     if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
#         raise HTTPException(status_code=400, detail="Only JPG/PNG files allowed")

#     # 2. Save File (Permanent for History/PDF)
#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)
    
#     # Use unique name to prevent overwriting
#     import uuid
#     unique_filename = f"{uuid.uuid4()}_{file.filename}"
#     file_path = upload_dir / unique_filename
        
#     try:
#         with open(file_path, "wb") as buffer:
#             while chunk := await file.read(1024 * 1024):
#                 buffer.write(chunk)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"File save error: {e}")
        
#     try:
#         # 3. Run AI Inference
#         logger.info(f"Classifying image: {file_path}")
#         raw_result = classify_disease(str(file_path))
        
#         # ✅ FALLBACK: If AI fails, return error gracefully
#         if not raw_result.get("success", False):
#              return {
#                  "disease": "Error",
#                  "confidence": 0.0,
#                  "treatment": ["AI Model Failed to process image."],
#                  "success": False
#              }

#         # 4. Apply Math Logic
#         filtered_predictions = filter_predictions_by_crop(raw_result["all_predictions"], crop_type)
#         new_top = get_new_top_prediction(filtered_predictions)
#         final_disease = new_top["disease"]
#         final_confidence = new_top["confidence"]
        
#         # 5. Fetch Content (With KB Fallback)
#         treatment = get_treatment_for_disease(final_disease)
#         prevention = get_prevention_for_disease(final_disease)
        
#         # 6. Translation
#         audio_url = None
#         final_disease_clean = final_disease.replace("___", " ").replace("_", " ")
#         final_disease_trans = final_disease_clean
        
#         if language != "en" and language != "en-US":
#             treatment = [translate_response(t, language) for t in treatment]
#             prevention = [translate_response(p, language) for p in prevention]
#             final_disease_trans = translate_response(final_disease_clean, language)

#         # 7. Generate Audio (With Try-Except Fallback)
#         try:
#             treatment_summary = treatment[0] if treatment else "Consult expert."
#             audio_script = f"Detected {final_disease_trans}. {treatment_summary}"
            
#             audio_filename = await generate_audio_response(audio_script, language)
#             if audio_filename:
#                 audio_url = f"/uploads/{audio_filename}"
                
#         except Exception as audio_e:
#             logger.error(f"Audio Generation Failed: {audio_e}")
#             # Fallback: Proceed without audio

#         # 8. Save to Database
#         new_prediction = None
#         try:
#             new_prediction = Prediction(
#                 farmer_id=farmer_id, 
#                 disease=final_disease,
#                 confidence=float(final_confidence),
#                 latitude=latitude,   
#                 longitude=longitude, 
#                 top5=filtered_predictions,
#                 treatment=treatment,
#                 prevention=prevention,
#                 crop_stage=crop_stage,
#                 image_path=str(file_path) 
#             )
#             db.add(new_prediction)
#             db.commit()
#             db.refresh(new_prediction) # Get ID
#             logger.success(f"Data saved for ID: {farmer_id}")
#         except Exception as db_e:
#             logger.error(f"DB Save Failed: {db_e}")
#             # Fallback: Prediction continues even if DB save fails

#         # 9. Generate Professional PDF (With Try-Except Fallback)
#         pdf_url = None
#         try:
#             if new_prediction:
#                 pdf_data = {
#                     "farmer_id": farmer_id,
#                     "disease": final_disease_clean, # Use English/Clean name for PDF
#                     "confidence": final_confidence,
#                     "treatment": treatment,
#                     "prevention": prevention,
#                     "audio_url": audio_url,
#                     "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
#                     "image_path": str(file_path), # ✅ Correctly passing image path
#                     "language": language
#                 }
                
#                 filename_base = str(new_prediction.id)
                
#                 logger.info("Generating PDF Prescription...")
#                 pdf_url = generate_prescription_pdf(pdf_data, filename_base)
#                 logger.success(f"PDF Created: {pdf_url}")
                
#         except Exception as pdf_e:
#             logger.error(f"PDF Generation Failed: {pdf_e}")
#             # Fallback: User gets result, just no PDF link

#         # 10. Final Response
#         return {
#             "disease": final_disease,
#             "confidence": final_confidence,
#             "treatment": treatment,
#             "prevention": prevention,
#             "language": language,
#             "audio_url": audio_url,
#             "pdf_url": pdf_url, 
#             "all_predictions": raw_result["all_predictions"],
#             "filtered_predictions": filtered_predictions,
#             "crop_stage": crop_stage,
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Prediction Logic Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
    
    # Note: No 'finally' block to delete image. 
    # We keep the image for the PDF and Database history.











# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# WEAPON 1: The Core Intelligence
# FEATURES: 
#   - AI Inference (YOLOv8)
#   - Math-Based Confidence Boosting
#   - Multi-Language Audio Generation
#   - Geo-Tagging for Heatmap
#   - Professional PDF Prescription Generation
# """

# from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
# from sqlalchemy.orm import Session
# from pathlib import Path
# import json
# from typing import Dict, Any, List, Optional
# from datetime import datetime # ✅ Date time for PDF timestamp

# # --- Imports ---
# from ..ml.disease_classifier import classify_disease
# from ..ml.translator import translate_response
# from ..ml.audio_generator import generate_audio_response
# from ..config import get_settings
# from ..models.schemas import PredictionResponse 
# from ..models.sql_models import Prediction
# from ..database import get_db
# from ..utils.logger import Logger 
# # 👇 NEW: Import PDF Generator
# from ..utils.pdf_generator import generate_prescription_pdf

# # --- Initialization ---
# router = APIRouter(tags=["disease"]) 
# settings = get_settings()
# logger = Logger(__name__)

# # --- ROBUST PATH FINDING FOR KNOWLEDGE BASE ---
# try:
#     current_file = Path(__file__).resolve()
#     # Points to app/ml/knowledge_base/diseases.json
#     kb_path = current_file.parent.parent.parent.parent / "ml/knowledge_base/diseases.json"
    
#     knowledge_base = {}
    
#     if kb_path.exists():
#         with open(kb_path, encoding='utf-8') as f:
#             knowledge_base = json.load(f)
#         logger.success(f"✅ Knowledge base loaded from: {kb_path}")
#     else:
#         logger.warning(f"❌ KB File MISSING at: {kb_path}")

# except Exception as e:
#     logger.error(f"❌ Critical Path Error: {e}")

# # --- Helper Functions ---

# def get_treatment_for_disease(disease_name: str) -> List[str]:
#     """Fetches treatment steps from JSON database"""
#     if disease_name in knowledge_base:
#         return knowledge_base[disease_name].get("treatment", ["Consult an expert."])
#     return ["Treatment information currently unavailable."]

# def get_prevention_for_disease(disease_name: str) -> List[str]:
#     """Fetches prevention steps from JSON database"""
#     if disease_name in knowledge_base:
#         return knowledge_base[disease_name].get("prevention", [])
#     return []

# def filter_predictions_by_crop(predictions: Dict[str, float], crop_type: str) -> Dict[str, float]:
#     """
#     MATH MAGIC: Increases accuracy by filtering diseases relevant to the crop 
#     and re-normalizing probabilities.
#     """
#     target_crop = ""
    
#     if crop_type and crop_type != "Unknown":
#         target_crop = crop_type.lower()
#     else:
#         # Auto-detect crop from top prediction name (e.g. "Tomato___Blight" -> "tomato")
#         if predictions:
#             top_raw = max(predictions, key=predictions.get)
#             if "___" in top_raw:
#                 target_crop = top_raw.split("___")[0].lower() 
#             else:
#                 return predictions 

#     # Filter dictionary
#     filtered = {d: p for d, p in predictions.items() if target_crop in d.lower()}
    
#     if not filtered:
#         return predictions 

#     # Re-calculate percentages (Math Boost)
#     total_crop_confidence = sum(filtered.values())
    
#     if total_crop_confidence == 0:
#         return filtered

#     normalized_predictions = {
#         d: round(p / total_crop_confidence, 4) 
#         for d, p in filtered.items()
#     }

#     return normalized_predictions

# def get_new_top_prediction(filtered_predictions: Dict[str, float]) -> Dict[str, Any]:
#     """Finds the winner after math filtering"""
#     if not filtered_predictions:
#         return {"disease": "Uncertain", "confidence": 0.0}
#     top_disease = max(filtered_predictions, key=filtered_predictions.get)
#     return {"disease": top_disease, "confidence": filtered_predictions[top_disease]}

# # --- MAIN API ENDPOINT ---

# @router.post("/predict", response_model=PredictionResponse)
# async def predict_disease(
#     file: UploadFile = File(...),
#     crop_type: str = Form("Unknown"),
#     language: str = Form("en"),
#     latitude: Optional[float] = Form(None), # ✅ GPS Data
#     longitude: Optional[float] = Form(None), # ✅ GPS Data
#     farmer_id: str = Form("guest_user"),     # ✅ String ID (No UUID crash)
#     db: Session = Depends(get_db)
# ):
#     # 1. Validate File Type
#     if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
#         raise HTTPException(status_code=400, detail="Only JPG/PNG files allowed")

#     # 2. Save Temp File
#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)
#     file_path = upload_dir / f"temp_{file.filename}"
        
#     try:
#         with open(file_path, "wb") as buffer:
#             while chunk := await file.read(1024 * 1024):
#                 buffer.write(chunk)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"File save error: {e}")
        
#     try:
#         # 3. Run AI Inference
#         logger.info(f"Classifying image: {file_path}")
#         raw_result = classify_disease(str(file_path))
        
#         if not raw_result.get("success", False):
#              return {
#                  "disease": "Error",
#                  "confidence": 0.0,
#                  "treatment": ["AI Model Failed"],
#                  "success": False
#              }

#         # 4. Apply Math Logic
#         filtered_predictions = filter_predictions_by_crop(raw_result["all_predictions"], crop_type)
#         new_top = get_new_top_prediction(filtered_predictions)
#         final_disease = new_top["disease"]
#         final_confidence = new_top["confidence"]
        
#         # 5. Fetch Treatment Info
#         treatment = get_treatment_for_disease(final_disease)
#         prevention = get_prevention_for_disease(final_disease)
        
#         # 6. Translate Content (If language is not English)
#         audio_url = None
#         final_disease_clean = final_disease.replace("___", " ").replace("_", " ")
        
#         if language != "en" and language != "en-US":
#             treatment = [translate_response(t, language) for t in treatment]
#             prevention = [translate_response(p, language) for p in prevention]
#             final_disease_trans = translate_response(final_disease_clean, language)
#         else:
#             final_disease_trans = final_disease_clean

#         # 7. Generate Audio (TTS)
#         try:
#             treatment_summary = treatment[0] if treatment else "Consult expert."
#             audio_script = f"Detected {final_disease_trans}. {treatment_summary}"
            
#             # logger.info(f"Generating Audio for Lang: {language}")
#             audio_filename = await generate_audio_response(audio_script, language)
            
#             if audio_filename:
#                 audio_url = f"/uploads/{audio_filename}"
                
#         except Exception as audio_e:
#             logger.error(f"Audio Generation Failed: {audio_e}")

#         # 8. Save to Database (UPDATED FOR STRING ID)
#         new_prediction = None
#         try:
#             new_prediction = Prediction(
#                 farmer_id=farmer_id, # ✅ Direct String use kar rahe hain (Safe for SQLite)
#                 disease=final_disease,
#                 confidence=float(final_confidence),
#                 latitude=latitude,   # ✅ Heatmap Data
#                 longitude=longitude, # ✅ Heatmap Data
#                 top5=filtered_predictions,
#                 treatment=treatment,
#                 prevention=prevention,
#                 image_path=str(file_path)
#             )
#             db.add(new_prediction)
#             db.commit()
#             db.refresh(new_prediction) # ✅ ID fetch karne ke liye refresh kiya
#             logger.success(f"Analytics data saved for ID: {farmer_id}")
#         except Exception as db_e:
#             logger.error(f"DB Save Failed: {db_e}")

#         # 9. MASTERSTROKE: Generate Professional PDF 📄
#         pdf_url = None
#         try:
#             if new_prediction:
#                 pdf_data = {
#     "farmer_id": farmer_id,
#     "disease": final_disease_trans,
#     "confidence": final_confidence,
#     "treatment": treatment,
#     "audio_url": audio_url,
#     "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
#     "image_path": str(file_path)     # 👈 NEW LINE (VERY IMPORTANT)
# }

#                 # Use DB ID for unique filename
#                 filename_base = str(new_prediction.id)
                
#                 logger.info("Generating PDF Prescription...")
#                 pdf_url = generate_prescription_pdf(pdf_data, filename_base)
#                 logger.success(f"PDF Created: {pdf_url}")
                
#         except Exception as pdf_e:
#             logger.error(f"PDF Generation Failed: {pdf_e}")

#         # 10. Final Response
#         return {
#             "disease": final_disease,
#             "confidence": final_confidence,
#             "treatment": treatment,
#             "prevention": prevention,
#             "language": language,
#             "audio_url": audio_url,
#             "pdf_url": pdf_url, # ✅ Frontend ko PDF link bhej rahe hain
#             "all_predictions": raw_result["all_predictions"],
#             "filtered_predictions": filtered_predictions,
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Prediction Logic Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
    
    # finally:
    #     # Clean up temp file to save space
    #     if file_path.exists():
    #         file_path.unlink()








# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# FEATURES: Math-Based Confidence Boosting + Audio + Geo-Tagging + Robust Pathing
# """

# from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
# from sqlalchemy.orm import Session
# from pathlib import Path
# import json
# from typing import Dict, Any, List, Optional
# from datetime import datetime

# # --- Imports ---
# from ..ml.disease_classifier import classify_disease
# from ..ml.translator import translate_response
# from ..ml.audio_generator import generate_audio_response
# from ..config import get_settings
# from ..models.schemas import PredictionResponse 
# from ..models.sql_models import Prediction
# from ..database import get_db
# from ..utils.logger import Logger 
# from ..utils.pdf_generator import generate_prescription_pdf

# # --- Initialization ---
# router = APIRouter(tags=["disease"]) 
# settings = get_settings()
# logger = Logger(__name__)

# # --- ROBUST PATH FINDING ---
# try:
#     current_file = Path(__file__).resolve()
#     # Ensure this path points correctly to your diseases.json
#     kb_path = current_file.parent.parent.parent.parent / "ml/knowledge_base/diseases.json"
    
#     knowledge_base = {}
    
#     if kb_path.exists():
#         with open(kb_path, encoding='utf-8') as f:
#             knowledge_base = json.load(f)
#         logger.success(f"✅ Knowledge base loaded from: {kb_path}")
#     else:
#         logger.warning(f"❌ KB File MISSING at: {kb_path}")

# except Exception as e:
#     logger.error(f"❌ Critical Path Error: {e}")

# # --- Helper Functions ---
# def get_treatment_for_disease(disease_name: str) -> List[str]:
#     if disease_name in knowledge_base:
#         return knowledge_base[disease_name].get("treatment", ["Consult an expert."])
#     return ["Treatment information currently unavailable."]

# def get_prevention_for_disease(disease_name: str) -> List[str]:
#     if disease_name in knowledge_base:
#         return knowledge_base[disease_name].get("prevention", [])
#     return []

# def filter_predictions_by_crop(predictions: Dict[str, float], crop_type: str) -> Dict[str, float]:
#     """
#     Filters predictions by crop AND normalizes probabilities.
#     """
#     target_crop = ""
    
#     if crop_type and crop_type != "Unknown":
#         target_crop = crop_type.lower()
#     else:
#         if predictions:
#             top_raw = max(predictions, key=predictions.get)
#             if "___" in top_raw:
#                 target_crop = top_raw.split("___")[0].lower() 
#             else:
#                 return predictions 

#     filtered = {d: p for d, p in predictions.items() if target_crop in d.lower()}
    
#     if not filtered:
#         return filtered # Return empty or original depending on logic, here returning filtered empty dict is safer

#     total_crop_confidence = sum(filtered.values())
    
#     if total_crop_confidence == 0:
#         return filtered

#     normalized_predictions = {
#         d: round(p / total_crop_confidence, 4) 
#         for d, p in filtered.items()
#     }

#     return normalized_predictions

# def get_new_top_prediction(filtered_predictions: Dict[str, float]) -> Dict[str, Any]:
#     if not filtered_predictions:
#         return {"disease": "Uncertain", "confidence": 0.0}
#     top_disease = max(filtered_predictions, key=filtered_predictions.get)
#     return {"disease": top_disease, "confidence": filtered_predictions[top_disease]}

# # --- Endpoints ---

# @router.post("/predict", response_model=PredictionResponse)
# async def predict_disease(
#     file: UploadFile = File(...),
#     crop_type: str = Form("Unknown"),
#     language: str = Form("en"),
#     latitude: Optional[float] = Form(None),
#     longitude: Optional[float] = Form(None),
#     farmer_id: str = Form("guest_user"),
#     db: Session = Depends(get_db)
# ):
#     # 1. Validate & Save File
#     if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
#         raise HTTPException(status_code=400, detail="Only JPG/PNG files allowed")

#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)
#     file_path = upload_dir / f"temp_{file.filename}"
        
#     try:
#         with open(file_path, "wb") as buffer:
#             while chunk := await file.read(1024 * 1024):
#                 buffer.write(chunk)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"File save error: {e}")
        
#     try:
#         # 2. AI Inference
#         logger.info(f"Classifying image: {file_path}")
#         raw_result = classify_disease(str(file_path))
        
#         if not raw_result.get("success", False):
#              return {
#                  "disease": "Error",
#                  "confidence": 0.0,
#                  "treatment": ["AI Model Failed"],
#                  "success": False
#              }

#         # 3. Logic: Math Boost
#         filtered_predictions = filter_predictions_by_crop(raw_result["all_predictions"], crop_type)
#         new_top = get_new_top_prediction(filtered_predictions)
#         final_disease = new_top["disease"]
#         final_confidence = new_top["confidence"]
        
#         # 4. Knowledge Base
#         treatment = get_treatment_for_disease(final_disease)
#         prevention = get_prevention_for_disease(final_disease)
        
#         # 5. Translation
#         audio_url = None
#         final_disease_clean = final_disease.replace("___", " ").replace("_", " ")
        
#         if language != "en" and language != "en-US":
#             treatment = [translate_response(t, language) for t in treatment]
#             prevention = [translate_response(p, language) for p in prevention]
#             final_disease_trans = translate_response(final_disease_clean, language)
#         else:
#             final_disease_trans = final_disease_clean

#         # 6. Audio Generation
#         try:
#             treatment_summary = treatment[0] if treatment else "Consult expert."
#             audio_script = f"Detected {final_disease_trans}. {treatment_summary}"
            
#             # logger.info(f"Generating Audio for Lang: {language}")
#             audio_filename = await generate_audio_response(audio_script, language)
            
#             if audio_filename:
#                 audio_url = f"/uploads/{audio_filename}"
                
#         except Exception as audio_e:
#             logger.error(f"Audio Generation Failed: {audio_e}")

#         # 7. Database Save (Simplified for String IDs)
#         try:
#             new_prediction = Prediction(
#                 farmer_id=farmer_id, # Direct String use kar rahe hain
#                 disease=final_disease,
#                 confidence=float(final_confidence),
#                 latitude=latitude,   # ✅ Heatmap ke liye zaroori
#                 longitude=longitude, # ✅ Heatmap ke liye zaroori
#                 top5=filtered_predictions,
#                 treatment=treatment,
#                 prevention=prevention,
#                 image_path=str(file_path)
#             )
#             db.add(new_prediction)
#             db.commit()
#             logger.success(f"Analytics data saved for ID: {farmer_id}")
#         except Exception as db_e:
#             logger.error(f"DB Save Failed: {db_e}")

#         return {
#             "disease": final_disease,
#             "confidence": final_confidence,
#             "treatment": treatment,
#             "prevention": prevention,
#             "language": language,
#             "audio_url": audio_url,
#             "all_predictions": raw_result["all_predictions"],
#             "filtered_predictions": filtered_predictions,
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Prediction Logic Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
    
#     finally:
#         if file_path.exists():
#             file_path.unlink()





# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# FEATURES: Math-Based Confidence Boosting + Audio + Geo-Tagging + Robust Pathing
# """

# from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
# from sqlalchemy.orm import Session
# from pathlib import Path
# import json
# import uuid  # ✅ Added for UUID conversion
# from typing import Dict, Any, List, Optional

# # --- Imports ---
# from ..ml.disease_classifier import classify_disease
# from ..ml.translator import translate_response
# from ..ml.audio_generator import generate_audio_response
# from ..config import get_settings
# from ..models.schemas import PredictionResponse 
# from ..models.sql_models import Prediction
# from ..database import get_db
# from ..utils.logger import Logger 

# # --- Initialization ---
# router = APIRouter(tags=["disease"]) 
# settings = get_settings()
# logger = Logger(__name__)

# # --- ✅ FIX: ROBUST PATH FINDING ---
# try:
#     current_file = Path(__file__).resolve()
#     # Adjust this depending on where your diseases.json actually is
#     # Assuming: app/routers/disease.py -> app/ml/knowledge_base/diseases.json
#     kb_path = current_file.parent.parent.parent.parent / "ml/knowledge_base/diseases.json"
    
#     knowledge_base = {}
    
#     if kb_path.exists():
#         with open(kb_path, encoding='utf-8') as f:
#             knowledge_base = json.load(f)
#         logger.success(f"✅ Knowledge base loaded from: {kb_path}")
#     else:
#         logger.warning(f"❌ KB File MISSING at: {kb_path}")

# except Exception as e:
#     logger.error(f"❌ Critical Path Error: {e}")

# # --- Helper Functions ---
# def get_treatment_for_disease(disease_name: str) -> List[str]:
#     if disease_name in knowledge_base:
#         return knowledge_base[disease_name].get("treatment", ["Consult an expert."])
#     return ["Treatment information currently unavailable."]

# def get_prevention_for_disease(disease_name: str) -> List[str]:
#     if disease_name in knowledge_base:
#         return knowledge_base[disease_name].get("prevention", [])
#     return []

# def validate_uuid(id_str: str) -> uuid.UUID:
#     """
#     Helper: Ensures the farmer_id is a valid UUID for the Database.
#     If 'guest_user' or invalid, returns a consistent dummy UUID.
#     """
#     try:
#         return uuid.UUID(id_str)
#     except ValueError:
#         # Return a fixed UUID for guests/demos so DB doesn't crash
#         return uuid.UUID('00000000-0000-0000-0000-000000000000')

# def filter_predictions_by_crop(predictions: Dict[str, float], crop_type: str) -> Dict[str, float]:
#     """
#     Filters predictions by crop AND normalizes probabilities.
#     This boosts confidence using Conditional Probability logic.
#     """
#     target_crop = ""
    
#     if crop_type and crop_type != "Unknown":
#         target_crop = crop_type.lower()
#     else:
#         if predictions:
#             top_raw = max(predictions, key=predictions.get)
#             if "___" in top_raw:
#                 target_crop = top_raw.split("___")[0].lower() 
#             else:
#                 return predictions 

#     filtered = {d: p for d, p in predictions.items() if target_crop in d.lower()}
    
#     if not filtered:
#         return predictions 

#     total_crop_confidence = sum(filtered.values())
    
#     if total_crop_confidence == 0:
#         return filtered

#     normalized_predictions = {
#         d: round(p / total_crop_confidence, 4) 
#         for d, p in filtered.items()
#     }

#     return normalized_predictions

# def get_new_top_prediction(filtered_predictions: Dict[str, float]) -> Dict[str, Any]:
#     if not filtered_predictions:
#         return {"disease": "Uncertain", "confidence": 0.0}
#     top_disease = max(filtered_predictions, key=filtered_predictions.get)
#     return {"disease": top_disease, "confidence": filtered_predictions[top_disease]}

# # --- Endpoints ---

# @router.post("/predict", response_model=PredictionResponse)
# async def predict_disease(
#     file: UploadFile = File(...),
#     crop_type: str = Form("Unknown"),
#     language: str = Form("en"),
#     latitude: Optional[float] = Form(None),
#     longitude: Optional[float] = Form(None),
#     farmer_id: str = Form("guest_user"),
#     db: Session = Depends(get_db)
# ):
#     # 1. Validate & Save File
#     if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
#         raise HTTPException(status_code=400, detail="Only JPG/PNG files allowed")

#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)
#     file_path = upload_dir / f"temp_{file.filename}"
        
#     try:
#         with open(file_path, "wb") as buffer:
#             while chunk := await file.read(1024 * 1024):
#                 buffer.write(chunk)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"File save error: {e}")
        
#     try:
#         # 2. AI Inference
#         logger.info(f"Classifying image: {file_path}")
#         raw_result = classify_disease(str(file_path))
        
#         if not raw_result.get("success", False):
#              return {
#                  "disease": "Error",
#                  "confidence": 0.0,
#                  "treatment": ["AI Model Failed"],
#                  "success": False
#              }

#         # 3. Logic: Math Boost Applied Here
#         filtered_predictions = filter_predictions_by_crop(raw_result["all_predictions"], crop_type)
#         new_top = get_new_top_prediction(filtered_predictions)
#         final_disease = new_top["disease"]
#         final_confidence = new_top["confidence"]
        
#         # 4. Knowledge Base
#         treatment = get_treatment_for_disease(final_disease)
#         prevention = get_prevention_for_disease(final_disease)
        
#         # 5. Translation
#         audio_url = None
#         final_disease_clean = final_disease.replace("___", " ").replace("_", " ")
        
#         if language != "en" and language != "en-US":
#             treatment = [translate_response(t, language) for t in treatment]
#             prevention = [translate_response(p, language) for p in prevention]
#             final_disease_trans = translate_response(final_disease_clean, language)
#         else:
#             final_disease_trans = final_disease_clean

#         # 6. Audio Generation
#         try:
#             treatment_summary = treatment[0] if treatment else "Consult expert."
#             audio_script = f"Detected {final_disease_trans}. {treatment_summary}"
            
#             logger.info(f"Generating Audio for Lang: {language}")
#             audio_filename = await generate_audio_response(audio_script, language)
            
#             if audio_filename:
#                 audio_url = f"/uploads/{audio_filename}"
                
#         except Exception as audio_e:
#             logger.error(f"Audio Generation Failed: {audio_e}")

#         # 7. Database Save (FIXED FOR UUID & LAT/LONG)
#         try:
#             # Convert string ID to UUID object to prevent DB crash
#             valid_farmer_uuid = validate_uuid(farmer_id)

#             new_prediction = Prediction(
#                 farmer_id=valid_farmer_uuid,
#                 disease=final_disease,
#                 confidence=float(final_confidence),
#                 latitude=latitude,   # ✅ Saving Location for Heatmap
#                 longitude=longitude, # ✅ Saving Location for Heatmap
#                 top5=filtered_predictions,
#                 treatment=treatment,
#                 prevention=prevention,
#                 image_path=str(file_path)
#             )
#             db.add(new_prediction)
#             db.commit()
#             logger.success("Analytics data saved to DB")
#         except Exception as db_e:
#             logger.error(f"DB Save Failed: {db_e}")

#         return {
#             "disease": final_disease,
#             "confidence": final_confidence,
#             "treatment": treatment,
#             "prevention": prevention,
#             "language": language,
#             "audio_url": audio_url,
#             "all_predictions": raw_result["all_predictions"],
#             "filtered_predictions": filtered_predictions,
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Prediction Logic Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
    
#     finally:
#         # Clean up temp file to save space
#         if file_path.exists():
#             file_path.unlink()


























# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# FEATURES: Math-Based Confidence Boosting + Audio + Geo-Tagging + Robust Pathing
# """

# from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
# from sqlalchemy.orm import Session
# from pathlib import Path
# import shutil
# import json
# import sys
# from typing import Dict, Any, List, Optional

# # --- Imports ---
# from ..ml.disease_classifier import classify_disease
# from ..ml.translator import translate_response, get_supported_languages
# from ..ml.audio_generator import generate_audio_response
# from ..config import get_settings
# from ..models.schemas import PredictionResponse 
# from ..models.sql_models import Prediction
# from ..database import get_db
# from ..utils.logger import Logger 

# # --- Initialization ---
# router = APIRouter(tags=["disease"]) 
# settings = get_settings()
# logger = Logger(__name__)

# # --- ✅ FIX: ROBUST PATH FINDING ---
# try:
#     current_file = Path(__file__).resolve()
#     project_root = current_file.parent.parent.parent.parent
#     kb_path = project_root / "ml/knowledge_base/diseases.json"
    
#     knowledge_base = {}
    
#     if kb_path.exists():
#         with open(kb_path, encoding='utf-8') as f:
#             knowledge_base = json.load(f)
#         logger.success(f"✅ Knowledge base loaded from: {kb_path}")
#     else:
#         logger.warning(f"❌ KB File MISSING at: {kb_path}")

# except Exception as e:
#     logger.error(f"❌ Critical Path Error: {e}")

# # --- Helper Functions ---
# def get_treatment_for_disease(disease_name: str) -> List[str]:
#     if disease_name in knowledge_base:
#         return knowledge_base[disease_name].get("treatment", ["Consult an expert."])
#     return ["Treatment information currently unavailable."]

# def get_prevention_for_disease(disease_name: str) -> List[str]:
#     if disease_name in knowledge_base:
#         return knowledge_base[disease_name].get("prevention", [])
#     return []

# def filter_predictions_by_crop(predictions: Dict[str, float], crop_type: str) -> Dict[str, float]:
#     """
#     Filters predictions by crop AND normalizes probabilities.
#     This boosts confidence using Conditional Probability logic.
#     """
    
#     # 1. Identify the Target Crop
#     target_crop = ""
    
#     if crop_type and crop_type != "Unknown":
#         target_crop = crop_type.lower()
#     else:
#         # Auto-detect crop from the highest probability raw prediction
#         # Example: If "Tomato___Early_Blight" is top, assume crop is "Tomato"
#         if predictions:
#             top_raw = max(predictions, key=predictions.get)
#             # Only split if format is "Crop___Disease"
#             if "___" in top_raw:
#                 target_crop = top_raw.split("___")[0].lower() 
#             else:
#                 return predictions # Cannot safely auto-detect

#     # 2. Filter dictionary to only include that crop's diseases
#     filtered = {d: p for d, p in predictions.items() if target_crop in d.lower()}
    
#     if not filtered:
#         return predictions # Fallback if filtering emptied everything

#     # 3. ✅ SMART RENORMALIZATION ( The Math Magic )
#     # Sum of probabilities for THIS crop only (e.g. sum of all Tomato scores)
#     total_crop_confidence = sum(filtered.values())
    
#     if total_crop_confidence == 0:
#         return filtered

#     # Recalculate percentages relative to this crop
#     # Example: Old (0.32) / Total_Tomato (0.40) = New (0.80 or 80%)
#     normalized_predictions = {
#         d: round(p / total_crop_confidence, 4) 
#         for d, p in filtered.items()
#     }

#     return normalized_predictions

# def get_new_top_prediction(filtered_predictions: Dict[str, float]) -> Dict[str, Any]:
#     if not filtered_predictions:
#         return {"disease": "Uncertain", "confidence": 0.0}
#     top_disease = max(filtered_predictions, key=filtered_predictions.get)
#     return {"disease": top_disease, "confidence": filtered_predictions[top_disease]}

# # --- Endpoints ---

# @router.post("/predict", response_model=PredictionResponse)
# async def predict_disease(
#     file: UploadFile = File(...),
#     crop_type: str = Form("Unknown"),
#     language: str = Form("en"),
#     latitude: Optional[float] = Form(None),
#     longitude: Optional[float] = Form(None),
#     farmer_id: str = Form("guest_user"),
#     db: Session = Depends(get_db)
# ):
#     # 1. Validate & Save File
#     if file.content_type not in ["image/jpeg", "image/png"]:
#         raise HTTPException(status_code=400, detail="Only JPG/PNG files allowed")

#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)
#     file_path = upload_dir / f"temp_{file.filename}"
        
#     try:
#         with open(file_path, "wb") as buffer:
#             while chunk := await file.read(1024 * 1024):
#                 buffer.write(chunk)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"File save error: {e}")
        
#     try:
#         # 2. AI Inference
#         logger.info(f"Classifying image: {file_path}")
#         raw_result = classify_disease(str(file_path))
        
#         if not raw_result.get("success", False):
#              return {
#                  "disease": "Error",
#                  "confidence": 0.0,
#                  "treatment": ["AI Model Failed"],
#                  "success": False
#              }

#         # 3. Logic: Math Boost Applied Here
#         filtered_predictions = filter_predictions_by_crop(raw_result["all_predictions"], crop_type)
#         new_top = get_new_top_prediction(filtered_predictions)
#         final_disease = new_top["disease"]
#         final_confidence = new_top["confidence"]
        
#         # 4. Knowledge Base
#         treatment = get_treatment_for_disease(final_disease)
#         prevention = get_prevention_for_disease(final_disease)
        
#         # 5. Translation
#         audio_url = None
#         final_disease_clean = final_disease.replace("___", " ").replace("_", " ")
        
#         if language != "en" and language != "en-US":
#             treatment = [translate_response(t, language) for t in treatment]
#             prevention = [translate_response(p, language) for p in prevention]
#             final_disease_trans = translate_response(final_disease_clean, language)
#         else:
#             final_disease_trans = final_disease_clean

#         # 6. Audio Generation
#         try:
#             treatment_summary = treatment[0] if treatment else "Consult expert."
#             audio_script = f"Detected {final_disease_trans}. {treatment_summary}"
            
#             logger.info(f"Generating Audio for Lang: {language}")
#             audio_filename = await generate_audio_response(audio_script, language)
            
#             if audio_filename:
#                 audio_url = f"/uploads/{audio_filename}"
#             else:
#                 logger.warning("Audio file generation returned None")
                
#         except Exception as audio_e:
#             logger.error(f"Audio Generation Failed: {audio_e}")

#         # 7. Database Save
#         try:
#             new_prediction = Prediction(
#                 farmer_id=farmer_id,
#                 disease=final_disease,
#                 confidence=float(final_confidence),
#                 latitude=latitude,
#                 longitude=longitude,
#                 top5=filtered_predictions,
#                 treatment=treatment,
#                 prevention=prevention,
#                 image_path=str(file_path)
#             )
#             db.add(new_prediction)
#             db.commit()
#             logger.success("Analytics data saved to DB")
#         except Exception as db_e:
#             logger.error(f"DB Save Failed: {db_e}")

#         return {
#             "disease": final_disease,
#             "confidence": final_confidence,
#             "treatment": treatment,
#             "prevention": prevention,
#             "language": language,
#             "audio_url": audio_url,
#             "all_predictions": raw_result["all_predictions"],
#             "filtered_predictions": filtered_predictions,
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Prediction Logic Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
    
#     finally:
#         # Clean up temp file to save space
#         if file_path.exists():
#             file_path.unlink()










# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# MERGED: Robust File Handling + Crop Filtering + Multilingual Support
# """

# from fastapi import APIRouter, File, UploadFile, HTTPException, Form
# from pathlib import Path
# import shutil
# import json
# import sys
# from typing import Dict, Any, List

# # --- Imports ---
# from ..ml.disease_classifier import classify_disease
# from ..ml.translator import translate_response, get_supported_languages  # ✅ NEW: Translator
# from ..config import get_settings
# from ..models.schemas import PredictionResponse 
# from ..utils.logger import Logger 

# # --- Initialization ---
# router = APIRouter(tags=["disease"]) 
# settings = get_settings()
# logger = Logger(__name__)

# # --- Load Knowledge Base ONCE ---
# knowledge_base = {}
# try:
#     # Try to find the KB file relative to this script
#     kb_path = (Path(__file__).parent.parent.parent / "ml/knowledge_base/diseases.json").resolve()
#     # kb_path = (Path(__file__).parent.parent.parent / "../../../ml/knowledge_base/diseases.json").resolve()
    
#     # Fallback check for Docker/Production paths if needed
#     if not kb_path.exists():
#         kb_path = Path("ml/knowledge_base/diseases.json").resolve()
#         # kb_path = Path("../../../ml/knowledge_base/diseases.json").resolve()

#     if kb_path.exists():
#         with open(kb_path, encoding='utf-8') as f:
#             knowledge_base = json.load(f)
#         logger.success(f"✅ Knowledge base loaded with {len(knowledge_base)} diseases.")
#     else:
#         logger.warning(f"❌ WARNING: Knowledge base file not found at {kb_path}")
# except Exception as e:
#     logger.error(f"❌ CRITICAL ERROR: Failed to load knowledge base: {e}")


# # --- Helper Functions ---

# def get_treatment_for_disease(disease_name: str) -> List[str]:
#     """Helper function to get treatment from the loaded knowledge base"""
#     if disease_name in knowledge_base:
#         treatment = knowledge_base[disease_name].get("treatment", ["USE_API_FALLBACK"])
#         if "USE_API_FALLBACK" in treatment:
#             logger.info(f"API Fallback: No local data for {disease_name}, calling LLM...")
#             return [f"AI Fallback: Treatment for {disease_name} would be generated here."]
#         return treatment
#     return ["Knowledge base entry not found."]

# def get_prevention_for_disease(disease_name: str) -> List[str]:
#     """Helper function to get prevention from the loaded knowledge base"""
#     if disease_name in knowledge_base:
#         return knowledge_base[disease_name].get("prevention", [])
#     return []

# def filter_predictions_by_crop(predictions: Dict[str, float], crop_type: str) -> Dict[str, float]:
#     """Filters the model's predictions to only match the user's selected crop."""
#     if not crop_type or crop_type == "Unknown":
#         return predictions 

#     filter_key = ""
#     crop_lower = crop_type.lower()
    
#     if crop_lower == "potato": filter_key = "Potato___"
#     elif crop_lower == "tomato": filter_key = "Tomato___"
#     elif crop_lower == "apple": filter_key = "Apple___"
#     elif crop_lower == "grape": filter_key = "Grape___"
#     elif crop_lower == "corn": filter_key = "Corn_(maize)___"
#     elif crop_lower == "cassava": filter_key = "Cassava"
#     elif crop_lower == "paddy":
#         paddy_diseases = ["bacterial_leaf_blight", "bacterial_leaf_streak", "bacterial_panicle_blight", "blast", "brown_spot", "dead_heart", "downy_mildew", "hispa", "normal", "tungro"]
#         filtered = {d: p for d, p in predictions.items() if d in paddy_diseases}
#         return filtered if filtered else predictions

#     if not filter_key:
#         return predictions

#     filtered_predictions = {d: p for d, p in predictions.items() if d.startswith(filter_key)}
#     return filtered_predictions if filtered_predictions else predictions

# def get_new_top_prediction(filtered_predictions: Dict[str, float]) -> Dict[str, Any]:
#     """Finds the new highest-confidence prediction from the filtered list"""
#     if not filtered_predictions:
#         return {"disease": "Uncertain", "confidence": 0.0}
#     top_disease = max(filtered_predictions, key=filtered_predictions.get)
#     top_confidence = filtered_predictions[top_disease]
#     return {"disease": top_disease, "confidence": top_confidence}


# # --- Endpoints ---

# @router.post("/predict", response_model=PredictionResponse)
# async def predict_disease(
#     file: UploadFile = File(...),
#     crop_type: str = Form("Unknown"),
#     language: str = Form("en")  # ✅ NEW: Language parameter via Form
# ):
#     """
#     Upload image and get a CROP-FILTERED & TRANSLATED disease prediction
#     """
    
#     # Validate file type
#     if file.content_type not in ["image/jpeg", "image/png"]:
#         logger.error(f"Invalid file type: {file.content_type}")
#         raise HTTPException(status_code=400, detail="Only JPG/PNG files allowed")

#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)
#     file_path = upload_dir / f"temp_{file.filename}"
        
#     try:
#         # Save the file in chunks (Fixes Seek/Size errors)
#         logger.info(f"Saving uploaded file to {file_path}")
#         with open(file_path, "wb") as buffer:
#             while chunk := await file.read(1024 * 1024):
#                 buffer.write(chunk)
        
#         # Check size
#         file_size = file_path.stat().st_size
#         if file_size > settings.MAX_FILE_SIZE:
#             logger.error(f"File too large: {file_size}")
#             raise HTTPException(status_code=413, detail="File is too large.")

#     except Exception as e:
#         logger.error(f"Failed to save file: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
#     try:
#         # Step 1: Get the model's raw prediction
#         logger.info(f"Classifying image: {file_path}")
#         raw_result = classify_disease(str(file_path))
        
#         if not raw_result.get("success", False):
#              logger.error(f"Classification failed: {raw_result.get('error')}")
#              raise HTTPException(status_code=500, detail=raw_result.get("error", "Classification failed"))

#         # Step 2: Filter the predictions based on Crop Type
#         logger.info(f"Original top guess: {raw_result['disease']} ({raw_result['confidence']})")
#         logger.info(f"Filtering results by crop: '{crop_type}'")
        
#         filtered_predictions = filter_predictions_by_crop(
#             raw_result["all_predictions"], 
#             crop_type
#         )
        
#         # Step 3: Determine final disease
#         new_top_prediction = get_new_top_prediction(filtered_predictions)
#         final_disease = new_top_prediction["disease"]
#         final_confidence = new_top_prediction["confidence"]
        
#         logger.success(f"Filtered top guess: {final_disease} ({final_confidence})")
        
#         # Step 4: Get info from Knowledge Base
#         treatment = get_treatment_for_disease(final_disease)
#         prevention = get_prevention_for_disease(final_disease)
        
#         # Step 5: ✅ TRANSLATION LOGIC
#         if language != "en":
#             logger.info(f"Translating response to: {language}")
            
#             # Translate Treatment
#             if treatment:
#                 treatment = [translate_response(t, language) for t in treatment]
            
#             # Translate Prevention
#             if prevention:
#                 prevention = [translate_response(p, language) for p in prevention]
                
#         # Construct Final Response
#         return {
#             "disease": final_disease,
#             "confidence": final_confidence,
#             "treatment": treatment,
#             "prevention": prevention,
#             "language": language,
#             "all_predictions": raw_result["all_predictions"],
#             "filtered_predictions": filtered_predictions,
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Error in prediction logic: {e}")
#         raise HTTPException(status_code=500, detail=f"Classification logic failed: {str(e)}")
        
#     finally:
#         # Clean up the uploaded file
#         if file_path.exists():
#             file_path.unlink()
#             logger.info(f"Cleaned up temp file: {file_path}")

# @router.get("/languages")
# async def get_languages():
#     """Get list of supported languages for translation"""
#     return {
#         "supported_languages": get_supported_languages(),
#         "default": "en"
#     }





# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# FINAL - Fixes URL prefix and seek() error.
# """

# from fastapi import APIRouter, File, UploadFile, HTTPException, Form
# from pathlib import Path
# import shutil
# import json
# import sys
# from typing import Dict, Any

# # Go up from 'routers' to 'app', then import from 'ml' and 'config'
# from ..ml.disease_classifier import classify_disease
# from ..config import get_settings
# from ..models.schemas import PredictionResponse 
# from ..utils.logger import Logger 

# router = APIRouter(tags=["disease"]) # <-- 1. FIX: Removed prefix="/api/disease"
# settings = get_settings()
# logger = Logger(__name__) # Initialize logger

# # --- Load Knowledge Base ONCE when the app starts ---
# knowledge_base = {}
# try:
#     kb_path = (Path(__file__).parent /diseases.json "../../../ml/knowledge_base/").resolve()
#     if kb_path.exists():
#         with open(kb_path, encoding='utf-8') as f:
#             knowledge_base = json.load(f)
#         logger.success(f"✅ Knowledge base loaded with {len(knowledge_base)} diseases.")
#     else:
#         logger.warning(f"❌ WARNING: Knowledge base file not found at {kb_path}")
# except Exception as e:
#     logger.error(f"❌ CRITICAL ERROR: Failed to load knowledge base: {e}")
# # --- End of KB Load ---


# def get_treatment_for_disease(disease_name: str):
#     """Helper function to get treatment from the loaded knowledge base"""
#     if disease_name in knowledge_base:
#         treatment = knowledge_base[disease_name].get("treatment", ["USE_API_FALLBACK"])
#         if "USE_API_FALLBACK" in treatment:
#             logger.info(f"API Fallback: No local data for {disease_name}, calling LLM...")
#             return [f"AI Fallback: Treatment for {disease_name} would be generated here."]
#         return treatment
#     return ["Knowledge base entry not found."]

# def filter_predictions_by_crop(predictions: Dict[str, float], crop_type: str) -> Dict[str, float]:
#     """Filters the model's predictions to only match the user's selected crop."""
#     if crop_type == "Unknown":
#         return predictions 

#     filter_key = ""
#     if crop_type.lower() == "potato":
#         filter_key = "Potato___"
#     elif crop_type.lower() == "tomato":
#         filter_key = "Tomato___"
#     elif crop_type.lower() == "apple":
#         filter_key = "Apple___"
#     elif crop_type.lower() == "grape":
#         filter_key = "Grape___"
#     elif crop_type.lower() == "corn":
#         filter_key = "Corn_(maize)___"
#     elif crop_type.lower() == "cassava":
#         filter_key = "Cassava"
#     elif crop_type.lower() == "paddy":
#         paddy_diseases = ["bacterial_leaf_blight", "bacterial_leaf_streak", "bacterial_panicle_blight", "blast", "brown_spot", "dead_heart", "downy_mildew", "hispa", "normal", "tungro"]
#         filtered = {disease: prob for disease, prob in predictions.items() if disease in paddy_diseases}
#         return filtered if filtered else predictions

#     if not filter_key:
#         return predictions

#     filtered_predictions = {disease: prob for disease, prob in predictions.items() if disease.startswith(filter_key)}
#     return filtered_predictions if filtered_predictions else predictions

# def get_new_top_prediction(filtered_predictions: Dict[str, float]) -> Dict[str, Any]:
#     """Finds the new highest-confidence prediction from the filtered list"""
#     if not filtered_predictions:
#         return {"disease": "Uncertain", "confidence": 0.0}
#     top_disease = max(filtered_predictions, key=filtered_predictions.get)
#     top_confidence = filtered_predictions[top_disease]
#     return {"disease": top_disease, "confidence": top_confidence}

# @router.post("/predict", response_model=PredictionResponse) # <-- This path is now correct: /api/disease/predict
# async def predict_disease(
#     file: UploadFile = File(...),
#     crop_type: str = Form("Unknown")
# ):
#     """
#     Upload image and get a CROP-FILTERED disease prediction
#     """
    
#     # Validate file type
#     if file.content_type not in ["image/jpeg", "image/png"]:
#         logger.error(f"Invalid file type: {file.content_type}")
#         raise HTTPException(status_code=400, detail="Only JPG/PNG files allowed")

#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)
#     file_path = upload_dir / f"temp_{file.filename}"
        
#     try:
#         # --- 2. THIS IS THE FIX for seek() and NameError: 'offset' ---
#         # Save the file in chunks
#         logger.info(f"Saving uploaded file to {file_path}")
#         with open(file_path, "wb") as buffer:
#             while chunk := await file.read(1024 * 1024):
#                 buffer.write(chunk)
        
#         # Check size of the *saved file*
#         file_size = file_path.stat().st_size
#         if file_size > settings.MAX_FILE_SIZE:
#             logger.error(f"File too large: {file_size}")
#             raise HTTPException(status_code=413, detail="File is too large.")
#         # --- END OF FIX ---

#     except Exception as e:
#         logger.error(f"Failed to save file: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
#     try:
#         # Step 1: Get the model's raw prediction
#         logger.info(f"Classifying image: {file_path}")
#         raw_result = classify_disease(str(file_path))
        
#         if not raw_result.get("success", False):
#              logger.error(f"Classification failed: {raw_result.get('error')}")
#              raise HTTPException(status_code=500, detail=raw_result.get("error", "Classification failed"))

#         # Step 2: Filter the predictions
#         logger.info(f"Original top guess: {raw_result['disease']} ({raw_result['confidence']})")
#         logger.info(f"Filtering results by crop: '{crop_type}'")
        
#         filtered_predictions = filter_predictions_by_crop(
#             raw_result["all_predictions"], 
#             crop_type
#         )
        
#         # Step 3: Get the new, correct top prediction
#         new_top_prediction = get_new_top_prediction(filtered_predictions)
        
#         final_disease = new_top_prediction["disease"]
#         final_confidence = new_top_prediction["confidence"]
        
#         logger.success(f"Filtered top guess: {final_disease} ({final_confidence})")
        
#         # Step 4: Get treatment
#         treatment = get_treatment_for_disease(final_disease)
                
#         return {
#             "disease": final_disease,
#             "confidence": final_confidence,
#             "treatment": treatment,
#             "all_predictions": raw_result["all_predictions"],
#             "filtered_predictions": filtered_predictions,
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Error in prediction logic: {e}")
#         raise HTTPException(status_code=500, detail=f"Classification logic failed: {str(e)}")
        
#     finally:
#         # Clean up the uploaded file
#         if file_path.exists():
#             file_path.unlink()
#             logger.info(f"Cleaned up temp file: {file_path}")





# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# """

# from fastapi import APIRouter, File, UploadFile, HTTPException
# from pathlib import Path
# import shutil
# import json
# import sys


# # Go up from 'routers' to 'app', then import from 'ml' and 'config'
# from ..ml.disease_classifier import classify_disease
# from ..models.schemas import PredictionResponse
# from ..config import get_settings

# router = APIRouter(prefix="/api/disease", tags=["disease"])
# settings = get_settings()

# # --- Load Knowledge Base ONCE when the app starts ---
# knowledge_base = {}
# try:
#     # Build the correct relative path: app -> backend -> agroguard -> ml -> ...
#     kb_path = (Path(__file__).parent / "../../../ml/knowledge_base/diseases.json").resolve()
#     if kb_path.exists():
#         with open(kb_path) as f:
#             knowledge_base = json.load(f)
#         print(f"✅ Knowledge base loaded with {len(knowledge_base)} diseases.")
#     else:
#         print(f"❌ WARNING: Knowledge base file not found at {kb_path}")
# except Exception as e:
#     print(f"❌ CRITICAL ERROR: Failed to load knowledge base: {e}")
# # --- End of KB Load ---


# def get_treatment_for_disease(disease_name: str):
#     """Helper function to get treatment from the loaded knowledge base"""
#     if disease_name in knowledge_base:
#         # This is where your API Fallback logic will live
#         treatment = knowledge_base[disease_name].get("treatment", ["USE_API_FALLBACK"])
#         if "USE_API_FALLBACK" in treatment:
#             # TODO: Add call to your llm_provider here
#             print(f"API Fallback: No local data for {disease_name}, calling LLM...")
#             # For now, return a placeholder
#             return [f"AI Fallback: Treatment for {disease_name} would be generated here."]
#         return treatment
#     return ["Knowledge base entry not found."]


# @router.post("/predict", response_model=PredictionResponse)
# async def predict_disease(file: UploadFile = File(...)):
#     """
#     Upload crop image and get disease prediction
#     Uses AI for uncertain cases (confidence < 60%)
#     """
    
#     # Validate file type
#     if file.content_type not in ["image/jpeg", "image/png"]:
#         logger.error(f"Invalid file type: {file.content_type}")
#         raise HTTPException(
#             status_code=400,
#             detail="Only JPG/PNG files allowed"
#         )
    
#     # Check file size
#     # file_size = await file.seek(0, 2)
#     file_size = await file.seek(offset)
#     await file.seek(0)
    
#     if file_size > settings.MAX_FILE_SIZE:
#         logger.error(f"File too large: {file_size}")
#         raise HTTPException(
#             status_code=413,
#             detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
#         )
    
#     # Save uploaded image
#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)
    
#     unique_filename = f"temp_{file.filename}"
#     file_path = upload_dir / unique_filename
    
#     try:
#         # Save file
#         logger.info(f"Saving uploaded file: {unique_filename}")
        
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
        
#         logger.success(f"File saved: {file_path}")
        
#         # Classify disease
#         logger.info("Starting disease classification...")
#         result = classify_disease(str(file_path), confidence_threshold=0.60)
        
#         if not result.get("success"):
#             logger.error(f"Classification failed: {result.get('error')}")
#             raise HTTPException(
#                 status_code=500,
#                 detail=result.get("error", "Classification failed")
#             )
        
#         # ✅ NEW: Check if needs AI analysis
#         if result.get("needs_ai_analysis"):
#             logger.info("Low confidence detected - querying AI for analysis...")
            
#             # Import AI analyzer
#             from ..ml.llm_provider import analyze_uncertain_prediction
            
#             # Get AI analysis
#             ai_analysis = analyze_uncertain_prediction(
#                 result["top5"],
#                 result["confidence"]
#             )
            
#             # Add AI analysis to result
#             result["treatment"] = [ai_analysis["text"]]
#             result["prevention"] = [
#                 "Follow the suggestions above",
#                 "Consult with local agricultural expert if symptoms persist"
#             ]
#             result["ai_analyzed"] = True
#             result["ai_provider"] = ai_analysis.get("provider", "unknown")
            
#             logger.success(f"✓ AI analysis complete via {ai_analysis.get('provider')}")
        
#         logger.success(f"✓ Predicted: {result['disease']}")
        
#         return result
    
#     except HTTPException:
#         raise
    
#     except Exception as e:
#         logger.error(f"Error in disease prediction: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))
    
#     finally:
#         # Clean up uploaded file
#         if file_path.exists():
#             try:
#                 file_path.unlink()
#                 logger.info(f"Cleaned up: {file_path}")
#             except Exception as e:
#                 logger.warning(f"Could not delete file: {e}")






# #!/usr/bin/env python3
# """
# API Router for Disease Prediction
# """

# from fastapi import APIRouter, File, UploadFile, HTTPException
# from pathlib import Path
# import shutil
# import json
# import sys

# # Go up from 'routers' to 'app', then import from 'ml' and 'config'
# from ..ml.disease_classifier import classify_disease
# from ..config import get_settings

# router = APIRouter(prefix="/api/disease", tags=["disease"])
# settings = get_settings()

# # --- Load Knowledge Base ONCE when the app starts ---
# knowledge_base = {}
# try:
#     # Build the correct relative path: app -> backend -> agroguard -> ml -> ...
#     kb_path = Path(__file__).parent / "../../../ml/knowledge_base/diseases.json"
#     if kb_path.exists():
#         with open(kb_path) as f:
#             knowledge_base = json.load(f)
#         print(f"✅ Knowledge base loaded with {len(knowledge_base)} diseases.")
#     else:
#         print(f"❌ WARNING: Knowledge base file not found at {kb_path.resolve()}")
# except Exception as e:
#     print(f"❌ CRITICAL ERROR: Failed to load knowledge base: {e}")
# # --- End of KB Load ---


# def get_treatment_for_disease(disease_name: str):
#     """Helper function to get treatment from the loaded knowledge base"""
#     if disease_name in knowledge_base:
#         # This is where your API Fallback logic will live
#         treatment = knowledge_base[disease_name].get("treatment", ["USE_API_FALLBACK"])
#         if "USE_API_FALLBACK" in treatment:
#             # TODO: Add call to your llm_provider here
#             print(f"API Fallback: No local data for {disease_name}, calling LLM...")
#             # For now, return a placeholder
#             return [f"AI Fallback: Treatment for {disease_name} would be generated here."]
#         return treatment
#     return ["Knowledge base entry not found."]


# @router.post("/predict")
# async def predict_disease(file: UploadFile = File(...)):
#     """
#     Upload image and get disease prediction
#     """
    
#     upload_dir = Path(settings.UPLOAD_DIR)
#     upload_dir.mkdir(exist_ok=True)
        
#     # Create a unique file path
#     file_path = upload_dir / f"temp_{file.filename}"
        
#     try:
#         # --- FIX: Read the file in chunks and save it ---
#         # This is safer than shutil.copyfileobj and avoids seek()
#         with open(file_path, "wb") as buffer:
#             while chunk := await file.read(1024 * 1024): # Read 1MB chunks
#                 buffer.write(chunk)
        
#         # --- Now we check the size of the saved file ---
#         file_size = file_path.stat().st_size
#         if file_size > settings.MAX_FILE_SIZE:
#             file_path.unlink() # Delete the large file
#             raise HTTPException(
#                 status_code=413, 
#                 detail=f"File is too large. Max size is {settings.MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
#             )

#     except HTTPException as e:
#         raise e # Re-raise the HTTPException
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
#     # Classify the saved file
#     try:
#         result = classify_disease(str(file_path))
        
#         if "error" in result:
#              raise HTTPException(status_code=500, detail=result["error"])

#         # Add treatment info from our knowledge base
#         if "disease" in result:
#             result["treatment"] = get_treatment_for_disease(result["disease"])
                
#         return result
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")
        
#     finally:
#         # Clean up the uploaded file after prediction
#         if file_path.exists():
#             file_path.unlink()