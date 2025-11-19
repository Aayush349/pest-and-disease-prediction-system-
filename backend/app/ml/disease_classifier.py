#!/usr/bin/env python3
"""
Disease Classification using trained YOLO model
99.31% accuracy on 51 disease classes
FIXED: Dynamic AI-powered uncertain case handling (NO HARDCODING)
"""

import torch
from ultralytics import YOLO
from pathlib import Path
import json
import os
from threading import Lock
from ..config import get_settings
from ..models.schemas import PredictionResponse
from ..utils.logger import Logger

logger = Logger(__name__)
settings = get_settings()

# Thread-safe model loading
model_lock = Lock()

class DiseaseClassifier:
    def __init__(self):
        """Initialize classifier"""
        try:
            model_path_str = settings.MODEL_PATH
            model_path = (Path(__file__).parent.parent.parent.parent / model_path_str).resolve()
            
            if not model_path.exists():
                logger.error(f"Model not found at {model_path}")
                raise FileNotFoundError(f"Model not found at {model_path}")
            
            logger.info(f"Loading disease classifier from {model_path}...")
            self.model = YOLO(str(model_path))
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            
            logger.success(f"✓ Disease classifier loaded on {self.device}")
            self.is_ready = True
        
        except Exception as e:
            logger.error(f"Failed to load classifier: {str(e)}")
            self.is_ready = False
    
    def predict(self, image_path: str, confidence_threshold: float = 0.60):
        """
        Predict disease with AI-powered uncertain case handling
        
        Returns: {
            "disease": "Tomato___Early_blight" OR "Uncertain",
            "confidence": 0.33,
            "top5": [...],
            "is_uncertain": true/false,
            "needs_ai_analysis": true/false,  # NEW FLAG
            "success": True
        }
        """
        
        if not self.is_ready:
            logger.error("Classifier not initialized")
            return {"error": "Classifier not initialized", "success": False}
        
        try:
            # Validate image
            if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
                logger.error(f"Image file is empty or missing at {image_path}")
                return {"error": "Image file is empty or missing", "success": False}
            
            # Run inference (thread-safe)
            with model_lock:
                results = self.model.predict(image_path, conf=0.01, device=self.device)
            
            if not results or len(results) == 0:
                logger.error("Model returned no results")
                return {"error": "No prediction from model", "success": False}
            
            result = results[0]
            
            # Get probabilities safely
            all_probs = result.probs.data.cpu().numpy()
            
            # Get top class
            top_class_idx = int(result.probs.top1)
            top_class_name = result.names[top_class_idx]
            top_confidence = float(result.probs.top1conf.item())
            
            # Get top 5 predictions
            sorted_indices = torch.argsort(torch.tensor(all_probs), descending=True)[:5].numpy()
            
            top5_predictions = [
                {
                    "disease": result.names[int(idx)],
                    "probability": round(float(all_probs[int(idx)]), 4)
                }
                for idx in sorted_indices
            ]
            
            # ✅ NEW: Check if uncertain
            is_uncertain = top_confidence < confidence_threshold
            
            if is_uncertain:
                # Low confidence - need AI analysis
                logger.warning(f"⚠️  Low confidence: {top_class_name} ({top_confidence*100:.2f}%) < {confidence_threshold*100:.0f}%")
                
                return {
                    "disease": "Uncertain",
                    "confidence": round(top_confidence, 4),
                    "is_uncertain": True,
                    "needs_ai_analysis": True,  # ✅ FLAG for AI
                    "top5": top5_predictions,
                    "all_predictions": {
                        result.names[i]: round(float(all_probs[i]), 4)
                        for i in range(len(all_probs))
                    },
                    "success": True
                }
            
            else:
                # High confidence - use model prediction
                logger.success(f"✓ Classified as {top_class_name} ({top_confidence*100:.2f}%)")
                
                treatment, prevention = self._get_disease_info(top_class_name)
                
                warning = None
                if top_confidence < 0.80:
                    warning = f"Moderate confidence ({top_confidence*100:.1f}%). Consider consulting an expert for verification."
                
                response = {
                    "disease": top_class_name,
                    "confidence": round(top_confidence, 4),
                    "is_uncertain": False,
                    "needs_ai_analysis": False,
                    "top5": top5_predictions,
                    "treatment": treatment,
                    "prevention": prevention,
                    "all_predictions": {
                        result.names[i]: round(float(all_probs[i]), 4)
                        for i in range(len(all_probs))
                    },
                    "success": True
                }
                
                if warning:
                    response["warning"] = warning
                
                return response
        
        except Exception as e:
            logger.error(f"Classification error: {str(e)}")
            return {"error": str(e), "success": False}
    
    def _get_disease_info(self, disease_name: str):
        """Get treatment and prevention from knowledge base"""
        try:
            kb_path_str = settings.KB_PATH
            kb_path = (Path(__file__).parent.parent.parent.parent / kb_path_str).resolve()
            
            if not kb_path.exists():
                logger.warning(f"Knowledge base not found at {kb_path}")
                return (
                    ["Consult with agricultural expert for treatment"],
                    ["Monitor plant regularly", "Improve field hygiene"]
                )
            
            with open(kb_path, 'r', encoding='utf-8') as f:
                kb = json.load(f)
            
            if disease_name in kb:
                disease_info = kb[disease_name]
                treatment = disease_info.get("treatment", ["Consult agricultural expert"])
                prevention = disease_info.get("prevention", ["Monitor plant regularly"])
                
                if isinstance(treatment, str):
                    treatment = [treatment]
                if isinstance(prevention, str):
                    prevention = [prevention]
                
                return (treatment, prevention)
            else:
                logger.warning(f"Disease '{disease_name}' not found in knowledge base")
                return (
                    ["Treatment information not available - consult expert"],
                    ["Prevention information not available"]
                )
        
        except Exception as e:
            logger.warning(f"Could not load knowledge base: {e}")
            return (
                ["AI Fallback: Treatment would be generated here"],
                ["AI Fallback: Prevention would be generated here"]
            )

