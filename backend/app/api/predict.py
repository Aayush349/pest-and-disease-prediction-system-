"""
Prediction Routes with Async Support
Now supports both online (Gemini) and offline (YOLO) modes
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import shutil
from pathlib import Path
from datetime import datetime
import json

from ..ml.disease_detector import DiseaseDetector
from ..config import get_settings
from ..utils.logger import Logger

router = APIRouter(tags=["Prediction"])
settings = get_settings()
logger = Logger(__name__)

# Initialize detector
detector = DiseaseDetector()

@router.post("/disease")
async def detect_disease(file: UploadFile = File(...)):
    """
    Upload crop image and get disease prediction
    Auto-switches between Hidden Gemini (online) and Local YOLO (offline)
    """
    try:
        # Validate file
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create uploads directory
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(exist_ok=True)
        
        # Save file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = upload_dir / f"{timestamp}_{file.filename}"
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved: {file_path}")
        
        # Run prediction (async)
        prediction = await detector.predict(str(file_path))
        
        if not prediction.get("success"):
            raise HTTPException(status_code=500, detail=prediction.get("error"))
        
        # Add engine info to response
        response_data = {
            "success": True,
            "data": prediction,
            "image_path": str(file_path),
            "engine_used": "GEMINI_VISION" if not prediction.get("is_offline") else "LOCAL_YOLO",
            "timestamp": datetime.now().isoformat()
        }
        
        return response_data
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/engine-status")
async def get_engine_status():
    """Check which engine is active (for debugging)"""
    status = detector.check_engine_status()
    return {
        "success": True,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/diseases")
async def get_diseases():
    """Get list of detectable diseases"""
    try:
        disease_list = list(detector.disease_classes.values())
        return {
            "success": True,
            "total": len(disease_list),
            "diseases": disease_list,
            "engine": detector.check_engine_status()["active_engine"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_model_stats():
    """Get model statistics"""
    engine_status = detector.check_engine_status()
    
    return {
        "active_engine": engine_status["active_engine"],
        "is_online": engine_status["is_online"],
        "local_model": engine_status["local_model"],
        "knowledge_base_size": engine_status["knowledge_base_count"],
        "total_classes": len(detector.disease_classes),
        "timestamp": datetime.now().isoformat()
    }


# from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
# from fastapi.responses import JSONResponse
# import shutil
# from pathlib import Path
# from datetime import datetime
# import json

# from ..ml.disease_detector import DiseaseDetector
# from ..config import get_settings
# from ..utils.logger import Logger

# router = APIRouter(tags=["Prediction"])
# settings = get_settings()
# logger = Logger(__name__)

# # Initialize detector
# detector = DiseaseDetector()

# @router.post("/disease")
# async def detect_disease(file: UploadFile = File(...)):
#     """
#     Upload crop image and get disease prediction
#     Uses TRAINED model from agricultural dataset
#     Returns REAL analysis (not hardcoded)
#     """
#     try:
#         # Validate file
#         if not file.content_type.startswith("image/"):
#             raise HTTPException(status_code=400, detail="File must be an image")
        
#         # Create uploads directory
#         upload_dir = Path(settings.UPLOAD_DIR)
#         upload_dir.mkdir(exist_ok=True)
        
#         # Save file with timestamp
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         file_path = upload_dir / f"{timestamp}_{file.filename}"
        
#         with file_path.open("wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
        
#         logger.info(f"File saved: {file_path}")
        
#         # Run prediction
#         prediction = detector.predict(str(file_path))
        
#         if not prediction.get("success"):
#             raise HTTPException(status_code=500, detail=prediction.get("error"))
        
#         return {
#             "success": True,
#             "data": prediction,
#             "image_path": str(file_path)
#         }
        
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         logger.error(f"Prediction error: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/diseases")
# async def get_diseases():
#     """Get list of detectable diseases"""
#     try:
#         disease_list = list(detector.disease_classes.values())
#         return {
#             "success": True,
#             "total": len(disease_list),
#             "diseases": disease_list
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/stats")
# async def get_model_stats():
#     """Get model statistics"""
#     return {
#         "model_type": detector.model.__class__.__name__,
#         "is_trained": detector.is_trained,
#         "total_classes": len(detector.disease_classes),
#         "knowledge_base_size": len(detector.knowledge_base),
#         "timestamp": datetime.now().isoformat()
#     }
