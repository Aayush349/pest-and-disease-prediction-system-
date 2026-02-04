from ultralytics import YOLO
from pathlib import Path
import torch
import json
import os
from threading import Lock
from ..config import get_settings
from ..utils.logger import Logger

logger = Logger(__name__)
settings = get_settings()

# Thread-safe model loading
model_lock = Lock()

class DualModelSystem:
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model1 = None
        self.model2 = None
        self.is_ready = False
        self.load_models()

    def load_models(self):
        BASE_DIR = Path(__file__).resolve().parents[3]  # backend/
        p1 = (BASE_DIR / "backend/app/models/model_v1.pt").resolve()
        p2 = (BASE_DIR /  "backend/app/models/model_v2.pt").resolve()
        
        logger.info(f"[MODEL CHECK] V1 path: {p1} | exists={p1.exists()}")
        logger.info(f"[MODEL CHECK] V2 path: {p2} | exists={p2.exists()}")
        try:
            if p1.exists(): 
                self.model1 = YOLO(str(p1)).to(self.device)
                logger.success(f"✓ Agro-Net V1 loaded on {self.device}")
            
            if p2.exists(): 
                self.model2 = YOLO(str(p2)).to(self.device)
                logger.success(f"✓ Agro-Net V2 loaded on {self.device}")
            
            if self.model1 or self.model2:
                self.is_ready = True
                logger.success(f"✅ AgroGuard Dual-Core Active on {self.device}")
            else:
                logger.error("❌ No models could be loaded")
                
        except Exception as e:
            logger.error(f"❌ Dual Load Fail: {e}")
            self.is_ready = False

    def predict(self, image_path, confidence_threshold=0.60):
        """
        Predict disease using dual model system
        
        Returns: {
            "disease": "apple_black_rot" or "Uncertain",
            "confidence": 0.95,
            "model_used": "Agro-Net V1" or "Agro-Net V2" or "Both",
            "is_uncertain": True/False,
            "needs_ai_analysis": True/False,
            "treatment": [...],
            "prevention": [...],
            "top5": [...],
            "all_predictions": {...},
            "success": True/False
        }
        """
        if not self.is_ready:
            return {"error": "Model system not initialized", "success": False}
        
        # Validate image
        if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
            logger.error(f"Image file is empty or missing at {image_path}")
            return {"error": "Image file is empty or missing", "success": False}
        
        results = []
        models = [(self.model1, "Agro-Net V1"), (self.model2, "Agro-Net V2")]
        
        try:
            for model, name in models:
                if not model: 
                    continue
                
                try:
                    with model_lock:
                        res = model.predict(source=image_path, conf=0.01, save=False, device=self.device)[0]
                    
                    if hasattr(res, 'probs') and res.probs is not None:
                        raw_name = res.names[int(res.probs.top1)]
                        # Normalize name: "Apple___Black_rot" -> "apple_black_rot"
                        # dual_classifier.py के predict function में:
                        clean_name = raw_name.replace("___", "_").replace(" ", "_").replace("(", "").replace(")", "").replace(",", "").lower()
                        
                        # Get all probabilities
                        all_probs = res.probs.data.cpu().numpy()
                        confidence = float(res.probs.top1conf.item())
                        
                        results.append({
                            "model": name,
                            "disease": clean_name,
                            "confidence": confidence,
                            "all_probs": all_probs,
                            "names": res.names,
                            "raw_name": raw_name,
                            "model_instance": model
                        })
                        
                except Exception as e:
                    logger.error(f"Error with {name}: {e}")
                    continue
            
            if not results:
                return {"success": False, "error": "No predictions from any model"}
            
            # Choose best prediction (highest confidence)
            best_result = max(results, key=lambda x: x['confidence'])
            model_used = best_result['model']
            disease_name = best_result['disease']
            raw_disease_name = best_result['raw_name']
            confidence = best_result['confidence']
            
            # Get top 5 predictions
            sorted_indices = torch.argsort(
                torch.tensor(best_result['all_probs']), 
                descending=True
            )[:5].numpy()
            
            top5_predictions = []
            for idx in sorted_indices:
                raw_name = best_result['names'][int(idx)]
                clean_name = raw_name.replace("___", "_").replace(" ", "_").replace("(", "").replace(")", "").lower()
                top5_predictions.append({
                    "disease": clean_name,
                    "raw_disease": raw_name,
                    "probability": round(float(best_result['all_probs'][int(idx)]), 4)
                })
            
            # Get all predictions dictionary
            all_predictions = {}
            for i in range(len(best_result['all_probs'])):
                raw_name = best_result['names'][i]
                clean_name = raw_name.replace("___", "_").replace(" ", "_").replace("(", "").replace(")", "").lower()
                all_predictions[clean_name] = {
                    "raw_name": raw_name,
                    "probability": round(float(best_result['all_probs'][i]), 4)
                }
            
            # Check uncertainty
            is_uncertain = confidence < confidence_threshold
            
            if is_uncertain:
                logger.warning(f"⚠️ Low confidence: {disease_name} ({confidence*100:.2f}%) < {confidence_threshold*100:.0f}%")
                
                return {
                    "disease": "Uncertain",
                    "raw_disease": raw_disease_name,
                    "confidence": round(confidence, 4),
                    "model_used": model_used,
                    "is_uncertain": True,
                    "needs_ai_analysis": True,
                    "top5": top5_predictions,
                    "all_predictions": all_predictions,
                    "success": True
                }
            
            else:
                # High confidence - get treatment info
                logger.success(f"✓ Classified as {disease_name} ({confidence*100:.2f}%) using {model_used}")
                
                treatment, prevention = self._get_disease_info(disease_name)
                
                warning = None
                if confidence < 0.80:
                    warning = f"Moderate confidence ({confidence*100:.1f}%). Consider expert verification."
                
                response = {
                    "disease": disease_name,
                    "raw_disease": raw_disease_name,
                    "confidence": round(confidence, 4),
                    "model_used": model_used,
                    "is_uncertain": False,
                    "needs_ai_analysis": False,
                    "top5": top5_predictions,
                    "treatment": treatment,
                    "prevention": prevention,
                    "all_predictions": all_predictions,
                    "success": True
                }
                
                if warning:
                    response["warning"] = warning
                
                return response
                
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {"error": str(e), "success": False}
    
    def _get_disease_info(self, disease_name: str):
        """
        Get treatment and prevention from knowledge base
        """
        try:
            # Try multiple path locations for knowledge base
            kb_path_options = [
                Path(settings.KB_PATH).resolve(),
                Path(__file__).parent.parent.parent.parent / settings.KB_PATH,
                Path(__file__).parent.parent.parent.parent / "ml/knowledge_base/diseases.json",
                Path("./ml/knowledge_base/diseases.json"),
                Path("../ml/knowledge_base/diseases.json"),
                Path("../../ml/knowledge_base/diseases.json"),
                Path("../../../ml/knowledge_base/diseases.json"),
            ]
            
            kb_path = None
            for path_option in kb_path_options:
                if path_option.exists():
                    kb_path = path_option
                    logger.info(f"✓ Found knowledge base at: {kb_path}")
                    break
            
            if kb_path is None:
                logger.warning(f"⚠️ Knowledge base not found at any location")
                return self._generate_fallback_treatment(disease_name)
            
            # Load knowledge base
            with open(kb_path, 'r', encoding='utf-8') as f:
                kb = json.load(f)
            
            # Try to find disease in KB (both normalized and raw format)
            kb_key = None
            
            # First try normalized name
            if disease_name in kb:
                kb_key = disease_name
            else:
                # Try to find by matching key parts
                for key in kb.keys():
                    normalized_key = key.replace("___", "_").replace(" ", "_").replace("(", "").replace(")", "").lower()
                    if normalized_key == disease_name:
                        kb_key = key
                        break
            
            if kb_key:
                disease_info = kb[kb_key]
                treatment = disease_info.get("treatment", [])
                prevention = disease_info.get("prevention", [])
                
                # Ensure lists
                if isinstance(treatment, str):
                    treatment = [treatment]
                if isinstance(prevention, str):
                    prevention = [prevention]
                
                # Validate not empty
                if not treatment:
                    logger.warning(f"Empty treatment for {disease_name}")
                    treatment = self._generate_fallback_treatment(disease_name)[0]
                
                if not prevention:
                    logger.warning(f"Empty prevention for {disease_name}")
                    prevention = self._generate_fallback_treatment(disease_name)[1]
                
                logger.success(f"✓ Loaded treatment for {disease_name}")
                return (treatment, prevention)
            else:
                logger.warning(f"Disease '{disease_name}' not in KB, using fallback")
                return self._generate_fallback_treatment(disease_name)
        
        except Exception as e:
            logger.error(f"KB loading error: {str(e)}")
            return self._generate_fallback_treatment(disease_name)
    
    def _generate_fallback_treatment(self, disease_name: str):
        """
        Generate intelligent fallback treatment advice
        """
        # Extract crop and disease type from normalized name
        parts = disease_name.split('_')
        crop = ""
        disease_type = ""
        
        # Try to identify crop (common crops)
        crop_keywords = [
            'apple', 'tomato', 'potato', 'corn', 'grape', 'cherry',
            'peach', 'pepper', 'strawberry', 'soybean', 'raspberry',
            'blueberry', 'squash', 'cucumber', 'pumpkin'
        ]
        
        for keyword in crop_keywords:
            if keyword in disease_name:
                crop = keyword
                break
        
        if not crop:
            crop = "plant"
        
        # Identify disease type
        if 'blight' in disease_name:
            disease_type = 'blight'
        elif 'rot' in disease_name:
            disease_type = 'rot'
        elif 'spot' in disease_name:
            disease_type = 'spot'
        elif 'rust' in disease_name:
            disease_type = 'rust'
        elif 'mosaic' in disease_name:
            disease_type = 'mosaic'
        elif 'virus' in disease_name:
            disease_type = 'virus'
        elif 'bacterial' in disease_name:
            disease_type = 'bacterial'
        elif 'scab' in disease_name:
            disease_type = 'scab'
        elif 'mildew' in disease_name:
            disease_type = 'mildew'
        else:
            disease_type = 'fungal'
        
        # Generate treatment based on disease type
        treatment = [
            f"Immediately isolate affected {crop} plants",
            "Remove and destroy infected plant parts (leaves, stems, fruits)",
        ]
        
        if disease_type == 'blight':
            treatment.extend([
                "Apply copper-based fungicide or Mancozeb (follow label instructions)",
                "Spray every 7-10 days until symptoms reduce",
                "Ensure good air circulation around plants",
                "Avoid overhead watering"
            ])
        elif disease_type == 'rot':
            treatment.extend([
                "Remove affected parts immediately",
                "Apply fungicide containing Chlorothalonil or Copper",
                "Improve drainage around plants",
                "Reduce soil moisture"
            ])
        elif disease_type == 'spot':
            treatment.extend([
                "Apply appropriate fungicide (Chlorothalonil or Copper)",
                "Remove infected leaves and dispose properly",
                "Avoid overhead watering",
                "Water in morning so leaves dry quickly"
            ])
        elif disease_type == 'virus' or disease_type == 'mosaic':
            treatment.extend([
                "⚠️ Viral disease - no chemical cure available",
                "Remove and destroy infected plants immediately",
                "Control aphids and other virus vectors with insecticidal soap",
                "Plant virus-resistant varieties in future"
            ])
        elif disease_type == 'bacterial':
            treatment.extend([
                "Apply copper-based bactericide",
                "Remove infected plant parts with sterilized tools",
                "Avoid working with plants when wet",
                "Improve air circulation"
            ])
        else:
            treatment.extend([
                "Apply broad-spectrum fungicide as per label instructions",
                "Improve plant spacing for better air flow",
                "Consult local agricultural expert for specific diagnosis",
                "Maintain proper plant hygiene"
            ])
        
        # Generate prevention
        prevention = [
            f"Plant disease-resistant {crop} varieties",
            "Practice crop rotation (avoid same crop in same location for 2-3 years)",
            "Maintain proper plant spacing (12-18 inches minimum)",
        ]
        
        if disease_type in ['blight', 'spot', 'rot']:
            prevention.extend([
                "Avoid overhead watering - use drip irrigation",
                "Water in morning so leaves dry before evening",
                "Apply mulch to prevent soil splash onto leaves",
                "Remove plant debris after harvest"
            ])
        elif disease_type in ['virus', 'mosaic']:
            prevention.extend([
                "Control aphids, whiteflies, and other insects with neem oil",
                "Use insecticidal soap for pests",
                "Remove weeds that harbor viruses",
                "Sanitize tools between plants"
            ])
        else:
            prevention.extend([
                "Remove and destroy infected plant debris",
                "Apply preventive fungicide spray during humid weather",
                "Monitor plants weekly for early signs",
                "Maintain good field hygiene"
            ])
        
        logger.info(f"✓ Generated intelligent fallback for {disease_name}")
        return (treatment, prevention)

