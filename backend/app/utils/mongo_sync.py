from pymongo import MongoClient
import os
from datetime import datetime

# Free MongoDB Atlas URL (Hackathon ke liye best hai)
# Agar local mongodb hai to: "mongodb://localhost:27017/"
MONGO_URI = "mongodb+srv://aayushsahu867:88888888@cluster0.84rd6gj.mongodb.net/?appName=Cluster0"

def sync_to_cloud(data):
    """
    Saves prediction to MongoDB for Global Heatmap.
    Fail-safe: Agar net nahi hai, toh crash nahi karega, bas skip karega.
    """
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client["agroguard_cloud"]
        collection = db["global_heatmap"]
        
        # Data packet based on your Risk & Disease logic
        payload = {
            "scan_id": data.get("id"),
            "location": {
                "type": "Point",
                "coordinates": [data.get("longitude"), data.get("latitude")] # Mongo expects [Lon, Lat]
            },
            "status": data.get("risk_summary"), # HIGH RISK / SAFE
            "disease": data.get("disease"),
            "ndvi": data.get("ndvi_score"),
            "timestamp": datetime.utcnow()
        }
        
        # Insert or Update (Upsert)
        collection.update_one(
            {"scan_id": data.get("id")}, 
            {"$set": payload}, 
            upsert=True
        )
        print("☁️ Synced to MongoDB Cloud")
        return True
    except Exception as e:
        print(f"⚠️ Cloud Sync Skipped (Offline): {e}")
        return False