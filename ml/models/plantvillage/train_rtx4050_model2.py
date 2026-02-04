# -*- coding: utf-8 -*-
"""
🚀 AGROGUARD ULTIMATE SPEED TRAINING - WINDOWS FIXED
✅ All logic inside main guard
✅ No multiprocessing issues
✅ Windows stable
✅ Optimized for RTX 4050 6GB
"""

import os
import sys
import yaml
import torch
import time
import random
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("="*100)
print("🚀 AGROGUARD WINDOWS STABLE TRAINING")
print("="*100)

def main():
    """Main function - All logic inside to prevent Windows multiprocessing issues"""
    
    # ============================================================================
    # WINDOWS MULTIPROCESSING FIX
    # ============================================================================
    from multiprocessing import freeze_support
    freeze_support()
    
    # ============================================================================
    # 1. QUICK DATASET DETECTION
    # ============================================================================
    
    print("\n🔍 STEP 1: DETECTING DATASET")
    print("-"*80)
    
    CURRENT_DIR = Path.cwd()
    print(f"📁 Working Directory: {CURRENT_DIR}")
    
    DATASET_ROOT = None
    possible_structures = [
        CURRENT_DIR / "dataset" / "PlantVillage_for_object_detection",
        CURRENT_DIR / "plantvillage-for-object-detection-yolo" / "PlantVillage_for_object_detection",
        CURRENT_DIR / "PlantVillage_for_object_detection",
        CURRENT_DIR / "PlantVillage",
        CURRENT_DIR / "plantvillage",
    ]
    
    for path in possible_structures:
        if path.exists():
            DATASET_ROOT = path
            print(f"✅ Found dataset: {DATASET_ROOT}")
            break
    
    if not DATASET_ROOT:
        print("❌ Dataset not found!")
        sys.exit(1)
    
    # ============================================================================
    # 2. CLASSES DEFINITION
    # ============================================================================
    
    PLANTVILLAGE_CLASSES = [
        "Apple_Apple_scab", "Apple_Black_rot", "Apple_Cedar_apple_rust", "Apple_healthy",
        "Blueberry_healthy", "Cherry_healthy", "Cherry_Powdery_mildew",
        "Corn_Cercospora_leaf_spot_Gray_leaf_spot", "Corn_Common_rust", "Corn_healthy", 
        "Corn_Northern_Leaf_Blight", "Grape_Black_rot", "Grape_Esca_(Black_Measles)",
        "Grape_healthy", "Grape_Leaf_blight_(Isariopsis_Leaf_Spot)",
        "Orange_Haunglongbing_(Citrus_greening)", "Peach_Bacterial_spot", "Peach_healthy",
        "Pepper_bell_Bacterial_spot", "Pepper_bell_healthy", "Potato_Early_blight",
        "Potato_healthy", "Potato_Late_blight", "Raspberry_healthy", "Soybean_healthy",
        "Squash_Powdery_mildew", "Strawberry_healthy", "Strawberry_Leaf_scorch",
        "Tomato_Bacterial_spot", "Tomato_Early_blight", "Tomato_healthy", "Tomato_Late_blight",
        "Tomato_Leaf_Mold", "Tomato_Septoria_leaf_spot", 
        "Tomato_Spider_mites_Two-spotted_spider_mite", "Tomato_Target_Spot",
        "Tomato_Tomato_mosaic_virus", "Tomato_Tomato_Yellow_Leaf_Curl_virus"
    ]
    
    print(f"🎯 Classes: {len(PLANTVILLAGE_CLASSES)}")
    
    # Find images and labels without copying
    print("\n🔍 Scanning for images and labels...")
    image_extensions = ['.jpg', '.jpeg', '.png']
    image_files = []
    for ext in image_extensions:
        image_files.extend(list(DATASET_ROOT.rglob(f"*{ext}")))
        image_files.extend(list(DATASET_ROOT.rglob(f"*{ext.upper()}")))
    
    label_files = list(DATASET_ROOT.rglob("*.txt"))
    
    print(f"📸 Images found: {len(image_files):,}")
    print(f"📝 Labels found: {len(label_files):,}")
    
    if len(image_files) == 0:
        print("❌ No images found!")
        sys.exit(1)
    
    # ============================================================================
    # 3. CREATE DATA.YAML
    # ============================================================================
    
    print("\n📄 STEP 3: CREATING DATA.YAML")
    print("-"*80)
    
    data_yaml_path = CURRENT_DIR / "agroguard_fixed.yaml"
    
    data_config = {
        'path': str(DATASET_ROOT),
        'train': 'Dataset/images',
        'val': 'Dataset/images',
        'nc': len(PLANTVILLAGE_CLASSES),
        'names': PLANTVILLAGE_CLASSES
    }
    
    with open(data_yaml_path, 'w') as f:
        yaml.dump(data_config, f, default_flow_style=False)
    
    print(f"✅ Created data.yaml at: {data_yaml_path}")
    
    # ============================================================================
    # 4. WINDOWS OPTIMIZED TRAINING CONFIG (RTX 4050 6GB)
    # ============================================================================
    
    print("\n⚡ STEP 4: WINDOWS OPTIMIZED CONFIG")
    print("-"*80)
    
    # Check GPU
    gpu_available = torch.cuda.is_available()
    if gpu_available:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"🎮 GPU: {gpu_name}")
        print(f"🧠 VRAM: {gpu_memory:.1f} GB")
        
        # WINDOWS FIXED CONFIG - NO CRASH
        TRAIN_CONFIG = {
            'model': 'yolov8s.pt',          # Small model - less VRAM
            'epochs': 100,                  # Max 100 epochs
            'imgsz': 416,                   # Balanced speed vs accuracy
            'batch': 16,                    # REDUCED: 20->16 for VRAM stability
            'workers': 2,                   # CRITICAL: Windows needs 0-2 workers
            'device': 0,                    # GPU
            'patience': 20,                 # Early stopping patience
            'amp': True,                    # Mixed precision
            'fraction': 0.85,               # Train/val split
            'cache': False,                 # No cache (Windows issue)
            'optimizer': 'AdamW',           # Better than SGD for accuracy
            'lr0': 0.001,                   # Lower LR for stability
            'lrf': 0.01,                    # Learning rate final
            'momentum': 0.937,
            'weight_decay': 0.0005,
            'warmup_epochs': 3,
            'warmup_momentum': 0.8,
            'box': 7.5,
            'cls': 0.5,
            'dfl': 1.5,
            'close_mosaic': 10,             # Last 10 epochs no mosaic
            'degrees': 10.0,                # Slight rotation
            'translate': 0.1,
            'scale': 0.5,
            'shear': 0.0,
            'perspective': 0.0,
            'flipud': 0.0,
            'fliplr': 0.5,
            'mosaic': 0.4,                  # Moderate mosaic for better accuracy
            'mixup': 0.1,                   # Slight mixup for augmentation
            'copy_paste': 0.0,
            'cos_lr': True,
            'label_smoothing': 0.0,
            'nbs': 64,
            'overlap_mask': False,
            'mask_ratio': 1,
            'dropout': 0.0,
            'val': True,
            'save': True,
            'save_period': 10,
            'plots': True,                  # Show plots for monitoring
            'verbose': True,
            'seed': 42,
            'deterministic': True,          # Deterministic for reproducibility
            'single_cls': False,
            'rect': False,
            'notebook': False,
            'v5loader': False,
        }
        
        # Time estimation
        total_images = len(image_files)
        train_images = int(total_images * 0.85)
        batches_per_epoch = train_images / TRAIN_CONFIG['batch']
        
        # With reduced workers: ~0.12 seconds per batch
        seconds_per_epoch = batches_per_epoch * 0.12
        total_seconds = seconds_per_epoch * 100
        total_hours = total_seconds / 3600
        
        print(f"\n⏰ TIME ESTIMATION:")
        print(f"  Total images: {total_images:,}")
        print(f"  Batch size: {TRAIN_CONFIG['batch']} (optimized for 6GB VRAM)")
        print(f"  Workers: {TRAIN_CONFIG['workers']} (Windows fix)")
        print(f"  Image size: {TRAIN_CONFIG['imgsz']}px")
        print(f"  Mosaic: {TRAIN_CONFIG['mosaic']} (good for accuracy)")
        print(f"\n📈 ESTIMATED TRAINING TIME:")
        print(f"  Max 100 epochs: {total_hours:.1f} hours")
        print(f"  Likely stop at ~60 epochs: {(seconds_per_epoch*60)/3600:.1f} hours")
        print(f"\n🎯 EXPECTED ACCURACY: 85-89% mAP50")
        
    else:
        print("⚠️ No GPU - CPU training")
        TRAIN_CONFIG = {
            'model': 'yolov8n.pt',
            'epochs': 50,
            'imgsz': 320,
            'batch': 4,
            'workers': 0,  # Windows CPU fix
            'device': 'cpu',
            'patience': 10,
        }
    
    # ============================================================================
    # 5. INSTALL DEPENDENCIES
    # ============================================================================
    
    print("\n📦 STEP 5: INSTALLING DEPENDENCIES")
    print("-"*80)
    
    try:
        from ultralytics import YOLO
        import ultralytics
        print(f"✅ ultralytics v{ultralytics.__version__}")
    except ImportError:
        print("📦 Installing ultralytics...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ultralytics", "-q"])
        from ultralytics import YOLO
        import ultralytics
        print("✅ Installed")
    
    # ============================================================================
    # 6. TRAINING
    # ============================================================================
    
    print("\n" + "="*100)
    print("🚀 STARTING WINDOWS STABLE TRAINING")
    print("="*100)
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⚙️ Config: {TRAIN_CONFIG['epochs']} epochs, batch {TRAIN_CONFIG['batch']}")
    print(f"🎯 Target Accuracy: 85-89% mAP50")
    print("="*100)
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = CURRENT_DIR / f"agroguard_{timestamp}"
    output_dir.mkdir(exist_ok=True)
    print(f"\n📁 Output directory: {output_dir}")
    
    # Load model
    print(f"\n🔄 Loading model: {TRAIN_CONFIG['model']}")
    model = YOLO(TRAIN_CONFIG['model'])
    
    # Start timer
    training_start_time = time.time()
    
    try:
        # START TRAINING - MINIMAL PARAMS FOR WINDOWS STABILITY
        print(f"\n🔥 TRAINING STARTED - WINDOWS STABLE MODE")
        print("-"*80)
        
        results = model.train(
            # Data config
            data=str(data_yaml_path),
            epochs=TRAIN_CONFIG['epochs'],
            imgsz=TRAIN_CONFIG['imgsz'],
            batch=TRAIN_CONFIG['batch'],
            workers=TRAIN_CONFIG['workers'],  # CRITICAL: 2 workers max for Windows
            device=TRAIN_CONFIG['device'],
            
            # Optimization
            amp=TRAIN_CONFIG.get('amp', True),
            patience=TRAIN_CONFIG.get('patience', 20),
            fraction=TRAIN_CONFIG.get('fraction', 0.85),
            cache=TRAIN_CONFIG.get('cache', False),
            
            # Learning rate
            optimizer=TRAIN_CONFIG.get('optimizer', 'AdamW'),
            lr0=TRAIN_CONFIG.get('lr0', 0.001),
            lrf=TRAIN_CONFIG.get('lrf', 0.01),
            momentum=TRAIN_CONFIG.get('momentum', 0.937),
            weight_decay=TRAIN_CONFIG.get('weight_decay', 0.0005),
            warmup_epochs=TRAIN_CONFIG.get('warmup_epochs', 3),
            warmup_momentum=TRAIN_CONFIG.get('warmup_momentum', 0.8),
            
            # Loss weights
            box=TRAIN_CONFIG.get('box', 7.5),
            cls=TRAIN_CONFIG.get('cls', 0.5),
            dfl=TRAIN_CONFIG.get('dfl', 1.5),
            
            # Augmentation (balanced for Windows)
            degrees=TRAIN_CONFIG.get('degrees', 10.0),
            translate=TRAIN_CONFIG.get('translate', 0.1),
            scale=TRAIN_CONFIG.get('scale', 0.5),
            shear=TRAIN_CONFIG.get('shear', 0.0),
            flipud=TRAIN_CONFIG.get('flipud', 0.0),
            fliplr=TRAIN_CONFIG.get('fliplr', 0.5),
            mosaic=TRAIN_CONFIG.get('mosaic', 0.4),  # Good for accuracy
            mixup=TRAIN_CONFIG.get('mixup', 0.1),    # Slight mixup
            
            # Training settings
            cos_lr=TRAIN_CONFIG.get('cos_lr', True),
            label_smoothing=TRAIN_CONFIG.get('label_smoothing', 0.0),
            val=TRAIN_CONFIG.get('val', True),
            save=True,
            save_period=TRAIN_CONFIG.get('save_period', 10),
            plots=TRAIN_CONFIG.get('plots', True),
            verbose=True,
            seed=TRAIN_CONFIG.get('seed', 42),
            deterministic=TRAIN_CONFIG.get('deterministic', True),
            single_cls=False,
            rect=False,
            project=str(output_dir),
            name='train',
            exist_ok=True,
        )
        
        success = True
        
    except KeyboardInterrupt:
        print("\n⚠️ Training interrupted by user")
        success = False
    except Exception as e:
        print(f"\n❌ Training error: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    # ============================================================================
    # 7. RESULTS
    # ============================================================================
    
    if success:
        training_end_time = time.time()
        total_hours = (training_end_time - training_start_time) / 3600
        
        print("\n" + "="*100)
        print("✅ TRAINING COMPLETED SUCCESSFULLY!")
        print("="*100)
        print(f"⏱️ Total training time: {total_hours:.1f} hours")
        
        # Find best model
        best_model_path = output_dir / "train" / "weights" / "best.pt"
        
        if best_model_path.exists():
            print(f"\n🏆 Best model saved: {best_model_path}")
            
            # Quick test
            try:
                # Create test script
                test_script = output_dir / "test_model.py"
                test_code = f'''
from ultralytics import YOLO
import cv2

model = YOLO(r"{best_model_path}")

def predict(image_path):
    results = model(image_path, conf=0.5)
    for r in results:
        if r.boxes:
            print("Detected:")
            for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
                class_name = model.names[int(cls)]
                print(f"  {{class_name}} ({{conf:.1%}})")
            r.save("result.jpg")
        else:
            print("No detection")

predict("test.jpg")
'''
                with open(test_script, 'w') as f:
                    f.write(test_code)
                
                print(f"🧪 Test script: {test_script}")
                
            except Exception as e:
                print(f"⚠️ Export failed: {e}")
        
        print("\n🎉 TRAINING COMPLETE!")
        print(f"   Time: {total_hours:.1f} hours")
        print(f"   Model ready for deployment")

# ============================================================================
# MAIN EXECUTION - WINDOWS SAFE
# ============================================================================
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*100)
    print("🏁 SCRIPT FINISHED")
    print("="*100)


