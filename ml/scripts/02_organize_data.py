#!/usr/bin/env python3
"""
Organize and analyze downloaded/manual datasets
RUN THIS FIRST if you already have datasets downloaded manually
"""

import os
import json
from pathlib import Path
from collections import defaultdict

class DatasetOrganizer:
    def __init__(self):
        self.raw_path = Path("../data/raw")
        self.processed_path = Path("../data/processed")
        self.processed_path.mkdir(exist_ok=True)
    
    def analyze(self):
        """Analyze dataset structure"""
        print("\n" + "="*70)
        print("📊 DATASET ANALYSIS - ORGANIZING YOUR DATA")
        print("="*70)
        
        disease_counts = defaultdict(int)
        total_images = 0
        
        # Walk through all folders
        for item in self.raw_path.iterdir():
            if item.is_dir():
                print(f"\n📁 Scanning: {item.name}/")
                
                for disease_folder in item.rglob("*"):
                    if disease_folder.is_dir():
                        images = list(disease_folder.glob("*.jpg")) + list(disease_folder.glob("*.png"))
                        if images:
                            disease_name = disease_folder.name
                            count = len(images)
                            disease_counts[disease_name] = count
                            total_images += count
                            print(f"   ✓ {disease_name}: {count} images")
        
        # Print statistics
        print(f"\n" + "="*70)
        print(f"✓ Total Images: {total_images:,}")
        print(f"✓ Total Diseases: {len(disease_counts)}")
        print(f"="*70)
        
        # Save statistics
        stats = {
            "total_images": total_images,
            "total_diseases": len(disease_counts),
            "disease_breakdown": disease_counts
        }
        
        stats_path = self.processed_path.parent / "dataset_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"\n✓ Statistics saved to: {stats_path}")
        return total_images, len(disease_counts)

if __name__ == "__main__":
    organizer = DatasetOrganizer()
    total, diseases = organizer.analyze()
    print(f"\n✅ READY: {total} images, {diseases} diseases\n")
