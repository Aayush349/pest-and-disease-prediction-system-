#!/usr/bin/env python3
"""
Complete dataset download script
Downloads from Kaggle to ml/data/raw/
"""

import os
import kaggle
from pathlib import Path
import sys

print("\n" + "="*70)
print("🌾 AGROGUARD DATASET DOWNLOADER")
print("="*70)

# Create directories
base_path = Path("../data/raw")
base_path.mkdir(parents=True, exist_ok=True)

print(f"\n📁 Download location: {base_path.absolute()}\n")

# Dataset list
datasets = [
    {
        "name": "PlantVillage",
        "kaggle_id": "abdallahalidev/plantvillage-dataset",
        "output_dir": "plantvillage",
        "size": "~3 GB",
        "description": "50,000 images - 14 crops × 26 diseases",
        "type": "dataset"
    },
    {
        "name": "Cassava Leaf Disease",
        "kaggle_id": "cassava-leaf-disease-classification",
        "output_dir": "cassava",
        "size": "~500 MB",
        "description": "5,000 images - 4 disease classes",
        "type": "competition"
    },
    {
        "name": "Paddy Doctor",
        "kaggle_id": "ravirajsinh45/paddy-doctor-complete-dataset",
        "output_dir": "paddy",
        "size": "~400 MB",
        "description": "3,700 images - 10 disease classes",
        "type": "dataset"
    },
    {
        "name": "Apple Leaf Diseases",
        "kaggle_id": "rvboyle/apple-leaf-diseases",
        "output_dir": "apple",
        "size": "~200 MB",
        "description": "1,800 images - 4 disease classes",
        "type": "dataset"
    }
]

# Calculate total
total_gb = 3 + 0.5 + 0.4 + 0.2
print(f"📊 Total size: ~{total_gb:.1f} GB")
print("⏱️  Time estimate: 30-90 minutes (depends on internet speed)\n")

input("Press ENTER to start downloading...")

# Download each dataset
for idx, dataset in enumerate(datasets, 1):
    print(f"\n{idx}️⃣  {dataset['name']}")
    print(f"   Size: {dataset['size']}")
    print(f"   {dataset['description']}")
    print(f"   Downloading... ", end="", flush=True)
    
    try:
        output_dir = base_path / dataset["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if dataset["type"] == "competition":
            kaggle.api.competition_download_files(
                dataset["kaggle_id"],
                path=str(output_dir)
            )
        else:
            kaggle.api.dataset_download_files(
                dataset["kaggle_id"],
                path=str(output_dir),
                unzip=True
            )
        
        print("✓ DONE")
        
    except Exception as e:
        print(f"✗ FAILED")
        print(f"   Error: {str(e)}")
        print(f"   Try manually downloading from kaggle.com")

print("\n" + "="*70)
print("✓ DOWNLOAD COMPLETE (or check for errors above)")
print("="*70)

# Verify downloads
print("\n📊 Verifying downloads...")
for dataset in datasets:
    output_dir = base_path / dataset["output_dir"]
    if output_dir.exists():
        images = len(list(output_dir.glob("**/*.jpg"))) + len(list(output_dir.glob("**/*.png")))
        if images > 0:
            print(f"✓ {dataset['name']}: {images} images")
        else:
            print(f"⚠ {dataset['name']}: folder exists but no images found")
    else:
        print(f"✗ {dataset['name']}: folder not found")

print("\nNext step: Run python 02_organize_data.py")