# Singleton instance
dual_bot = DualModelSystem()

# Easy function to call from API
def classify_disease(image_path: str, confidence_threshold: float = 0.60):
    """Easy function to call from API"""
    if not dual_bot.is_ready:
        logger.error("Dual Model System not ready")
        return {"error": "Model system not initialized", "success": False}
    
    return dual_bot.predict(image_path, confidence_threshold)


# from ultralytics import YOLO
# from ..config import get_settings
# import torch

# settings = get_settings()

# class DualModelSystem:
#     def __init__(self):
#         # Dono models ko CUDA par load karo (RTX 4050 ka pura faayda uthao)
#         device = 'cuda' if torch.cuda.is_available() else 'cpu'
#         self.device = device
#         self.model1 = None
#         self.model2 = None
#         try:
#             if getattr(settings, 'YOLO_MODEL_V1_PATH', None):
#                 self.model1 = YOLO(settings.YOLO_MODEL_V1_PATH)
#                 try:
#                     self.model1.to(device)
#                 except Exception:
#                     pass
#             if getattr(settings, 'YOLO_MODEL_V2_PATH', None):
#                 self.model2 = YOLO(settings.YOLO_MODEL_V2_PATH)
#                 try:
#                     self.model2.to(device)
#                 except Exception:
#                     pass
#             print(f"✅ Dual Core Loaded on {device}")
#         except Exception as e:
#             print(f"❌ Load Error: {e}")

