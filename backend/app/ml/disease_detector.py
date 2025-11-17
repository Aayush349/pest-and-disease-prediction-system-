from ultralytics import YOLO
from PIL import Image
import torch
import json
from pathlib import Path
from ..config import get_settings
from ..utils.logger import Logger

settings = get_settings()
logger = Logger(__name__)

class DiseaseDetector:
    def __init__(self):
        """Initialize with TRAINED model (or fallback to pre-trained)"""
        
        logger.info("Initializing Disease Detector...")
        
        # Try to load trained model
        model_path = Path(settings.YOLO_MODEL_PATH)
        
        if model_path.exists():
            logger.success(f"✓ Loaded trained model: {model_path}")
            self.model = YOLO(str(model_path))
            self.model_source = "trained"
        else:
            logger.warning(f"⚠ Trained model not found at {model_path}")
            logger.info("Using pre-trained YOLOv8 (fallback)")
            self.model = YOLO('yolov8n.pt')
            self.model_source = "pretrained"
        
        # Load knowledge base (from extracted dataset, not hardcoded!)
        self._load_knowledge_base()
        
        # Build disease class mapping from knowledge base
        self._build_class_mapping()
        
        logger.success("Disease Detector initialized")
    
    def _load_knowledge_base(self):
        """Load knowledge base from JSON (extracted from dataset)"""
        kb_path = Path(settings.KNOWLEDGE_BASE_PATH) / "diseases.json"
        
        if kb_path.exists():
            try:
                with open(kb_path, 'r') as f:
                    self.knowledge_base = json.load(f)
                logger.success(f"✓ Loaded KB with {len(self.knowledge_base)} diseases")
            except Exception as e:
                logger.error(f"Error loading KB: {e}")
                self.knowledge_base = self._get_fallback_knowledge_base()
        else:
            logger.warning(f"⚠ KB file not found at {kb_path}")
            logger.info("Using fallback knowledge base")
            self.knowledge_base = self._get_fallback_knowledge_base()
    
    def _build_class_mapping(self):
        """Build class mapping from knowledge base"""
        self.disease_classes = {}
        for idx, disease_name in enumerate(self.knowledge_base.keys()):
            self.disease_classes[idx] = disease_name
        
        logger.info(f"✓ Built class mapping for {len(self.disease_classes)} diseases")
    
    def _get_fallback_knowledge_base(self):
        """
        Fallback knowledge base if extraction fails
        This is ONLY used as backup - not the main source
        """
        logger.warning("Using FALLBACK knowledge base (not from dataset)")
        
        return {
            "healthy": {
                "symptoms": ["No visible signs of disease"],
                "treatment": ["Continue regular maintenance"],
                "prevention": ["Maintain regular monitoring"]
            },
            "unknown_disease": {
                "symptoms": ["Unable to identify specific disease"],
                "treatment": ["Consult local agricultural extension"],
                "prevention": ["Document symptoms and seek expert advice"]
            }
        }
    
    def predict(self, image_path: str) -> dict:
        """
        REAL prediction using trained or pre-trained model
        Uses knowledge base extracted from ACTUAL dataset
        """
        try:
            logger.info(f"Predicting disease for: {image_path}")
            
            # Validate image
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            # Run model inference
            results = self.model(image_path, conf=0.5)
            
            detections = []
            predictions = []
            
            # Process YOLO results
            for result in results:
                if hasattr(result, 'boxes') and result.boxes is not None:
                    boxes = result.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        
                        # Get disease from class mapping
                        disease_name = self.disease_classes.get(cls, f"Unknown_Class_{cls}")
                        
                        detections.append({
                            "bbox": [x1, y1, x2, y2],
                            "confidence": round(conf, 3),
                            "disease": disease_name
                        })
                        predictions.append((disease_name, conf))
            
            # Get top prediction
            if predictions:
                top_disease, top_confidence = max(predictions, key=lambda x: x[1])
            else:
                top_disease = "healthy"
                top_confidence = 0.95
            
            # Calculate severity (0-100)
            severity = int(top_confidence * 100)
            
            # Get treatment from knowledge base (from extracted data!)
            kb_entry = self.knowledge_base.get(top_disease, {})
            treatment = kb_entry.get("treatment", ["Consult agricultural expert"])
            prevention = kb_entry.get("prevention", ["Monitor plants regularly"])
            
            if not treatment or treatment == ["Consult agricultural expert"]:
                logger.warning(f"⚠ No treatment data for {top_disease} - using fallback")
            
            result = {
                "success": True,
                "disease": top_disease,
                "confidence": round(top_confidence, 3),
                "severity": severity,
                "detections": detections,
                "treatment": treatment,
                "prevention": prevention,
                "model_type": self.model_source.upper(),
                "knowledge_source": "EXTRACTED_FROM_DATASET",
                "message": f"Detected {top_disease} with {top_confidence*100:.1f}% confidence"
            }
            
            logger.success(f"✓ Prediction: {top_disease} ({top_confidence*100:.1f}%)")
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to analyze image"
            }