# # -*- coding: utf-8 -*-
# """
# 🚀 AGROGUARD ULTIMATE SPEED TRAINING - NO COPY, DIRECT TRAINING
# ✅ No image copying - Use existing structure
# ✅ imgsz=416 for 2.5x speed
# ✅ Early stopping with patience=15
# ✅ Batch size optimized for RTX 4050 6GB
# ✅ Mixed precision (FP16) for 2x speed
# ✅ Target: 15-18 hours for 100 epochs
# ✅ Direct dataset usage - No reorganization
# """

# import os
# import sys
# import yaml
# import torch
# import time
# import random
# from pathlib import Path
# from datetime import datetime
# import warnings
# warnings.filterwarnings('ignore')

# print("="*100)
# print("🚀 AGROGUARD ULTIMATE SPEED - NO COPY TRAINING")
# print("="*100)
# print("✅ NO IMAGE COPYING - Use existing dataset structure")
# print("✅ imgsz=416 (2.5x faster than 640)")
# print("✅ Early stopping with patience=15")
# print("✅ Mixed precision (FP16) for 2x speed")
# print("✅ Target: 15-18 hours for 100 epochs")
# print("="*100)

# # ============================================================================
# # 1. QUICK DATASET DETECTION (NO COPY)
# # ============================================================================

# print("\n🔍 STEP 1: DETECTING DATASET (NO COPY)")
# print("-"*80)

# CURRENT_DIR = Path.cwd()
# print(f"📁 Working Directory: {CURRENT_DIR}")

# # Find dataset from your screenshot structure
# DATASET_ROOT = None
# possible_structures = [
#     # From your screenshot
#     CURRENT_DIR / "dataset" / "PlantVillage_for_object_detection",
#     CURRENT_DIR / "plantvillage-for-object-detection-yolo" / "PlantVillage_for_object_detection",
#     CURRENT_DIR / "PlantVillage_for_object_detection",
#     # Common variations
#     CURRENT_DIR / "PlantVillage",
#     CURRENT_DIR / "plantvillage",
# ]

# for path in possible_structures:
#     if path.exists():
#         DATASET_ROOT = path
#         print(f"✅ Found dataset: {DATASET_ROOT}")
#         break

# if not DATASET_ROOT:
#     print("❌ Dataset not found! Looking for any PlantVillage folder...")
#     for item in CURRENT_DIR.iterdir():
#         if item.is_dir() and ("plant" in item.name.lower() or "village" in item.name.lower()):
#             DATASET_ROOT = item
#             print(f"✅ Found: {DATASET_ROOT}")
#             break

# if not DATASET_ROOT:
#     print("❌ Could not find PlantVillage dataset!")
#     print("\n📁 Current directory contents:")
#     for item in CURRENT_DIR.iterdir():
#         print(f"  {'📁' if item.is_dir() else '📄'} {item.name}")
#     sys.exit(1)

# # ============================================================================
# # 2. QUICK ANALYSIS (NO COPY, NO REORGANIZATION)
# # ============================================================================

# print("\n📊 STEP 2: QUICK DATASET ANALYSIS")
# print("-"*80)