#     def predict(self, image_path):
#         results = []
#         # Dono models se prediction lo
#         for m in [self.model1, self.model2]:
#             if m:
#                 try:
#                     res = m.predict(source=image_path, conf=0.25, save=False)[0]
#                 except TypeError:
#                     # older/newer API compatibility
#                     res = m.predict(image_path, conf=0.25, save=False)[0]
#                 except Exception:
#                     continue

#                 # Attempt to extract a class name and confidence robustly
#                 try:
#                     # ultralytics may provide .boxes.cls or .probs; try both
#                     if hasattr(res, 'probs') and getattr(res.probs, 'top1', None) is not None:
#                         cls_idx = res.probs.top1
#                         cls_name = res.names[int(cls_idx)]
#                         conf = float(res.probs.top1conf.item()) if hasattr(res.probs.top1conf, 'item') else float(res.probs.top1conf)
#                     else:
#                         # Fallback: use boxes
#                         boxes = getattr(res, 'boxes', None)
#                         if boxes and len(boxes) > 0:
#                             cls_idx = int(boxes.cls[0]) if hasattr(boxes, 'cls') else int(boxes[0].cls)
#                             cls_name = res.names.get(cls_idx, str(cls_idx)) if isinstance(res.names, dict) else res.names[cls_idx]
#                             conf = float(boxes.conf[0]) if hasattr(boxes, 'conf') else 0.0
#                         else:
#                             continue

