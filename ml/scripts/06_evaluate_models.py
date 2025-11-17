#!/usr/bin/env python3
"""
Evaluate the trained YOLO CLASSIFICATION model.
This script is now synchronized with the 04_train_yolo.py (classification) script.
"""

import torch
from ultralytics import YOLO
from pathlib import Path
import json
import sys  # <-- Make sure this import is here

class ModelEvaluator:
    def __init__(self):
        # This path is correct and points to your new classification model
        self.model_path = Path("../models/yolo_classification/disease_classifier_v1/weights/best.pt")
        
        # This is the path to your data folder (contains train/val/test)
        self.data_path = Path("../data/processed")
        
        # --- FIX 1: Correct results path ---
        # This is where the final report will be saved
        self.results_path = Path("../models/yolo_classification/disease_classifier_v1/evaluation_results.json")
        self.results_path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists

    def load_model(self):
        """Load trained YOLO model"""
        if not self.model_path.exists():
            print(f"❌ Model not found at {self.model_path}")
            print("Run training first (04_train_yolo.py)")
            return None
                
        print(f"\n✓ Loading model: {self.model_path}")
        model = YOLO(str(self.model_path))
        return model

    def evaluate(self):
        """Evaluate model on the 'test' set"""
        print("\n" + "="*70)
        print("📊 MODEL EVALUATION")
        print("="*70)
                
        model = self.load_model()
        if not model:
            return False
                
        print(f"\n🧪 Evaluating on TEST set (this may take 10-15 minutes)...")
        print(f"   Data path: {self.data_path}")
        
        try:
            # --- FIX 2: Run a CLASSIFICATION evaluation ---
            # We must call model.val() using the same settings as training
            results = model.val(
                data=str(self.data_path),  # Point to the main processed folder
                split='test',             # Explicitly tell it to use the 'test' split
                imgsz=224,                # Must match your training imgsz
                batch=16,                 # Match your training batch
                workers=0,
                device=0 if torch.cuda.is_available() else 'cpu'
            )
            # --- END OF FIX ---
            
            # --- FIX 3: Extract CLASSIFICATION metrics ---
            metrics = {
                "top1_accuracy": float(results.top1),
                "top5_accuracy": float(results.top5),
                "test_set": str(self.data_path / "test"),
                "model_path": str(self.model_path)
            }
            # --- END OF FIX ---
                        
            print("\n" + "="*70)
            print("📈 EVALUATION RESULTS (ON TEST SET)")
            print("="*70)
            # --- FIX 4: Display CLASSIFICATION metrics ---
            print(f"   Top-1 Accuracy: {metrics['top1_accuracy'] * 100:.2f}%")
            print(f"   Top-5 Accuracy: {metrics['top5_accuracy'] * 100:.2f}%")
            # --- END OF FIX ---
                        
            # Save results
            with open(self.results_path, 'w') as f:
                json.dump(metrics, f, indent=2)
                        
            print(f"\n✓ Results saved to: {self.results_path}")
            return True
            
        except Exception as e:
            print(f"\n❌ Evaluation failed: {str(e)}")
            return False

    # --- FIX 5: This function was for DETECTION, this is the CLASSIFICATION version ---
    def test_single_image(self, image_path: str):
        """Test model on single image"""
        print(f"\n🖼️  Testing on image: {image_path}")
        
        model = self.load_model()
        if not model:
            return
            
        try:
            # Run CLASSIFICATION inference
            results = model(image_path, conf=0.5)
            
            # Print CLASSIFICATION results
            for result in results:
                print(f"\n✓ Classification results:")
                # Get top 1
                top1_idx = result.probs.top1
                top1_name = result.names[top1_idx]
                top1_conf = result.probs.top1conf
                print(f"   Top 1: {top1_name} (Confidence: {top1_conf:.3f})")

                # Get top 5
                print("\n   Top 5 Predictions:")
                top5_indices = result.probs.top5
                top5_confs = result.probs.top5conf
                for i in range(len(top5_indices)):
                    name = result.names[top5_indices[i]]
                    conf = top5_confs[i]
                    print(f"   {i+1}. {name} (Confidence: {conf:.3f})")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    # --- END OF FIX ---

