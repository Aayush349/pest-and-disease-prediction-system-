#!/usr/bin/env python3
"""
Extract disease information from dataset
SYNCHRONIZED - Finds all image types and all 53+ classes
"""

import os
import json
from pathlib import Path
from collections import defaultdict

print("\n" + "="*70)
print("🧠 BUILDING KNOWLEDGE BASE FROM DATASET")
print("="*70)

raw_data = Path("../data/raw")
kb_path = Path("../knowledge_base")
kb_path.mkdir(parents=True, exist_ok=True)

# --- This is the new SYNCHRONIZED logic ---
image_extensions = ["*.jpg", "*.JPG", "*.jpeg", "*.JPEG", "*.png", "*.PNG"]
all_images = []
print("\n🔍 Scanning for images in all formats...")
for ext in image_extensions:
    for image_path in raw_data.rglob(ext):
        all_images.append(image_path)
        
print(f"✅ Total images scanned: {len(all_images):,}")

# Group by disease
images_by_disease = defaultdict(int)
for img_path in all_images:
    disease_name = img_path.parent.name
    images_by_disease[disease_name] += 1

# Filter out junk folders
final_classes = {}
junk_folders = ["raw", "paddy", "cassava", "apple", "plantvillage", "train_images", "test_images", "val", "test"]

for disease_name, image_count in images_by_disease.items():
    if image_count < 3: # Skip tiny/empty folders
        continue
    if disease_name in junk_folders: # Skip junk folders
        continue
    final_classes[disease_name] = image_count
# --- End of SYNCHRONIZED logic ---
    
print(f"✅ Found {len(final_classes)} valid disease classes")
print("\nClass breakdown:")
for disease_name in sorted(final_classes.keys()):
    count = final_classes[disease_name]
    print(f"   ✓ {disease_name}: {count:,} images")

# Build knowledge base
knowledge_base = {}

for disease_name, image_count in final_classes.items():
    # Use API fallback for all
    knowledge_base[disease_name] = {
        "description": f"Disease class: {disease_name}",
        "symptoms": ["USE_API_FALLBACK"],
        "treatment": ["USE_API_FALLBACK"],
        "prevention": ["USE_API_FALLBACK"],
        "image_count": image_count
    }

# Save knowledge base
output_path = kb_path / "diseases.json"
with open(output_path, 'w') as f:
    json.dump(knowledge_base, f, indent=2)

print(f"\n✅ Knowledge base saved: {output_path}")
print(f"✅ Classes: {len(knowledge_base)}")
print("\n" + "="*70)
print("✅ KNOWLEDGE BASE EXTRACTION COMPLETE")
print("="*70)