#                     results.append({
#                         "disease": cls_name,
#                         "confidence": conf
#                     })
#                 except Exception:
#                     continue

#         if not results:
#             return {"success": False}

#         # Best prediction chuno
#         winner = max(results, key=lambda x: x['confidence'])
#         return {"success": True, **winner}

# # Singleton instance
# dual_bot = DualModelSystem()






# from ultralytics import YOLO
# from pathlib import Path
# import logging

# # Setup paths
# BASE_DIR = Path(__file__).resolve().parent
# MODEL_1_PATH = BASE_DIR / "models" / "model_v1.pt"
# MODEL_2_PATH = BASE_DIR / "models" / "model_v2.pt"

# class DualModelSystem:
#     def __init__(self):
#         self.model1 = None
#         self.model2 = None
#         self.load_models()

#     def load_models(self):
#         try:
#             if MODEL_1_PATH.exists():
#                 self.model1 = YOLO(str(MODEL_1_PATH))
#                 print(f"✅ Loaded Primary Model: {MODEL_1_PATH.name}")
            
#             if MODEL_2_PATH.exists():
#                 self.model2 = YOLO(str(MODEL_2_PATH))
#                 print(f"✅ Loaded Secondary Model: {MODEL_2_PATH.name}")
                
#         except Exception as e:
#             print(f"❌ Model Loading Error: {e}")

#     def predict(self, image_path):
#         """
#         Runs both models. Returns the one with higher confidence.
#         Fails if confidence is too low (< 40%).
#         """
#         results = []

#         # --- RUN MODEL 1 ---
#         if self.model1:
#             try:
#                 res1 = self.model1.predict(image_path, conf=0.25, save=False)[0]
#                 if res1.probs:
#                     top1 = res1.probs.top1
#                     conf = res1.probs.top1conf.item()
#                     name = res1.names[top1]
#                     results.append({"source": "Agro-Net V1", "disease": name, "confidence": conf})
#             except: pass

#         # --- RUN MODEL 2 ---
#         if self.model2:
#             try:
#                 res2 = self.model2.predict(image_path, conf=0.25, save=False)[0]
#                 if res2.probs:
#                     top1 = res2.probs.top1
#                     conf = res2.probs.top1conf.item()
#                     name = res2.names[top1]
#                     results.append({"source": "Agro-Net V2", "disease": name, "confidence": conf})
#             except: pass

#         # --- DECISION TIME ---
#         if not results:
#             return {"success": False, "reason": "No Detection"}

#         # Sort by confidence (Highest first)
#         best_result = sorted(results, key=lambda x: x['confidence'], reverse=True)[0]
        
#         # FAIL-SAFE: Agar confidence 40% se kam hai, toh Gemini ko de do
#         if best_result['confidence'] < 0.40:
#             return {"success": False, "reason": "Low Confidence"}

#         return {
#             "success": True,
#             "disease": best_result['disease'],
#             "confidence": best_result['confidence'],
#             "used_model": best_result['source']
#         }

# # Create Instance
# dual_bot = DualModelSystem()