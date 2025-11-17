#!/usr/bin/env python3
"""
Train a YOLO CLASSIFICATION model on the agricultural dataset.
This is the CORRECT task for your data (labeled by folders).
"""

import torch
from ultralytics import YOLO
from pathlib import Path
import sys

class YOLOTrainer:
    def __init__(self):
        # Point to the parent 'ml' folder
        self.base_path = Path("..")
        # Point to the folder containing train/val/test
        self.data_path = self.base_path / "data/processed"
        # Point to where models will be saved
        self.models_path = self.base_path / "models/yolo_classification"
        self.models_path.mkdir(parents=True, exist_ok=True)

    def train(self):
        """Train YOLO Classification model"""
        print("\n" + "="*70)
        print("🚀 YOLO CLASSIFICATION MODEL TRAINING")
        print("="*70)

        print(f"\n⚙️  GPU Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   Device: {torch.cuda.get_device_name(0)}")
        else:
            print("   ⚠️  GPU not available - training will be slower on CPU")

        # --- THIS IS THE CRITICAL FIX ---
        # We load a CLASSIFICATION model ('-cls'), not a detection model.
        print("\n📦 Loading YOLOv8 medium-classification model (yolov8m-cls.pt)...")
        try:
            model = YOLO('yolov8m-cls.pt')
        except Exception as e:
            print(f"❌ Failed to load YOLO model: {e}")
            sys.exit(1)
        # --- END OF FIX ---

        print("\n⏳ Starting training (2-4 hours on GPU, longer on CPU)...")
        print("   Do NOT close this terminal!")

        try:
            results = model.train(
                # --- THIS IS THE SECOND CRITICAL FIX ---
                # Classification training just needs the main data folder.
                # It automatically finds /train, /val, and /test.
                data=str(self.data_path),
                # --- END OF FIX ---
                
                epochs=50,
                imgsz=224,  # 224 is standard for classification
                batch=32,   # Can often use a larger batch size for classification
                patience=10,
                device=0 if torch.cuda.is_available() else 'cpu',
                save=True,
                project=str(self.models_path),
                name='disease_classifier_v1'
            )

            print("\n" + "="*70)
            print("✅ CLASSIFICATION TRAINING COMPLETE!")
            print("="*70)
            print(f"📂 Best Model:  {self.models_path}/disease_classifier_v1/weights/best.pt")
            return True

        except Exception as e:
            print(f"\n❌ Training failed: {str(e)}")
            return False

if __name__ == "__main__":
    trainer = YOLOTrainer()
    success = trainer.train()
    sys.exit(0 if success else 1)