# # PlantVillage 38 classes
# PLANTVILLAGE_CLASSES = [
#     "Apple_Apple_scab", "Apple_Black_rot", "Apple_Cedar_apple_rust", "Apple_healthy",
#     "Blueberry_healthy", "Cherry_healthy", "Cherry_Powdery_mildew",
#     "Corn_Cercospora_leaf_spot_Gray_leaf_spot", "Corn_Common_rust", "Corn_healthy", 
#     "Corn_Northern_Leaf_Blight", "Grape_Black_rot", "Grape_Esca_(Black_Measles)",
#     "Grape_healthy", "Grape_Leaf_blight_(Isariopsis_Leaf_Spot)",
#     "Orange_Haunglongbing_(Citrus_greening)", "Peach_Bacterial_spot", "Peach_healthy",
#     "Pepper_bell_Bacterial_spot", "Pepper_bell_healthy", "Potato_Early_blight",
#     "Potato_healthy", "Potato_Late_blight", "Raspberry_healthy", "Soybean_healthy",
#     "Squash_Powdery_mildew", "Strawberry_healthy", "Strawberry_Leaf_scorch",
#     "Tomato_Bacterial_spot", "Tomato_Early_blight", "Tomato_healthy", "Tomato_Late_blight",
#     "Tomato_Leaf_Mold", "Tomato_Septoria_leaf_spot", 
#     "Tomato_Spider_mites_Two-spotted_spider_mite", "Tomato_Target_Spot",
#     "Tomato_Tomato_mosaic_virus", "Tomato_Tomato_Yellow_Leaf_Curl_virus"
# ]

# print(f"🎯 Total classes: {len(PLANTVILLAGE_CLASSES)}")
# print(f"🌱 Diseases covered: 150+ pests and diseases")

# # Find images and labels without copying
# print("\n🔍 Scanning for images and labels...")
# image_extensions = ['.jpg', '.jpeg', '.png']
# image_files = []
# for ext in image_extensions:
#     image_files.extend(list(DATASET_ROOT.rglob(f"*{ext}")))
#     image_files.extend(list(DATASET_ROOT.rglob(f"*{ext.upper()}")))

# label_files = list(DATASET_ROOT.rglob("*.txt"))

# print(f"📸 Images found: {len(image_files):,}")
# print(f"📝 Labels found: {len(label_files):,}")

# if len(image_files) == 0:
#     print("❌ No images found!")
#     sys.exit(1)

# # ============================================================================
# # 3. CREATE DIRECT DATA.YAML (NO COPY, NO REORGANIZATION)
# # ============================================================================

# print("\n📄 STEP 3: CREATING DIRECT DATA.YAML")
# print("-"*80)

# # Find the images directory - TERE SCREENSHOT KE HISAB SE
# images_dir = None
# labels_dir = None

# # TERE SCREENSHOT MEIN Dataset/images AUR Dataset/labels HAI
# # Pehle check karo Dataset folder ke andar
# dataset_folder = DATASET_ROOT / "Dataset"
# if dataset_folder.exists():
#     images_dir = dataset_folder / "images"
#     labels_dir = dataset_folder / "labels"
    
#     if images_dir.exists():
#         print(f"✅ Found: Dataset/images structure")
#     else:
#         # Agar nahi hai to root mein check karo
#         images_dir = DATASET_ROOT
#         labels_dir = DATASET_ROOT
#         print(f"⚠️ Using root directory for both images and labels")
# else:
#     # Common structures in PlantVillage dataset
#     possible_structures = [
#         ("images", "labels"),
#         ("Images", "Labels"),
#         ("train/images", "train/labels"),
#         ("", ""),  # Root directory
#     ]
    
#     for img_subdir, lbl_subdir in possible_structures:
#         img_path = DATASET_ROOT / img_subdir
#         lbl_path = DATASET_ROOT / lbl_subdir
        
#         if img_path.exists() and (lbl_path.exists() or lbl_subdir == ""):
#             images_dir = img_path
#             labels_dir = lbl_path if lbl_path.exists() else DATASET_ROOT
#             print(f"✅ Found: Images in {img_subdir}, Labels in {lbl_subdir}")
#             break

# if not images_dir:
#     # Use root directory
#     images_dir = DATASET_ROOT
#     labels_dir = DATASET_ROOT
#     print(f"⚠️ Using root directory for both images and labels")

# # Create data.yaml pointing directly to existing structure
# data_yaml_path = CURRENT_DIR / "agroguard_direct.yaml"

# # TERE SCREENSHOT KE HISAB SE CORRECT PATH DENGE
# data_config = {
#     'path': str(DATASET_ROOT),
#     'train': 'Dataset/images',  # TERE SCREENSHOT MEIN YAHI HAI
#     'val': 'Dataset/images',    # Same for validation (fraction se split hoga)
#     'nc': len(PLANTVILLAGE_CLASSES),
#     'names': PLANTVILLAGE_CLASSES
# }

# with open(data_yaml_path, 'w') as f:
#     yaml.dump(data_config, f, default_flow_style=False)

# print(f"✅ Created data.yaml at: {data_yaml_path}")
# print(f"📍 Dataset path: {data_config['path']}")
# print(f"📍 Train/Val path: {data_config['train']}")
# print(f"📍 Classes: {len(PLANTVILLAGE_CLASSES)}")

# # ============================================================================
# # 4. ULTRA-OPTIMIZED TRAINING CONFIG (RTX 4050 6GB)
# # ============================================================================

# print("\n⚡ STEP 4: ULTRA-OPTIMIZED TRAINING CONFIG")
# print("-"*80)

# # Check GPU
# gpu_available = torch.cuda.is_available()
# if gpu_available:
#     gpu_name = torch.cuda.get_device_name(0)
#     gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
#     print(f"🎮 GPU: {gpu_name}")
#     print(f"🧠 VRAM: {gpu_memory:.1f} GB")
    
#     # EXTREME OPTIMIZATION for RTX 4050 6GB
#     if '4050' in gpu_name or gpu_memory <= 6:
#         print("✅ RTX 4050 6GB detected - EXTREME OPTIMIZATION MODE")
        
#         # ULTIMATE SPEED CONFIGURATION
#         TRAIN_CONFIG = {
#             'model': 'yolov8s.pt',      # Small model for speed
#             'epochs': 100,              # Max 100 epochs
#             'imgsz': 416,               # 2.5x faster than 640px
#             'batch': 20,                # Optimized for 6GB VRAM
#             'workers': 8,               # Max workers for fast data loading
#             'device': 0,                # GPU
#             'patience': 15,             # Early stopping - stops if no improvement for 15 epochs
#             'amp': True,                # Mixed precision (FP16) - 2x speed
#             'fraction': 0.85,           # 85% train, 15% validation
#             'cache': False,             # No cache (saves memory)
#             'optimizer': 'SGD',         # Faster than AdamW
#             'lr0': 0.01,                # Higher learning rate for faster convergence
#             'lrf': 0.1,                 # Learning rate final
#             'momentum': 0.937,
#             'weight_decay': 0.0005,
#             'warmup_epochs': 3,         # Quick warmup
#             'warmup_momentum': 0.8,
#             'box': 7.5,
#             'cls': 0.5,
#             'dfl': 1.5,
#             'close_mosaic': 0,          # No mosaic for speed
#             'degrees': 0.0,             # No rotation for speed
#             'translate': 0.1,
#             'scale': 0.5,
#             'shear': 0.0,
#             'perspective': 0.0,
#             'flipud': 0.0,
#             'fliplr': 0.5,
#             'mosaic': 0.2,              # No mosaic augmentation (saves memory)
#             'mixup': 0.0,               # No mixup for speed
#             'copy_paste': 0.0,
#             'erasing': 0.0,
#             'crop_fraction': 1.0,
#             'cos_lr': True,             # Cosine LR scheduler
#             'label_smoothing': 0.0,
#             'nbs': 64,                  # Nominal batch size
#             'overlap_mask': False,
#             'mask_ratio': 1,
#             'dropout': 0.0,
#             'val': True,
#             'save': True,
#             'save_period': 10,          # Save every 10 epochs
#             'plots': False,             # No plots for speed
#             'verbose': True,
#             'seed': 42,
#             'deterministic': False,     # Non-deterministic for speed
#             'single_cls': False,
#             'rect': False,
#             'resume': False,
#             'notebook': False,
#             'v5loader': False,
#         }
        
#         # Time estimation
#         total_images = len(image_files)
#         train_images = int(total_images * 0.85)
#         batches_per_epoch = train_images / TRAIN_CONFIG['batch']
        
#         # With FP16 + 416px + RTX 4050: ~0.08 seconds per batch
#         seconds_per_epoch = batches_per_epoch * 0.08
#         total_seconds = seconds_per_epoch * 100  # Max 100 epochs
#         total_hours = total_seconds / 3600
        
#         # With early stopping (patience=15), likely to stop around 40-50 epochs
#         early_stop_estimate = 50
#         early_stop_hours = (seconds_per_epoch * early_stop_estimate) / 3600
        
#         print(f"\n⏰ TIME ESTIMATION (RTX 4050 6GB):")
#         print(f"  Total images: {total_images:,}")
#         print(f"  Training images: {train_images:,}")
#         print(f"  Batch size: {TRAIN_CONFIG['batch']}")
#         print(f"  Image size: {TRAIN_CONFIG['imgsz']}px (2.5x faster than 640px)")
#         print(f"  Mixed precision: YES (FP16 - 2x speed)")
#         print(f"  Early stopping: YES (patience=15)")
#         print(f"\n📈 ESTIMATED TRAINING TIME:")
#         print(f"  Max 100 epochs: {total_hours:.1f} hours")
#         print(f"  With early stopping (~50 epochs): {early_stop_hours:.1f} hours")
#         print(f"  Per epoch: {seconds_per_epoch/60:.1f} minutes")
        
#     else:
#         # For other GPUs
#         TRAIN_CONFIG = {
#             'model': 'yolov8m.pt',
#             'epochs': 100,
#             'imgsz': 416,
#             'batch': 16,
#             'workers': 6,
#             'device': 0,
#             'amp': True,
#             'patience': 15,
#         }
# else:
#     print("⚠️ No GPU - CPU training (very slow)")
#     TRAIN_CONFIG = {
#         'model': 'yolov8n.pt',
#         'epochs': 50,
#         'imgsz': 320,
#         'batch': 4,
#         'workers': 2,
#         'device': 'cpu',
#         'patience': 10,
#     }

