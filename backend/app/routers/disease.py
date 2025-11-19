#!/usr/bin/env python3
"""
API Router for Disease Prediction
FINAL - Fixes URL prefix and seek() error.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pathlib import Path
import shutil
import json
import sys
from typing import Dict, Any

# Go up from 'routers' to 'app', then import from 'ml' and 'config'
from ..ml.disease_classifier import classify_disease
from ..config import get_settings
from ..models.schemas import PredictionResponse 
from ..utils.logger import Logger 

router = APIRouter(tags=["disease"]) # <-- 1. FIX: Removed prefix="/api/disease"
settings = get_settings()
logger = Logger(__name__) # Initialize logger

# --- Load Knowledge Base ONCE when the app starts ---
knowledge_base = {}
try:
    kb_path = (Path(__file__).parent / "../../../ml/knowledge_base/diseases.json").resolve()
    if kb_path.exists():
        with open(kb_path, encoding='utf-8') as f:
            knowledge_base = json.load(f)
        logger.success(f"✅ Knowledge base loaded with {len(knowledge_base)} diseases.")
    else:
        logger.warning(f"❌ WARNING: Knowledge base file not found at {kb_path}")
except Exception as e:
    logger.error(f"❌ CRITICAL ERROR: Failed to load knowledge base: {e}")
# --- End of KB Load ---


def get_treatment_for_disease(disease_name: str):
    """Helper function to get treatment from the loaded knowledge base"""
    if disease_name in knowledge_base:
        treatment = knowledge_base[disease_name].get("treatment", ["USE_API_FALLBACK"])
        if "USE_API_FALLBACK" in treatment:
            logger.info(f"API Fallback: No local data for {disease_name}, calling LLM...")
            return [f"AI Fallback: Treatment for {disease_name} would be generated here."]
        return treatment
    return ["Knowledge base entry not found."]

def filter_predictions_by_crop(predictions: Dict[str, float], crop_type: str) -> Dict[str, float]:
    """Filters the model's predictions to only match the user's selected crop."""
    if crop_type == "Unknown":
        return predictions 

    filter_key = ""
    if crop_type.lower() == "potato":
        filter_key = "Potato___"
    elif crop_type.lower() == "tomato":
        filter_key = "Tomato___"
    elif crop_type.lower() == "apple":
        filter_key = "Apple___"
    elif crop_type.lower() == "grape":
        filter_key = "Grape___"
    elif crop_type.lower() == "corn":
        filter_key = "Corn_(maize)___"
    elif crop_type.lower() == "cassava":
        filter_key = "Cassava"
    elif crop_type.lower() == "paddy":
        paddy_diseases = ["bacterial_leaf_blight", "bacterial_leaf_streak", "bacterial_panicle_blight", "blast", "brown_spot", "dead_heart", "downy_mildew", "hispa", "normal", "tungro"]
        filtered = {disease: prob for disease, prob in predictions.items() if disease in paddy_diseases}
        return filtered if filtered else predictions

    if not filter_key:
        return predictions

    filtered_predictions = {disease: prob for disease, prob in predictions.items() if disease.startswith(filter_key)}
    return filtered_predictions if filtered_predictions else predictions

def get_new_top_prediction(filtered_predictions: Dict[str, float]) -> Dict[str, Any]:
    """Finds the new highest-confidence prediction from the filtered list"""
    if not filtered_predictions:
        return {"disease": "Uncertain", "confidence": 0.0}
    top_disease = max(filtered_predictions, key=filtered_predictions.get)
    top_confidence = filtered_predictions[top_disease]
    return {"disease": top_disease, "confidence": top_confidence}

@router.post("/predict", response_model=PredictionResponse) # <-- This path is now correct: /api/disease/predict
async def predict_disease(
    file: UploadFile = File(...),
    crop_type: str = Form("Unknown")
):
    """
    Upload image and get a CROP-FILTERED disease prediction
    """
    
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        logger.error(f"Invalid file type: {file.content_type}")
        raise HTTPException(status_code=400, detail="Only JPG/PNG files allowed")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / f"temp_{file.filename}"
        
    try:
        # --- 2. THIS IS THE FIX for seek() and NameError: 'offset' ---
        # Save the file in chunks
        logger.info(f"Saving uploaded file to {file_path}")
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)
        
        # Check size of the *saved file*
        file_size = file_path.stat().st_size
        if file_size > settings.MAX_FILE_SIZE:
            logger.error(f"File too large: {file_size}")
            raise HTTPException(status_code=413, detail="File is too large.")
        # --- END OF FIX ---

    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
    try:
        # Step 1: Get the model's raw prediction
        logger.info(f"Classifying image: {file_path}")
        raw_result = classify_disease(str(file_path))
        
        if not raw_result.get("success", False):
             logger.error(f"Classification failed: {raw_result.get('error')}")
             raise HTTPException(status_code=500, detail=raw_result.get("error", "Classification failed"))

        # Step 2: Filter the predictions
        logger.info(f"Original top guess: {raw_result['disease']} ({raw_result['confidence']})")
        logger.info(f"Filtering results by crop: '{crop_type}'")
        
        filtered_predictions = filter_predictions_by_crop(
            raw_result["all_predictions"], 
            crop_type
        )
        
        # Step 3: Get the new, correct top prediction
        new_top_prediction = get_new_top_prediction(filtered_predictions)
        
        final_disease = new_top_prediction["disease"]
        final_confidence = new_top_prediction["confidence"]
        
        logger.success(f"Filtered top guess: {final_disease} ({final_confidence})")
        
        # Step 4: Get treatment
        treatment = get_treatment_for_disease(final_disease)
                
        return {
            "disease": final_disease,
            "confidence": final_confidence,
            "treatment": treatment,
            "all_predictions": raw_result["all_predictions"],
            "filtered_predictions": filtered_predictions,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in prediction logic: {e}")
        raise HTTPException(status_code=500, detail=f"Classification logic failed: {str(e)}")
        
    finally:
        # Clean up the uploaded file
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up temp file: {file_path}")





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