if __name__ == "__main__":
    evaluator = ModelEvaluator()
    
    # Evaluate on test set
    success = evaluator.evaluate()
        
    if success:
        print("\n✅ Evaluation complete!")
    else:
        print("\n✗ Evaluation failed")
    
    sys.exit(0 if success else 1)



# #!/usr/bin/env python3
# """
# Evaluate trained YOLO model performance
# """

# import torch
# from ultralytics import YOLO
# from pathlib import Path
# import json
# import numpy as np
# from PIL import Image

# class ModelEvaluator:
#     def __init__(self):
#         self.model_path = Path("../models/yolo_classification/disease_classifier_v1/weights/best.pt")
#         self.test_path = Path("../data/processed/test")
#         self.results_path = Path("../models/yolo/disease_detector_v1/results.json")
    
#     def load_model(self):
#         """Load trained YOLO model"""
#         if not self.model_path.exists():
#             print(f"❌ Model not found at {self.model_path}")
#             print("Run training first (04_train_yolo.py)")
#             return None
        
#         print(f"\n✓ Loading model: {self.model_path}")
#         model = YOLO(str(self.model_path))
#         return model
    
#     def evaluate(self):
#         """Evaluate model on test set"""
#         print("\n" + "="*70)
#         print("📊 MODEL EVALUATION")
#         print("="*70)
        
#         # Load model
#         model = self.load_model()
#         if not model:
#             return False
        
#         # Evaluate on test set
#         print(f"\n🧪 Evaluating on test set ({self.test_path})...")
        
#         try:
#             # YOLO's built-in validation
#             results = model.val(
#                 data="../data/dataset.yaml",
#                 imgsz=640,
#                 batch=16,
#                 device=0 if torch.cuda.is_available() else 'cpu'
#             )
            
#             # Extract metrics
#             metrics = {
#                 "accuracy": float(results.top1),
#                 "map50": float(results.box.map50),
#                 "map": float(results.box.map),
#                 "precision": float(results.box.mp),
#                 "recall": float(results.box.mr),
#                 "test_set": str(self.test_path),
#                 "model_path": str(self.model_path)
#             }
            
#             # Display results
#             print("\n" + "="*70)
#             print("📈 EVALUATION RESULTS")
#             print("="*70)
#             print(f"Accuracy:   {metrics['accuracy']:.4f}")
#             print(f"mAP@0.5:    {metrics['map50']:.4f}")
#             print(f"mAP@0.5-0.95: {metrics['map']:.4f}")
#             print(f"Precision:  {metrics['precision']:.4f}")
#             print(f"Recall:     {metrics['recall']:.4f}")
            
#             # Save results
#             with open(self.results_path, 'w') as f:
#                 json.dump(metrics, f, indent=2)
            
#             print(f"\n✓ Results saved to: {self.results_path}")
            
#             return True
            
#         except Exception as e:
#             print(f"\n❌ Evaluation failed: {str(e)}")
#             return False
    
#     def test_single_image(self, image_path: str):
#         """Test model on single image"""
#         print(f"\n🖼️  Testing on image: {image_path}")
        
#         model = self.load_model()
#         if not model:
#             return
        
#         try:
#             # Run inference
#             results = model(image_path, conf=0.5)
            
#             # Print results
#             for result in results:
#                 print(f"\n✓ Detection results:")
#                 for box in result.boxes:
#                     print(f"   Class: {box.cls[0]} ({result.names[int(box.cls[0])]})")
#                     print(f"   Confidence: {box.conf[0]:.3f}")
#                     print(f"   Box: {box.xyxy[0].tolist()}")
            
#         except Exception as e:
#             print(f"❌ Error: {str(e)}")

# if __name__ == "__main__":
#     evaluator = ModelEvaluator()
    
#     # Evaluate on test set
#     success = evaluator.evaluate()
    
#     if success:
#         print("\n✓ Evaluation complete!")
#     else:
#         print("\n✗ Evaluation failed")