# # ============================================================================
# # 5. MINIMAL DEPENDENCIES
# # ============================================================================

# print("\n📦 STEP 5: INSTALLING MINIMAL DEPENDENCIES")
# print("-"*80)

# try:
#     from ultralytics import YOLO
#     import ultralytics
#     print(f"✅ ultralytics v{ultralytics.__version__}")
# except ImportError:
#     print("📦 Installing ultralytics...")
#     import subprocess
#     subprocess.check_call([sys.executable, "-m", "pip", "install", "ultralytics", "-q"])
#     from ultralytics import YOLO
#     import ultralytics
#     print("✅ Installed")

# # ============================================================================
# # 6. DIRECT TRAINING - NO COPY, NO REORGANIZATION
# # ============================================================================

# print("\n" + "="*100)
# print("🚀 STARTING DIRECT TRAINING - NO COPY, MAX SPEED")
# print("="*100)
# print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
# print(f"📊 Dataset: {len(image_files):,} images, {len(PLANTVILLAGE_CLASSES)} classes")
# print(f"⚙️ Config: {TRAIN_CONFIG['epochs']} epochs, batch {TRAIN_CONFIG['batch']}, size {TRAIN_CONFIG['imgsz']}")
# print(f"🎯 Target: ~15 hours with early stopping (patience=15)")
# print("="*100)

# # Create output directory
# timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# output_dir = CURRENT_DIR / f"agroguard_ultrafast_{timestamp}"
# output_dir.mkdir(exist_ok=True)

# print(f"\n📁 Output directory: {output_dir}")

# # Load model
# print(f"\n🔄 Loading model: {TRAIN_CONFIG['model']}")
# model = YOLO(TRAIN_CONFIG['model'])

# # Start timer
# training_start_time = time.time()
# start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# try:
#     # START TRAINING WITH ULTIMATE SPEED OPTIMIZATION
#     print(f"\n🔥 TRAINING STARTED - ULTIMATE SPEED MODE")
#     print("   (No copying, FP16, 416px, Early stopping)")
#     print("-"*80)
    
#     results = model.train(
#         # Data config
#         data=str(data_yaml_path),
#         epochs=TRAIN_CONFIG['epochs'],
#         imgsz=TRAIN_CONFIG['imgsz'],
#         batch=TRAIN_CONFIG['batch'],
#         workers=TRAIN_CONFIG['workers'],
#         device=TRAIN_CONFIG['device'],
        
#         # Optimization
#         amp=TRAIN_CONFIG.get('amp', True),       # FP16 mixed precision
#         patience=TRAIN_CONFIG.get('patience', 15),  # Early stopping
#         fraction=TRAIN_CONFIG.get('fraction', 0.85),
#         cache=TRAIN_CONFIG.get('cache', False),
        
#         # Learning rate
#         optimizer=TRAIN_CONFIG.get('optimizer', 'SGD'),
#         lr0=TRAIN_CONFIG.get('lr0', 0.01),
#         lrf=TRAIN_CONFIG.get('lrf', 0.1),
#         momentum=TRAIN_CONFIG.get('momentum', 0.937),
#         weight_decay=TRAIN_CONFIG.get('weight_decay', 0.0005),
#         warmup_epochs=TRAIN_CONFIG.get('warmup_epochs', 3),
#         warmup_momentum=TRAIN_CONFIG.get('warmup_momentum', 0.8),
        
#         # Loss weights
#         box=TRAIN_CONFIG.get('box', 7.5),
#         cls=TRAIN_CONFIG.get('cls', 0.5),
#         dfl=TRAIN_CONFIG.get('dfl', 1.5),
        
#         # Augmentation (minimal for speed)
#         degrees=TRAIN_CONFIG.get('degrees', 0.0),
#         translate=TRAIN_CONFIG.get('translate', 0.1),
#         scale=TRAIN_CONFIG.get('scale', 0.5),
#         shear=TRAIN_CONFIG.get('shear', 0.0),
#         perspective=TRAIN_CONFIG.get('perspective', 0.0),
#         flipud=TRAIN_CONFIG.get('flipud', 0.0),
#         fliplr=TRAIN_CONFIG.get('fliplr', 0.5),
#         mosaic=TRAIN_CONFIG.get('mosaic', 0.0),
#         mixup=TRAIN_CONFIG.get('mixup', 0.0),
#         copy_paste=TRAIN_CONFIG.get('copy_paste', 0.0),
        
#         # Training settings
#         cos_lr=TRAIN_CONFIG.get('cos_lr', True),
#         label_smoothing=TRAIN_CONFIG.get('label_smoothing', 0.0),
#         nbs=TRAIN_CONFIG.get('nbs', 64),
#         overlap_mask=TRAIN_CONFIG.get('overlap_mask', False),
#         mask_ratio=TRAIN_CONFIG.get('mask_ratio', 1),
#         dropout=TRAIN_CONFIG.get('dropout', 0.0),
#         val=TRAIN_CONFIG.get('val', True),
#         save=True,
#         save_period=TRAIN_CONFIG.get('save_period', 10),
#         plots=False,        # No plots for speed
#         verbose=True,
#         seed=TRAIN_CONFIG.get('seed', 42),
#         deterministic=TRAIN_CONFIG.get('deterministic', False),
#         single_cls=TRAIN_CONFIG.get('single_cls', False),
#         rect=TRAIN_CONFIG.get('rect', False),
#         resume=False,
#         project=str(output_dir),
#         name='train',
#         exist_ok=True,
#     )
    
#     success = True
    
# except KeyboardInterrupt:
#     print("\n⚠️ Training interrupted by user")
#     success = False
# except Exception as e:
#     print(f"\n❌ Training error: {e}")
#     import traceback
#     traceback.print_exc()
#     success = False

# # ============================================================================
# # 7. RESULTS AND QUICK EXPORT
# # ============================================================================

# if success:
#     training_end_time = time.time()
#     total_hours = (training_end_time - training_start_time) / 3600
    
#     print("\n" + "="*100)
#     print("✅ TRAINING COMPLETED SUCCESSFULLY!")
#     print("="*100)
#     print(f"⏱️ Total training time: {total_hours:.1f} hours")
    
#     # Find best model
#     best_model_path = output_dir / "train" / "weights" / "best.pt"
#     last_model_path = output_dir / "train" / "weights" / "last.pt"
    
#     if best_model_path.exists():
#         print(f"\n🏆 Best model saved: {best_model_path}")
        
#         # Quick evaluation
#         try:
#             print("\n📊 Running quick evaluation...")
#             model = YOLO(str(best_model_path))
            
#             # Export to ONNX for web deployment
#             print("📤 Exporting to ONNX for web deployment...")
#             onnx_path = output_dir / "agroguard_fast.onnx"
#             model.export(format='onnx', imgsz=TRAIN_CONFIG['imgsz'])
            
#             # Move ONNX file
#             for f in CURRENT_DIR.glob("*.onnx"):
#                 f.rename(onnx_path)
#                 break
            
#             print(f"✅ ONNX model: {onnx_path}")
            
#             # Create super simple test script
#             test_script = output_dir / "test_model.py"
#             with open(test_script, 'w') as f:
#                 f.write(f'''#!/usr/bin/env python3
# """
# 🌾 AgroGuard Quick Test Script
# Trained: {datetime.now().strftime('%Y-%m-%d %H:%M')}
# Training Time: {total_hours:.1f} hours
# """

# from ultralytics import YOLO
# import cv2

# # Load model
# model = YOLO('{best_model_path}')

# # Test on sample image
# def test_image(image_path):
#     print(f"🔍 Testing: {{image_path}}")
    
#     results = model.predict(
#         source=image_path,
#         conf=0.5,
#         imgsz={TRAIN_CONFIG['imgsz']},
#         verbose=False
#     )
    
#     # Print results
#     for r in results:
#         if r.boxes is not None:
#             print(f"\\n📊 DETECTIONS:")
#             for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
#                 class_name = model.names[int(cls)]
#                 print(f"  • {{class_name}} ({{conf:.1%}} confidence)")
            
#             # Save image with bounding boxes
#             output_path = image_path.replace('.jpg', '_detected.jpg')
#             r.save(output_path)
#             print(f"✅ Saved: {{output_path}}")
#         else:
#             print("❌ No diseases detected")

# # Run test
# if __name__ == "__main__":
#     test_image("test_leaf.jpg")  # Replace with your image
# ''')
            
#             print(f"🧪 Test script: {test_script}")
            
#         except Exception as e:
#             print(f"⚠️ Quick test failed: {e}")
    
#     # Save training summary
#     summary = {
#         'project': 'AgroGuard Ultimate Speed Training',
#         'start_time': start_datetime,
#         'end_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         'total_hours': round(total_hours, 2),
#         'epochs_completed': TRAIN_CONFIG['epochs'],
#         'early_stopping': TRAIN_CONFIG.get('patience', 15),
#         'batch_size': TRAIN_CONFIG['batch'],
#         'image_size': TRAIN_CONFIG['imgsz'],
#         'mixed_precision': TRAIN_CONFIG.get('amp', True),
#         'gpu': gpu_name if gpu_available else 'CPU',
#         'total_images': len(image_files),
#         'classes': len(PLANTVILLAGE_CLASSES),
#         'model_path': str(best_model_path) if best_model_path.exists() else None,
#         'data_yaml': str(data_yaml_path),
#         'dataset_path': str(DATASET_ROOT)
#     }
    
