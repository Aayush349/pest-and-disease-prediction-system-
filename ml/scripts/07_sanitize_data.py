import os
from pathlib import Path
from PIL import Image
import sys

print("======================================================================")
print("🧼 SANITIZING ALL PROCESSED IMAGES (TRAIN, VAL, TEST) - v2")
print("This will force all images to be 224x224 RGB.")
print("This will take a long time, but is a one-time fix.")
print("======================================================================")

processed_path = Path("../data/processed")
target_size = (224, 224)

# --- THIS IS THE FIX ---
# Added the '*' wildcard to find all files ending with these extensions
image_extensions = ["*.jpg", "*.JPG", "*.jpeg", "*.JPEG", "*.png", "*.PNG"]
# --- END OF FIX ---

corrupt_files = []
total_files = 0

for split in ["train", "val", "test"]:
    split_path = processed_path / split
    if not split_path.exists():
        print(f"Warning: {split} folder not found. Skipping.")
        continue
        
    print(f"\nProcessing {split} folder...")
    
    image_paths = []
    # This loop will now find all the images
    for ext in image_extensions:
        for image_path in split_path.rglob(ext):
            image_paths.append(image_path)
    
    total_in_split = len(image_paths)
    print(f"Found {total_in_split:,} images in {split}...")
    
    for i, image_path in enumerate(image_paths):
        if (i+1) % 1000 == 0:
            print(f"   ...processing {i+1} / {total_in_split}")
        
        try:
            # Check for 0-byte files
            if os.path.getsize(image_path) == 0:
                print(f"   [DELETING] 0-byte file: {image_path}")
                corrupt_files.append(image_path)
                os.remove(image_path)
                continue
                
            with Image.open(image_path) as img:
                # 1. Convert to RGB (handles grayscale, 1-channel images)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 2. Resize to 224x224 (handles all different shapes)
                if img.size != target_size:
                    img = img.resize(target_size, Image.LANCZOS)
                    
                # 3. Save the image over itself
                img.save(image_path, "JPEG") # Save as JPEG for consistency
                
        except Exception as e:
            print(f"   [DELETING] Corrupt file: {image_path}")
            print(f"   Error: {e}")
            corrupt_files.append(image_path)
            if os.path.exists(image_path):
                os.remove(image_path)

print("\n" + "="*70)
print("✅ SANITIZATION COMPLETE.")
if corrupt_files:
    print(f"Removed {len(corrupt_files)} corrupt files.")
else:
    print("No corrupt files found.")
print("Your dataset is now clean and ready for evaluation.")
print("="*70)