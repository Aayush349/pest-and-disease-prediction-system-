#!/usr/bin/env python3
"""
Create train/val/test splits from raw dataset
SYNCHRONIZED image finding with other scripts
"""

import os
import shutil
from pathlib import Path
from sklearn.model_selection import train_test_split
import random
from collections import defaultdict

print("\n" + "="*70)
print("📂 CREATING TRAIN/VAL/TEST SPLITS (70/15/15)")
print("="*70)

raw_data = Path("../data/raw")
processed_data = Path("../data/processed")

# Clean up old processed directory
if processed_data.exists():
    print(f"\n🧹 Removing old processed directory...")
    shutil.rmtree(processed_data)

# Create split directories
for split in ["train", "val", "test"]:
    (processed_data / split).mkdir(parents=True, exist_ok=True)

# --- This is the new SYNCHRONIZED logic ---
image_extensions = ["*.jpg", "*.JPG", "*.jpeg", "*.JPEG", "*.png", "*.PNG"]
all_images = []
print("\n🔍 Scanning for images in all formats...")
for ext in image_extensions:
    for image_path in raw_data.rglob(ext):
        all_images.append(image_path)
        
print(f"✅ Total images scanned: {len(all_images):,}")

# Group images by disease
images_by_disease = defaultdict(list)
for img_path in all_images:
    disease_name = img_path.parent.name
    images_by_disease[disease_name].append(str(img_path))

# Filter out junk folders
final_classes = {}
junk_folders = ["raw", "paddy", "cassava", "apple", "plantvillage", "train_images", "test_images", "val", "test"]

for disease_name, images in images_by_disease.items():
    if len(images) < 3: # Skip tiny/empty folders
        continue
    if disease_name in junk_folders: # Skip junk folders
        continue
    final_classes[disease_name] = images
# --- End of SYNCHRONIZED logic ---

print(f"✅ Found {len(final_classes)} valid disease classes")

# Split each disease class 70/15/15
train_images = []
val_images = []
test_images = []
print("\n📋 Splitting by disease class...")

for disease_name, images in final_classes.items():
    train_split, temp_split = train_test_split(
        images, test_size=0.30, random_state=42
    )
    val_split, test_split = train_test_split(
        temp_split, test_size=0.50, random_state=42
    )
    
    train_images.extend([(img, disease_name) for img in train_split])
    val_images.extend([(img, disease_name) for img in val_split])
    test_images.extend([(img, disease_name) for img in test_split])
    
    print(f"   ✓ {disease_name}: {len(train_split)} train, {len(val_split)} val, {len(test_split)} test")

# Copy files to split folders
def copy_files(image_list, split_name):
    count = 0
    for src_path, disease_name in image_list:
        dest_dir = processed_data / split_name / disease_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        filename = Path(src_path).name
        dest_path = dest_dir / filename
        
        if not dest_path.exists():
            shutil.copy2(src_path, dest_path)
            count += 1
        
        if count % 20000 == 0 and count > 0:
            print(f"   Copying to {split_name}: {count:,} images...")
    
    print(f"✅ {split_name}: {count:,} images copied")
    return count

print("\n📋 Copying files to train/val/test folders...")
train_count = copy_files(train_images, "train")
val_count = copy_files(val_images, "val")
test_count = copy_files(test_images, "test")

print("\n" + "="*70)
print("✅ DATASET SPLIT COMPLETE!")
print("="*70)
print(f"✓ Train: {train_count:,} images")
print(f"✓ Val:   {val_count:,} images")
print(f"✓ Test:  {test_count:,} images")
print(f"✓ Total: {train_count + val_count + test_count:,} images")
print(f"✓ Classes: {len(final_classes)}")
print("="*70)