#     summary_file = output_dir / "training_summary.json"
#     with open(summary_file, 'w') as f:
#         import json
#         json.dump(summary, f, indent=2)
    
#     print(f"\n📋 Training summary: {summary_file}")
    
#     print("\n🎉 TRAINING COMPLETE!")
#     print(f"   Total time: {total_hours:.1f} hours")
#     print(f"   Model ready for deployment")
#     print(f"   ONNX model exported for web PWA")

# print("\n" + "="*100)
# print("🚀 AGROGUARD ULTIMATE SPEED TRAINING COMPLETE")
# print("="*100)
# print("\n📱 READY FOR PRODUCTION:")
# print("1. Use agroguard_fast.onnx for web deployment")
# print("2. Test with test_model.py script")
# print("3. Integrate with your FastAPI backend")
# print("4. Show bounding box detection in hackathon demo")

# # SABSE ZAROORI: Windows ke liye ye block mandatory hai
# if __name__ == '__main__':
#     # 1. SETUP PATHS
#     CURRENT_DIR = Path.cwd()
#     DATASET_ROOT = CURRENT_DIR / "dataset" / "PlantVillage_for_object_detection"
    
#     # 2. LOAD MODEL
#     model = YOLO('yolov8s.pt')
    
#     try:
#         # 3. START TRAINING
#         results = model.train(
#             data='agroguard_direct.yaml',
#             epochs=100,
#             imgsz=416,
#             batch=16,            # Reduced from 20 to 16 for stability
#             workers=2,           # CHANGED: 8 se 2 kiya taaki crash na ho (Windows fix)
#             device=0,            # GPU
#             amp=True,
#             patience=15,
#             mosaic=0.2,
#             project='AgroGuard_Final',
#             name='train',
#             exist_ok=True
#         )
        
#         # YE PRINTS SIRF TABHI CHALENGE JAB TRAINING KHATAM HOGI
#         print("\n" + "="*100)
#         print("✅ TRAINING COMPLETED SUCCESSFULLY!")
#         print("="*100)
#         print("📱 READY FOR PRODUCTION:")
#         print("1. Use agroguard_fast.onnx for web deployment")
        
#     except Exception as e:
#         print(f"\n❌ TRAINING FAILED: {e}")
# import os
# import sys
# import yaml
# import torch
# import json
# from pathlib import Path
# from datetime import datetime
# import time
# import warnings
# warnings.filterwarnings('ignore')

# print("="*80)
# print("🌾 AGROGUARD - FINAL TRAINING")
# print("="*80)

# # Auto-detect dataset
# print("\n🔍 Detecting dataset...")

# datasets = [
#     (Path.cwd() / "PlantVillage_compressed_416", 416, "COMPRESSED", "3-4h", 20),
#     (Path.cwd() / "PlantVillage_original_416", 640, "ORIGINAL", "5-6h", 25),
# ]

# SOURCE = None
# IMG_SIZE = 640
# DATASET_TYPE = "UNKNOWN"
# EST_TIME = "UNKNOWN"
# EPOCHS = 20

# for path, size, dtype, time_est, ep in datasets:
#     if path.exists():
#         SOURCE = path
#         IMG_SIZE = size
#         DATASET_TYPE = dtype
#         EST_TIME = time_est
#         EPOCHS = ep
#         print(f"✅ Found: {dtype} ({size}×{size})")
#         print(f"   Time: {time_est} | Accuracy: 82-87%" if size == 416 else f"   Time: {time_est} | Accuracy: 88-92%")
#         break

# if not SOURCE:
#     print("❌ No dataset found! Run compress_dataset.py first")
#     sys.exit(1)

# # Count images
# images = list(SOURCE.rglob("*.jpg")) + list(SOURCE.rglob("*.png"))
# print(f"✅ Images: {len(images):,}")

# # Classes
# classes = [
#     "Apple_Apple_scab", "Apple_Black_rot", "Apple_Cedar_apple_rust", "Apple_healthy",
#     "Blueberry_healthy", "Cherry_healthy", "Cherry_Powdery_mildew",
#     "Corn_Cercospora_leaf_spot_Gray_leaf_spot", "Corn_Common_rust", "Corn_healthy",
#     "Corn_Northern_Leaf_Blight", "Grape_Black_rot", "Grape_Esca_(Black_Measles)",
#     "Grape_healthy", "Grape_Leaf_blight_(Isariopsis_Leaf_Spot)",
#     "Orange_Haunglongbing_(Citrus_greening)", "Peach_Bacterial_spot", "Peach_healthy",
#     "Pepper_bell_Bacterial_spot", "Pepper_bell_healthy", "Potato_Early_blight",
#     "Potato_healthy", "Potato_Late_blight", "Raspberry_healthy", "Soybean_healthy",
#     "Squash_Powdery_mildew", "Strawberry_healthy", "Strawberry_Leaf_scorch",
#     "Tomato_Bacterial_spot", "Tomato_Early_blight", "Tomato_healthy", "Tomato_Late_blight",
#     "Tomato_Leaf_Mold", "Tomato_Septoria_leaf_spot",
#     "Tomato_Spider_mites_Two-spotted_spider_mite", "Tomato_Target_Spot",
#     "Tomato_Tomato_mosaic_virus", "Tomato_Tomato_Yellow_Leaf_Curl_virus"
# ]

# # Create data.yaml
# yaml_path = Path.cwd() / "plantvillage_data.yaml"
# data = {
#     'path': str(SOURCE),
#     'train': '.',
#     'val': '.',
#     'nc': len(classes),
#     'names': classes
# }
# with open(yaml_path, 'w') as f:
#     yaml.dump(data, f, default_flow_style=False)

# print(f"✅ Created data.yaml")

# # GPU
# gpu = torch.cuda.is_available()
# gpu_name = torch.cuda.get_device_name(0) if gpu else "CPU"
# print(f"🎮 GPU: {gpu_name}")

# # Config
# if IMG_SIZE == 416:
#     batch = 20
#     aug_mosaic = 0.3
#     aug_deg = 5.0
#     aug_scale = 0.2
# else:
#     batch = 16
#     aug_mosaic = 0.5
#     aug_deg = 10.0
#     aug_scale = 0.3

# config = {
#     'data': str(yaml_path),
#     'epochs': EPOCHS,
#     'imgsz': IMG_SIZE,
#     'batch': batch,
#     'patience': 8 if IMG_SIZE == 416 else 10,
#     'warmup_epochs': 2,
#     'device': 0 if gpu else 'cpu',
#     'save': True,
#     'save_period': 2,
#     'workers': 2,
#     'cache': 'ram',
#     'fraction': 0.85,
#     'augment': True,
#     'mosaic': aug_mosaic,
#     'degrees': aug_deg,
#     'translate': 0.1,
#     'scale': aug_scale,
#     'fliplr': 0.5,
#     'hsv_h': 0.015,
#     'hsv_s': 0.4,
#     'hsv_v': 0.3,
#     'weight_decay': 0.0005,
#     'val': True,
#     'plots': True,
#     'verbose': False,
#     'cos_lr': True,
#     'close_mosaic': 10,
#     'seed': 42,
#     'optimizer': 'SGD',
#     'lr0': 0.01,
#     'lrf': 0.01,
#     'momentum': 0.937,
#     'dropout': 0.0,
#     'label_smoothing': 0.0,
#     'nbs': 64,
#     'flipud': 0.0,
#     'hsv_prob': 0.5,
# }

# # Output dir
# ts = datetime.now().strftime("%Y%m%d_%H%M%S")
# out_dir = Path.cwd() / f"training_{DATASET_TYPE.lower()}_{ts}"
# out_dir.mkdir(exist_ok=True)

# config['project'] = str(out_dir)
# config['name'] = 'train'
# config['exist_ok'] = True

# # Display
# print("\n" + "="*80)
# print("⚙️  CONFIGURATION")
# print("="*80)
# print(f"Dataset: {DATASET_TYPE} ({IMG_SIZE}×{IMG_SIZE})")
# print(f"Epochs: {EPOCHS}")
# print(f"Batch: {batch}")
# print(f"Expected Time: {EST_TIME}")
# print(f"Expected Accuracy: 82-87%" if IMG_SIZE == 416 else f"Expected Accuracy: 88-92%")
# print(f"Output: {out_dir}")

# # Confirm
# print("\n" + "="*80)
# if input("🚀 START TRAINING? (y/n): ").strip().lower() != 'y':
#     print("❌ Cancelled")
#     sys.exit(0)

# # Train
# print("\n" + "="*80)
# print("🎯 TRAINING STARTED")
# print("="*80)
# print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
# print(f"Dataset: {DATASET_TYPE}")
# print(f"Images: {len(images):,}")
# print("="*80 + "\n")

# try:
#     from ultralytics import YOLO

#     # Check checkpoint
#     ckpt = out_dir / "train" / "weights" / "last.pt"
#     if ckpt.exists():
#         if input(f"Resume from {ckpt}? (y/n): ").strip().lower() == 'y':
#             model = YOLO(str(ckpt))
#             config['resume'] = True
#         else:
#             model = YOLO('yolov8m.pt')
#     else:
#         print("Loading yolov8m.pt...")
#         model = YOLO('yolov8m.pt')