# Singleton instance
try:
    classifier = DiseaseClassifier()
except Exception as e:
    logger.error(f"Failed to initialize classifier: {e}")
    classifier = None

def classify_disease(image_path: str, confidence_threshold: float = 0.60):
    """Easy function to call from API"""
    if classifier is None or not classifier.is_ready:
        logger.error("Classifier singleton is None or not ready")
        return {"error": "Classifier not initialized", "success": False}
    
    return classifier.predict(image_path, confidence_threshold)







# """
# Disease Classification using trained YOLO model
# 99.31% accuracy on 51 disease classes
# """

# import torch
# from ultralytics import YOLO
# from pathlib import Path
# import json
# from ..utils.logger import Logger
# from ..config import get_settings

# logger = Logger(__name__)
# settings = get_settings()

# class DiseaseClassifier:
#     """Load and inference with trained YOLO classifier"""
    
#     def __init__(self):
#         """Initialize classifier"""
#         try:
#             model_path = Path(settings.MODEL_PATH).resolve()
            
#             if not model_path.exists():
#                 # Try alternate path
#                 model_path = Path(__file__).parent.parent.parent.parent / settings.MODEL_PATH
            
#             if not model_path.exists():
#                 raise FileNotFoundError(f"Model not found at {model_path}")
            
#             logger.info(f"Loading disease classifier from {model_path}...")
            
#             self.model = YOLO(str(model_path))
#             self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            
#             logger.success(f"Disease classifier loaded on {self.device} ✓")
#             self.is_ready = True
        
#         except Exception as e:
#             logger.error(f"Failed to load classifier: {str(e)}")
#             self.is_ready = False
    
#     def predict(self, image_path: str, confidence_threshold: float = 0.3):
#         """
#         Predict disease from image
        
#         Args:
#             image_path: Path to crop image (JPG/PNG)
#             confidence_threshold: Minimum confidence (0-1)
        
#         Returns:
#             {
#                 "disease": "Tomato___Early_blight",
#                 "confidence": 0.9931,
#                 "top5": [{"disease": "...", "probability": 0.99}, ...],
#                 "treatment": [...],
#                 "prevention": [...],
#                 "success": True
#             }
#         """
        
#         if not self.is_ready:
#             return {
#                 "error": "Classifier not initialized",
#                 "success": False
#             }
        
#         try:
#             # Validate image exists
#             img_path = Path(image_path)
#             if not img_path.exists():
#                 return {
#                     "error": f"Image not found: {image_path}",
#                     "success": False
#                 }
            
#             # Run inference
#             results = self.model.predict(str(image_path), conf=confidence_threshold)
            
#             if not results or len(results) == 0:
#                 return {
#                     "error": "No prediction from model",
#                     "success": False
#                 }
            
#             result = results[0]
            
#             # Get top prediction
#             top_class_idx = int(result.probs.top1)
#             top_class_name = result.names[top_class_idx]
#             top_confidence = float(result.probs.top1conf.item())
            
#             # Get top 5 predictions
#             top5_indices = torch.argsort(result.probs.data)[-5:][::-1]
#             top5_predictions = [
#                 {
#                     "disease": result.names[int(idx)],
#                     "probability": round(float(result.probs.data[int(idx)].item()), 4)
#                 }
#                 for idx in top5_indices
#             ]
            
#             # Get treatment and prevention
#             treatment, prevention = self._get_disease_info(top_class_name)
            
#             logger.success(f"Classified as {top_class_name} ({top_confidence*100:.2f}%)")
            
#             return {
#                 "disease": top_class_name,
#                 "confidence": round(top_confidence, 4),
#                 "top5": top5_predictions,
#                 "treatment": treatment,
#                 "prevention": prevention,
#                 "success": True
#             }
        
#         except Exception as e:
#             logger.error(f"Classification error: {str(e)}")
#             return {
#                 "error": str(e),
#                 "success": False
#             }
    
#     def _get_disease_info(self, disease_name: str):
#         """Get treatment and prevention from knowledge base"""
#         try:
#             kb_path = Path(settings.KB_PATH).resolve()
            
#             if not kb_path.exists():
#                 kb_path = Path(__file__).parent.parent.parent.parent / settings.KB_PATH
            
#             if kb_path.exists():
#                 with open(kb_path, 'r', encoding='utf-8') as f:
#                     kb = json.load(f)
#                     if disease_name in kb:
#                         return (
#                             kb[disease_name].get("treatment", ["No treatment data"]),
#                             kb[disease_name].get("prevention", ["No prevention data"])
#                         )
#         except Exception as e:
#             logger.warning(f"Could not load knowledge base: {e}")
        
#         return (
#             ["Consult with agricultural expert"],
#             ["Monitor plant regularly"]
#         )

# # Singleton instance
# try:
#     classifier = DiseaseClassifier()
# except Exception as e:
#     logger.error(f"Failed to initialize classifier: {e}")
#     classifier = None

# def classify_disease(image_path: str, confidence_threshold: float = 0.3):
#     """Easy function to call from API"""
#     if classifier is None:
#         return {"error": "Classifier not initialized", "success": False}
    
#     return classifier.predict(image_path, confidence_threshold)
