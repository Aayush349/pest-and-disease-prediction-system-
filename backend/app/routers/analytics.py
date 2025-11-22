from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

from ..database import get_db
from ..models.sql_models import Prediction # Import Prediction Model

router = APIRouter(tags=["analytics"])

# Schema for Map Data (Lightweight for fast loading)
class HeatmapPoint(BaseModel):
    latitude: float
    longitude: float
    disease: str
    confidence: float

@router.get("/heatmap", response_model=List[HeatmapPoint])
async def get_disease_heatmap(db: Session = Depends(get_db)):
    """
    RETURNS LIVE DATA FOR MAP (Heatmap Data Source).
    Filters: Only shows high-confidence, geo-tagged, recent records.
    """
    try:
        # Final Filter Check: Filter out default guest user ID (String ID)
        demo_user_id = "guest_user" 
        
        # We also need to filter out the hardcoded ID we used in disease.py for safety
        test_user_id = "kisan_singh_001" 
        
        # 30 days look back for recency
        start_date = datetime.now() - timedelta(days=30)

        points = db.query(Prediction).filter(
            Prediction.latitude.isnot(None),
            Prediction.longitude.isnot(None),
            Prediction.confidence > 0.70, # High confidence for better map quality
            Prediction.created_at >= start_date,
            
            # ✅ Filter out Demo/Guest data (String comparison)
            Prediction.farmer_id != demo_user_id,
            Prediction.farmer_id != test_user_id
            
        ).all()
        
        heatmap_data = [
            HeatmapPoint(
                latitude=p.latitude,
                longitude=p.longitude,
                disease=p.disease,
                confidence=p.confidence
            ) 
            for p in points
        ]
        
        return heatmap_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_disease_stats(db: Session = Depends(get_db)):
    """
    RETURNS DATA FOR DASHBOARD PIE CHARTS
    """
    try:
        # Total scans count
        total_scans = db.query(Prediction).count()
        
        # Count distinct active farmers
        from sqlalchemy import func
        active_farmers = db.query(func.count(func.distinct(Prediction.farmer_id))).scalar()
        
        return {
            "total_scans": total_scans,
            "active_farmers": active_farmers,
            "system_status": "Online",
            "monitoring_mode": "Real-Time"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))












# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from typing import List
# from pydantic import BaseModel
# import uuid

# from ..database import get_db
# from ..models.sql_models import Prediction

# router = APIRouter(tags=["analytics"])

# # Schema for Map Data (Lightweight for fast loading)
# class HeatmapPoint(BaseModel):
#     latitude: float
#     longitude: float
#     disease: str
#     confidence: float

# @router.get("/heatmap", response_model=List[HeatmapPoint])
# async def get_disease_heatmap(db: Session = Depends(get_db)):
#     """
#     RETURNS LIVE DATA FOR MAP
#     Filters:
#     1. Must have GPS location
#     2. Confidence > 50% (High quality data only)
#     """
#     try:
#         # Define dummy UUID for demo users (match the one in disease.py)
#         demo_uuid = uuid.UUID('00000000-0000-0000-0000-000000000000')

#         points = db.query(Prediction).filter(
#             Prediction.latitude.isnot(None),
#             Prediction.longitude.isnot(None),
#             Prediction.confidence > 0.50, # Only high confidence
#             # ✅ Filter out Demo/Guest data from the public map
#             #Prediction.farmer_id != demo_uuid
#         ).all()
        
#         # Convert DB objects to JSON list
#         heatmap_data = [
#             HeatmapPoint(
#                 latitude=p.latitude,
#                 longitude=p.longitude,
#                 disease=p.disease,
#                 confidence=p.confidence
#             ) 
#             for p in points
#         ]
        
#         return heatmap_data
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/stats")
# async def get_disease_stats(db: Session = Depends(get_db)):
#     """
#     RETURNS DATA FOR DASHBOARD PIE CHARTS
#     """
#     try:
#         # Total scans count
#         total_scans = db.query(Prediction).count()
        
#         # Count distinct active farmers
#         from sqlalchemy import func
#         active_farmers = db.query(func.count(func.distinct(Prediction.farmer_id))).scalar()
        
#         return {
#             "total_scans": total_scans,
#             "active_farmers": active_farmers,
#             "system_status": "Online",
#             "monitoring_mode": "Real-Time"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))















# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from typing import List
# from pydantic import BaseModel

# from ..database import get_db
# from ..models.sql_models import Prediction

# router = APIRouter(tags=["analytics"])

# # Schema for Map Data (Lightweight for fast loading)
# class HeatmapPoint(BaseModel):
#     latitude: float
#     longitude: float
#     disease: str
#     confidence: float

# @router.get("/heatmap", response_model=List[HeatmapPoint])
# async def get_disease_heatmap(db: Session = Depends(get_db)):
#     """
#     RETURNS LIVE DATA FOR MAP
#     Filters:
#     1. Must have GPS location
#     2. Confidence > 50% (High quality data only)
#     3. NOT a Demo User (To prevent false alarms during hackathon)
#     """
#     try:
#         points = db.query(Prediction).filter(
#             Prediction.latitude.isnot(None),
#             Prediction.longitude.isnot(None),
#             Prediction.confidence > 0.50, # Only high confidence
#             # ✅ DEMO FILTER: In IDs ka data map par mat dikhao
#             Prediction.farmer_id != "demo_tester", 
#             Prediction.farmer_id != "guest_user"
#         ).all()
        
#         # Convert DB objects to JSON list
#         heatmap_data = [
#             HeatmapPoint(
#                 latitude=p.latitude,
#                 longitude=p.longitude,
#                 disease=p.disease,
#                 confidence=p.confidence
#             ) 
#             for p in points
#         ]
        
#         return heatmap_data
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/stats")
# async def get_disease_stats(db: Session = Depends(get_db)):
#     """
#     RETURNS DATA FOR DASHBOARD PIE CHARTS
#     """
#     try:
#         # Total scans count
#         total_scans = db.query(Prediction).count()
        
#         # Count distinct active farmers
#         from sqlalchemy import func
#         active_farmers = db.query(func.count(func.distinct(Prediction.farmer_id))).scalar()
        
#         return {
#             "total_scans": total_scans,
#             "active_farmers": active_farmers,
#             "system_status": "Online",
#             "monitoring_mode": "Real-Time"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))