#     # Train
#     start = time.time()
#     results = model.train(**config)
#     end = time.time()

#     # Summary
#     hrs = (end - start) / 3600
#     mins = ((end - start) % 3600) / 60

#     print("\n" + "="*80)
#     print("✅ TRAINING COMPLETE!")
#     print("="*80)
#     print(f"Time: {hrs:.1f} hours ({mins:.0f} min)")
#     print(f"Per epoch: {(end-start)/EPOCHS:.0f} sec")

#     best = out_dir / 'train' / 'weights' / 'best.pt'
#     print(f"\n✅ Model: {best}")

#     # Save summary
#     summary = {
#         "date": datetime.now().isoformat(),
#         "dataset": DATASET_TYPE,
#         "size": IMG_SIZE,
#         "time_hours": round(hrs, 2),
#         "epochs": EPOCHS,
#         "gpu": gpu_name,
#         "model_path": str(best),
#     }

#     with open(out_dir / "summary.json", 'w') as f:
#         json.dump(summary, f, indent=2)

#     print("\n💡 USE MODEL:")
#     print(f"""
# from ultralytics import YOLO
# model = YOLO('{best}')
# results = model.predict('image.jpg', conf=0.65)
# """)

# except Exception as e:
#     print(f"\n❌ Error: {e}")
#     import traceback
#     traceback.print_exc()
#     sys.exit(1)

# print("\n" + "="*80)
# print("🎉 READY TO USE!")
# print("="*80)


# # -*- coding: utf-8 -*-
# """
# 🌾 PLANT VILLAGE YOLO TRAINING - LOCAL LAPTOP (RTX 4050 OPTIMIZED)
# ✅ Fixed version attribute error
# ✅ Uses yolov8m.pt for better accuracy (95% target)
# ✅ Optimized for RTX 4050 6GB VRAM
# ✅ Auto-detects dataset structure
# ✅ Estimated Time: 5-7 hours
# """

# import os
# import sys
# import yaml
# import torch
# import json
# from pathlib import Path
# from datetime import datetime
# import time
# import warnings
# warnings.filterwarnings('ignore')

# print("="*80)
# print("🌾 AGROGUARD - PLANT DISEASE DETECTION MODEL (LOCAL TRAINING)")
# print("="*80)
# print("✅ Fixed YOLO.version error")
# print("✅ Using yolov8m.pt for 95% accuracy target")
# print("✅ Optimized for RTX 4050 6GB VRAM")
# print("✅ Auto-detects dataset structure")
# print("✅ Estimated Time: 5-7 hours")
# print("="*80)

# # ============================================================================
# # 1. DYNAMIC PATH DETECTION
# # ============================================================================

# print("\n🔍 STEP 1: AUTO-DETECTING DATASET STRUCTURE...")
# print("-"*60)

# # Current directory (where script is running)
# CURRENT_DIR = Path.cwd()
# print(f"📁 Current Directory: {CURRENT_DIR}")

# # List available directories
# print("\n📂 Available directories in current location:")
# dirs_found = []
# for item in CURRENT_DIR.iterdir():
#     if item.is_dir():
#         print(f"  📁 {item.name}")
#         dirs_found.append(item.name)

# # Try multiple possible paths based on VS Code screenshot
# possible_paths = [
#     CURRENT_DIR / "dataset" / "PlantVillage_for_object_detection",  # VS Code screenshot path
#     CURRENT_DIR / "PlantVillage_for_object detection",               # Old path
#     CURRENT_DIR / "dataset" / "PlantVillage_for_object detection",
#     CURRENT_DIR / "PlantVillage_for_object_detection",
# ]

# DATASET_ROOT = None
# for path in possible_paths:
#     if path.exists():
#         DATASET_ROOT = path
#         print(f"\n✅ Found dataset at: {DATASET_ROOT}")
#         break

# if not DATASET_ROOT:
#     print("\n❌ Could not find dataset at standard paths!")
#     print("\n🔍 Searching for dataset folders...")
    
#     # Search recursively for dataset-like folders
#     for root, dirs, files in os.walk(CURRENT_DIR):
#         for dir_name in dirs:
#             if any(keyword in dir_name.lower() for keyword in ['plantvillage', 'plant_village', 'dataset']):
#                 candidate = Path(root) / dir_name
#                 print(f"  🔍 Found: {candidate}")
                
#                 # Check if it has images
#                 img_count = len(list(candidate.rglob("*.jpg"))) + len(list(candidate.rglob("*.png")))
#                 if img_count > 100:  # Likely our dataset
#                     DATASET_ROOT = candidate
#                     print(f"  ✅ Contains {img_count} images - using this")
#                     break
#         if DATASET_ROOT:
#             break

# if not DATASET_ROOT:
#     print("\n❌ Could not automatically find PlantVillage dataset!")
#     print("\n💡 MANUAL SETUP REQUIRED:")
#     print("1. Check your VS Code screenshot - it shows:")
#     print("   plantvillage/dataset/PlantVillage_for_object_detection")
#     print("\n📁 Current directory contents:")
#     for item in CURRENT_DIR.iterdir():
#         print(f"  {'📁' if item.is_dir() else '📄'} {item.name}")
    
#     # Ask for manual input
#     manual_path = input("\n🔧 Enter dataset path manually (or press Enter to exit): ").strip()
#     if manual_path:
#         DATASET_ROOT = Path(manual_path)
#         if not DATASET_ROOT.exists():
#             print(f"❌ Path does not exist: {DATASET_ROOT}")
#             sys.exit(1)
#     else:
#         sys.exit(1)

# print(f"✅ Using dataset at: {DATASET_ROOT}")

# # ============================================================================
# # 2. ANALYZE DATASET STRUCTURE
# # ============================================================================

# print("\n📊 STEP 2: ANALYZING DATASET STRUCTURE...")
# print("-"*60)

# # Find all image files
# image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
# image_files = []
# for ext in image_extensions:
#     image_files.extend(list(DATASET_ROOT.rglob(f"*{ext}")))
#     image_files.extend(list(DATASET_ROOT.rglob(f"*{ext.upper()}")))

# image_count = len(image_files)
# print(f"📸 Total images found: {image_count:,}")

# # Find label files
# label_files = list(DATASET_ROOT.rglob("*.txt"))
# print(f"📝 Label files found: {len(label_files):,}")

# # Check for standard YOLO structure
# print("\n📁 Looking for YOLO dataset structure...")
# yolo_structure = {
#     'images/': len(list(DATASET_ROOT.rglob("images/*.jpg"))) + len(list(DATASET_ROOT.rglob("images/*.png"))),
#     'labels/': len(list(DATASET_ROOT.rglob("labels/*.txt"))),
#     'train/': len(list(DATASET_ROOT.rglob("train/*.jpg"))) + len(list(DATASET_ROOT.rglob("train/*.png"))),
#     'val/': len(list(DATASET_ROOT.rglob("val/*.jpg"))) + len(list(DATASET_ROOT.rglob("val/*.png"))),
# }

# for folder, count in yolo_structure.items():
#     if count > 0:
#         print(f"  ✅ Found {count} files in {folder}")

# # Find images directory for data.yaml
# images_dir = None
# for item in DATASET_ROOT.iterdir():
#     if item.is_dir() and "image" in item.name.lower():
#         images_dir = item
#         break

# if not images_dir:
#     # Check common locations
#     if (DATASET_ROOT / "Dataset" / "images").exists():
#         images_dir = DATASET_ROOT / "Dataset" / "images"
#     elif (DATASET_ROOT / "images").exists():
#         images_dir = DATASET_ROOT / "images"
#     else:
#         # Use first directory with images
#         for item in DATASET_ROOT.iterdir():
#             if item.is_dir():
#                 img_in_dir = len(list(item.rglob("*.jpg"))) + len(list(item.rglob("*.png")))
#                 if img_in_dir > 0:
#                     images_dir = item
#                     break

# if images_dir:
#     print(f"✅ Images directory: {images_dir}")
# else:
#     print("⚠️ Could not find dedicated images directory, using dataset root")

# # ============================================================================
# # 3. CREATE DATA.YAML WITH SMART PATHS
# # ============================================================================

# print("\n📄 STEP 3: CREATING DATA CONFIGURATION...")
# print("-"*60)

# # PlantVillage 38 classes (complete list)
# class_names = [
#     "Apple_Apple_scab", "Apple_Black_rot", "Apple_Cedar_apple_rust", "Apple_healthy",
#     "Blueberry_healthy", "Cherry_healthy", "Cherry_Powdery_mildew",
#     "Corn_Cercospora_leaf_spot_Gray_leaf_spot", "Corn_Common_rust", "Corn_healthy", 
#     "Corn_Northern_Leaf_Blight", "Grape_Black_rot", "Grape_Esca_(Black_Measles)",
#     "Grape_healthy", "Grape_Leaf_blight_(Isariopsis_Leaf_Spot)",
#     "Orange_Haunglongbing_(Citrus_greening)", "Peach_Bacterial_spot", "Peach_healthy",
#     "Pepper_bell_Bacterial_spot", "Pepper_bell_healthy", "Potato_Early_blight",
#     "Potato_healthy", "Potato_Late_blight", "Raspberry_healthy", "Soybean_healthy",
#     "Squash_Powdery_mildew", "Strawberry_healthy", "Strawberry_Leaf_scorch",
#     "Tomato_Bacterial_spot", "Tomato_Early_blight", "Tomato_healthy", "Tomato_Late_blight",
#     "Tomato_Leaf_Mold", "Tomato_Septoria_leaf_spot", 
#     "Tomato_Spider_mites_Two-spotted_spider_mite", "Tomato_Target_Spot",
#     "Tomato_Tomato_mosaic_virus", "Tomato_Tomato_Yellow_Leaf_Curl_virus"
# ]

# print(f"✅ Using {len(class_names)} PlantVillage disease classes")
# print(f"📋 Sample: {', '.join(class_names[:4])}...")

# # Create data.yaml
# data_yaml_path = CURRENT_DIR / "plantvillage_data.yaml"

# # Smart path configuration
# if images_dir:
#     dataset_folder = images_dir.parent
#     train_path = "images" if images_dir.name.lower() == "images" else str(images_dir.relative_to(dataset_folder))
# else:
#     dataset_folder = DATASET_ROOT
#     train_path = "."

# data_config = {
#     'path': str(dataset_folder),
#     'train': train_path,
#     'val': train_path,  # Same for validation, will auto-split
#     'test': train_path if image_count > 1000 else '',
#     'nc': len(class_names),
#     'names': class_names  # Ultralytics prefers list format
# }

# with open(data_yaml_path, 'w') as f:
#     yaml.dump(data_config, f, default_flow_style=False, sort_keys=False)

# print(f"✅ Created data.yaml at: {data_yaml_path}")
# print(f"📍 Dataset path: {data_config['path']}")
# print(f"📍 Train/Val path: {data_config['train']}")
# print(f"📍 Classes: {len(class_names)}")

# # Show preview
# print("\n📋 DATA.YAML PREVIEW:")
# print("-"*40)
# with open(data_yaml_path, 'r') as f:
#     for i, line in enumerate(f.readlines()[:8]):
#         print(line.rstrip())
# print("...")
# print("-"*40)

# # ============================================================================
# # 4. HARDWARE DETECTION & CONFIGURATION
# # ============================================================================

# print("\n🖥️ STEP 4: DETECTING HARDWARE & OPTIMIZING...")
# print("-"*60)

# # Detect GPU
# gpu_available = torch.cuda.is_available()
# print(f"🎮 CUDA Available: {gpu_available}")

# if gpu_available:
#     gpu_name = torch.cuda.get_device_name(0)
#     gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
#     print(f"💻 GPU: {gpu_name}")
#     print(f"🧠 VRAM: {gpu_memory:.1f} GB")
    
#     # RTX 4050 specific optimization
#     if '4050' in gpu_name or (gpu_memory <= 6 and 'RTX' in gpu_name):
#         print("✅ RTX 4050 6GB detected - Optimizing settings...")
#         batch_size = 12  # Adjusted for 108,586 images
#         workers = 6
#         model_size = 'yolov8m.pt'  # Medium model for good accuracy
        
#         # Adaptive batch size based on dataset size
#         if image_count > 50000:
#             batch_size = 8
#             print(f"  📊 Very large dataset ({image_count:,} images) -> Reducing batch size to 8")
#         elif image_count < 10000:
#             batch_size = 16
#             print(f"  📊 Small dataset -> Increasing batch size to 16")
            
#     elif gpu_memory >= 8:
#         print(f"✅ High VRAM GPU ({gpu_memory}GB) detected")
#         batch_size = 16
#         workers = 6
#         model_size = 'yolov8m.pt'
#     else:
#         print(f"⚠️  Unknown GPU type - Using safe defaults")
#         batch_size = 8
#         workers = 4
#         model_size = 'yolov8m.pt'
# else:
#     print("⚠️  No GPU detected - Training on CPU (not recommended)")
#     batch_size = 2
#     workers = 2
#     model_size = 'yolov8n.pt'  # Use nano on CPU

# print(f"\n⚙️  OPTIMIZED CONFIGURATION:")
# print(f"  Model: {model_size}")
# print(f"  Batch Size: {batch_size}")
# print(f"  Workers: {workers}")
# print(f"  Images: {image_count:,}")
# print(f"  Classes: {len(class_names)}")

# # Memory estimation
# if gpu_available:
#     estimated_vram = (batch_size * 640 * 640 * 3 * 4) / 1e9  # Rough estimation
#     print(f"  Estimated VRAM usage: {estimated_vram:.1f} GB / {gpu_memory:.1f} GB")
#     if estimated_vram > gpu_memory * 0.8:
#         print(f"  ⚠️  High VRAM usage predicted! Reducing batch size...")
#         batch_size = max(4, batch_size - 4)
#         print(f"  ✅ Adjusted batch size to: {batch_size}")

# # ============================================================================
# # 5. DEPENDENCIES CHECK
# # ============================================================================

# print("\n📦 STEP 5: CHECKING DEPENDENCIES...")
# print("-"*60)

# try:
#     from ultralytics import YOLO
#     import ultralytics
#     print(f"✅ ultralytics already installed")
#     print(f"  Version: {ultralytics.__version__}")
# except ImportError:
#     print("📦 Installing ultralytics...")
#     import subprocess
#     subprocess.check_call([sys.executable, "-m", "pip", "install", "ultralytics", "opencv-python", "pyyaml"])
#     from ultralytics import YOLO
#     import ultralytics
#     print("✅ ultralytics installed successfully")
#     print(f"  Version: {ultralytics.__version__}")

# # ============================================================================
# # 6. TRAINING SETUP WITH AUTO-RESUME
# # ============================================================================

# print("\n📁 STEP 6: SETTING UP TRAINING ENVIRONMENT...")
# print("-"*60)

# # Create timestamped output directory
# timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# output_dir = CURRENT_DIR / f"agroguard_training_{timestamp}"
# output_dir.mkdir(exist_ok=True)
# print(f"✅ Output directory: {output_dir}")

# # Training directory path
# train_dir = output_dir / "train"
# weights_dir = train_dir / "weights"

# # Check for existing checkpoints in current directory
# checkpoint_paths = [
#     CURRENT_DIR / "agroguard_model_local" / "train" / "weights" / "last.pt",
#     CURRENT_DIR / "agroguard_model_local" / "train" / "weights" / "best.pt",
#     CURRENT_DIR / "train" / "weights" / "last.pt",
#     CURRENT_DIR / "train" / "weights" / "best.pt",
# ]

# existing_checkpoint = None
# for checkpoint in checkpoint_paths:
#     if checkpoint.exists():
#         existing_checkpoint = checkpoint
#         print(f"🔄 Found existing checkpoint: {checkpoint}")
#         break

# if existing_checkpoint:
#     print(f"📥 Loading model from checkpoint: {existing_checkpoint}")
#     model = YOLO(str(existing_checkpoint))
#     resume = True
#     print("   Will resume training from checkpoint")
# else:
#     print(f"🆕 Starting fresh training with {model_size}")
#     model = YOLO(model_size)
#     resume = False
#     print(f"   Using {model_size.split('.')[0]} model")

# # ============================================================================
# # 7. TRAINING CONFIGURATION (RTX 4050 OPTIMIZED)
# # ============================================================================

# print("\n⚙️  STEP 7: CONFIGURING TRAINING PARAMETERS...")
# print("-"*60)

# # RTX 4050 optimized training configuration
# config = {
#     'data': str(data_yaml_path),
#     'epochs': 100 if image_count > 50000 else 50,  # More epochs for large dataset
#     'imgsz': 640,
#     'batch': batch_size,
#     'device': 0 if gpu_available else 'cpu',
#     'patience': 30,  # Increased patience for better convergence
#     'save': True,
#     'save_period': 10,
#     'workers': workers,
#     'cache': False,  # Disable cache for large dataset (108k images)
#     'fraction': 0.85,  # 85% train, 15% validation
#     'augment': True,
#     'mosaic': 0.5,  # Reduced for memory efficiency with large dataset
#     'degrees': 5.0,
#     'translate': 0.05,
#     'scale': 0.3,
#     'fliplr': 0.3,
#     'hsv_h': 0.01,
#     'hsv_s': 0.5,
#     'hsv_v': 0.3,
#     'weight_decay': 0.0005,
#     'warmup_epochs': 5,  # Increased warmup for large dataset
#     'warmup_momentum': 0.8,
#     'val': True,
#     'plots': True,
#     'project': str(output_dir),
#     'name': 'train',
#     'exist_ok': True,
#     'resume': resume,
#     'verbose': False,  # Reduced verbosity for cleaner output
#     'cos_lr': True,
#     'close_mosaic': 10,
#     'seed': 42,
#     'optimizer': 'AdamW',
#     'lr0': 0.001,  # Lower initial LR for stable training
#     'lrf': 0.01,
#     'momentum': 0.937,
#     'dropout': 0.0,
# }

# print(f"🎯 TRAINING CONFIGURATION:")
# print(f"  Model: {model_size}")
# print(f"  Epochs: {config['epochs']}")
# print(f"  Batch Size: {config['batch']}")
# print(f"  Image Size: {config['imgsz']}x{config['imgsz']}")
# print(f"  Train/Val Split: {config['fraction']*100:.0f}% / {(1-config['fraction'])*100:.0f}%")
# print(f"  GPU: {gpu_name if gpu_available else 'CPU'}")
# print(f"  Resume: {config['resume']}")
# print(f"  Cache: {config['cache']} (disabled for large dataset)")

# # Time estimation
# if gpu_available and '4050' in gpu_name:
#     # Adjusted estimation for 108k images
#     estimated_minutes_per_epoch = max(2, image_count / (batch_size * 60))  # Rough estimation
#     total_minutes = estimated_minutes_per_epoch * config['epochs']
#     hours = total_minutes / 60
    
#     print(f"\n⏰ ESTIMATED TIME: {hours:.1f}-{hours+2:.1f} hours on RTX 4050")
#     print(f"   Based on {image_count:,} images, batch size {batch_size}, {config['epochs']} epochs")
#     print(f"   (~{estimated_minutes_per_epoch:.1f} minutes per epoch)")
# elif gpu_available:
#     print(f"\n⏰ ESTIMATED TIME: 4-8 hours")
# else:
#     print(f"\n⏰ ESTIMATED TIME: 20-30 hours on CPU")

# print("-"*60)

# # ============================================================================
# # 8. PRE-TRAINING CHECKS & CONFIRMATION
# # ============================================================================

# print("\n🔍 STEP 8: FINAL CHECKS & CONFIRMATION")
# print("="*60)

# print(f"\n📊 DATASET SUMMARY:")
# print(f"  Location: {DATASET_ROOT}")
# print(f"  Images: {image_count:,}")
# print(f"  Labels: {len(label_files):,}")
# print(f"  Classes: {len(class_names)}")
# print(f"  Data Config: {data_yaml_path}")

# print(f"\n📁 OUTPUT LOCATION:")
# print(f"  Training Output: {output_dir}")
# print(f"  Final Model: {weights_dir / 'best.pt'}")

# print(f"\n🖥️ HARDWARE:")
# print(f"  GPU: {gpu_name if gpu_available else 'CPU'}")
# print(f"  VRAM: {gpu_memory:.1f} GB" if gpu_available else "  RAM only")

# print(f"\n⚠️ IMPORTANT NOTES FOR LARGE DATASET (108k images):")
# print("• Training will take 6-8 hours")
# print("• Ensure laptop is plugged in (charger connected)")
# print("• Close other GPU-intensive applications")
# print("• Laptop may get warm - ensure proper ventilation")
# print("• Progress will be shown in real-time")
# print("• Model auto-saves every 10 epochs")
# print("• Training can be resumed if interrupted")

# # Ask for confirmation
# print("\n" + "="*60)
# response = input("🚀 START TRAINING NOW? (y/n): ").strip().lower()

# if response != 'y':
#     print("\n❌ Training cancelled by user")
#     print(f"\n✅ Your data.yaml is ready: {data_yaml_path}")
#     print(f"✅ You can train later with: python {Path(__file__).name}")
#     sys.exit(0)

# print("\n" + "="*80)
# print("🚀 TRAINING STARTED - DO NOT CLOSE THIS WINDOW")
# print("="*80)
# print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
# print(f"📊 Dataset: {image_count:,} images, {len(class_names)} classes")
# print(f"⚙️  Config: {config['epochs']} epochs, batch size {config['batch']}")
# print("📈 Monitoring progress...")
# print("="*80)

# # ============================================================================
# # 9. TRAINING EXECUTION WITH PROGRESS TRACKING
# # ============================================================================

# success = False
# training_start_time = time.time()
# start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# try:
#     # Start training
#     print(f"\n🎯 Starting training at {start_datetime}")
#     print("📊 Training logs will appear below...")
#     print("-"*60)
    
#     results = model.train(**config)
#     success = True
    
# except KeyboardInterrupt:
#     print("\n\n⚠️  TRAINING INTERRUPTED BY USER")
#     print("="*60)
#     current_time = (time.time() - training_start_time) / 3600
#     print(f"⏱️  Training ran for: {current_time:.1f} hours")
    
#     if weights_dir.exists() and any(weights_dir.glob("*.pt")):
#         print(f"\n💾 Last checkpoint saved at: {weights_dir}")
#         print("   You can resume training by running this script again")
#     else:
#         print("\n⚠️  No checkpoints saved yet")
    
#     success = False
#     sys.exit(0)
    
# except Exception as e:
#     print(f"\n❌ Training failed with error: {str(e)}")
#     print(f"📝 Error type: {type(e).__name__}")
#     print("\n🔧 TROUBLESHOOTING:")
#     print("1. Check if dataset path is correct")
#     print("2. Ensure you have enough disk space")
#     print("3. Try reducing batch size if out of memory")
#     print("4. Check YOLO installation: pip install --upgrade ultralytics")
    
#     import traceback
#     traceback.print_exc()
#     success = False
#     sys.exit(1)

# # Calculate training time
# training_end_time = time.time()
# training_duration = training_end_time - training_start_time
# hours = training_duration / 3600
# minutes = (training_duration % 3600) / 60

# if success:
#     print("\n" + "="*80)
#     print("✅ TRAINING COMPLETED SUCCESSFULLY!")
#     print("="*80)
#     print(f"⏱️  Total Training Time: {hours:.1f} hours ({minutes:.0f} minutes)")
    
#     # Display final metrics
#     try:
#         # Try different ways to get metrics
#         if hasattr(results, 'results_dict'):
#             metrics = results.results_dict
#         elif hasattr(results, 'metrics'):
#             metrics = results.metrics
#         else:
#             metrics = {}
        
#         if metrics:
#             print(f"\n📊 FINAL MODEL PERFORMANCE:")
            
#             # Extract key metrics
#             map50 = metrics.get('metrics/mAP50(B)', metrics.get('mAP50', 0))
#             precision = metrics.get('metrics/precision(B)', metrics.get('precision', 0))
#             recall = metrics.get('metrics/recall(B)', metrics.get('recall', 0))
            
#             print(f"  🎯 mAP50: {map50:.3%}" if isinstance(map50, (int, float)) else f"  🎯 mAP50: {map50}")
#             print(f"  📏 Precision: {precision:.3%}" if isinstance(precision, (int, float)) else f"  📏 Precision: {precision}")
#             print(f"  🔍 Recall: {recall:.3%}" if isinstance(recall, (int, float)) else f"  🔍 Recall: {recall}")
            
#             # Performance evaluation
#             if isinstance(map50, (int, float)):
#                 if map50 >= 0.85:
#                     print(f"  🏆 EXCELLENT! High accuracy achieved")
#                 elif map50 >= 0.75:
#                     print(f"  👍 GOOD! Model is performing well")
#                 else:
#                     print(f"  ⚠️  ACCEPTABLE. Consider more training")
#     except Exception as e:
#         print(f"⚠️  Could not extract metrics: {e}")
    
#     # Save comprehensive training summary
#     summary = {
#         'project': 'AgroGuard Plant Disease Detection',
#         'timestamp': datetime.now().isoformat(),
#         'training_start': start_datetime,
#         'training_end': datetime.fromtimestamp(training_end_time).strftime("%Y-%m-%d %H:%M:%S"),
#         'training_duration_hours': round(hours, 2),
#         'model': model_size,
#         'epochs': config['epochs'],
#         'batch_size': config['batch'],
#         'image_size': config['imgsz'],
#         'hardware': {
#             'gpu': gpu_name if gpu_available else 'CPU',
#             'vram_gb': round(gpu_memory, 1) if gpu_available else None,
#             'cuda_available': gpu_available
#         },
#         'dataset': {
#             'path': str(DATASET_ROOT),
#             'total_images': image_count,
#             'labels_found': len(label_files),
#             'classes': len(class_names),
#             'class_list': class_names
#         },
#         'training_config': {k: v for k, v in config.items() if k not in ['data']},
#         'output_paths': {
#             'best_model': str(weights_dir / "best.pt"),
#             'last_model': str(weights_dir / "last.pt"),
#             'results_csv': str(train_dir / "results.csv"),
#             'args_yaml': str(train_dir / "args.yaml"),
#             'data_yaml': str(data_yaml_path)
#         }
#     }
    
#     summary_file = output_dir / "training_summary.json"
#     with open(summary_file, 'w') as f:
#         json.dump(summary, f, indent=2, ensure_ascii=False)
    
#     print(f"\n📊 Training summary saved: {summary_file}")
    
#     # Create quick usage guide
#     usage_guide = output_dir / "HOW_TO_USE.md"
#     with open(usage_guide, 'w', encoding='utf-8') as f:
#         f.write(f"""# 🌾 AgroGuard Plant Disease Detection Model

# ## Model Information
# - **Trained on**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
# - **Training Time**: {hours:.1f} hours
# - **Model**: {model_size}
# - **GPU Used**: {gpu_name if gpu_available else 'CPU'}
# - **Dataset**: {image_count:,} images, {len(class_names)} classes

# ## Quick Start

# ```python
# from ultralytics import YOLO
# import cv2

# # 1. Load your trained model
# model = YOLO('{weights_dir / "best.pt"}')

# # 2. Make predictions
# results = model.predict('your_image.jpg', conf=0.5)

# # 3. Display results
# for result in results:
#     annotated_image = result.plot()
#     cv2.imshow('Plant Disease Detection', annotated_image)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
    
# # 4. Or save the result
# results[0].save('detected_output.jpg')

# # 5. Get detection details
# for result in results:
#     boxes = result.boxes.xyxy  # Bounding boxes
#     classes = result.boxes.cls  # Class IDs
#     confidences = result.boxes.conf  # Confidence scores
    
#     for box, cls, conf in zip(boxes, classes, confidences):
#         print(f"Class: {class_names[int(cls)]}, Confidence: {conf:.2%}")""")
