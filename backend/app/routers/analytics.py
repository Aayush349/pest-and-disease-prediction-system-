from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

from ..database import get_db
from ..models.sql_models import Prediction # Import Prediction Model
from ..utils.logger import Logger  # ✅ NEW: For logging

router = APIRouter(tags=["Analytics & Maps"])
logger = Logger(__name__)  # ✅ NEW: Initialize logger

# Schema for Map Data (Lightweight for fast loading)
class HeatmapPoint(BaseModel):
    latitude: float
    longitude: float
    disease: str
    confidence: float
    ndvi: float = 0.0      # ✅ NEW: For Color Logic
    status: str = "Healthy" # ✅ NEW: For Legend (Urban/Stress/Healthy)
    location_name: str = ""  # ✅ Reverse-geocoded place name
    zone_radius: int = 10000 # ✅ 10km zone radius in meters
    created_at: datetime

@router.get("/heatmap", response_model=List[HeatmapPoint])
async def get_heatmap_data(
    db: Session = Depends(get_db),
    show_urban: bool = Query(False, description="Show urban areas on map")  # ✅ NEW: Filter toggle
):
    """
    RETURNS LIVE DATA FOR MAP (Heatmap Data Source).
    Includes logic for SQLite (Local) fetching + NDVI Status Calculation.
    Filters urban areas by default unless explicitly requested.
    """
    try:
        # 1. Filters
        start_date = datetime.now() - timedelta(days=30)
        
        # 2. Base Query
        query = db.query(Prediction).filter(
            Prediction.latitude.isnot(None),
            Prediction.longitude.isnot(None),
            Prediction.created_at >= start_date,
        )
        
        # ✅ FIXED: Filter out urban areas unless explicitly requested
        if not show_urban:
            # Filter by status field (preferred) or NDVI threshold (fallback)
            # Updated threshold: 0.10 (was 0.22) to match corrected classification
            query = query.filter(
                (Prediction.status != "Urban") | (Prediction.status.is_(None)),
                (Prediction.ndvi_score >= 0.10) | (Prediction.ndvi_score.is_(None))
            )
        
        # 3. Filter out healthy/unknown predictions and low confidence
        query = query.filter(
            Prediction.disease != "Healthy",
            Prediction.disease != "Unknown",
            Prediction.confidence >= 0.3  # Minimum 30% confidence
        )
        
        points = query.all()
        
        # 4. Format Data
        heatmap_data = []
        for p in points:
            # --- NDVI / STATUS LOGIC ---
            # Use stored NDVI or default to 0
            ndvi_val = p.ndvi_score if p.ndvi_score is not None else 0.0
            
            # Use stored status or calculate from NDVI
            if p.status:
                status_label = p.status
            else:
                # Fallback: calculate from NDVI using FIXED thresholds
                if ndvi_val < 0.10:
                    status_label = "Urban"
                elif ndvi_val < 0.40:
                    status_label = "Stressed"
                else:
                    status_label = "Healthy"
            
            heatmap_data.append({
                "latitude": p.latitude,
                "longitude": p.longitude,
                "disease": p.disease,
                "confidence": p.confidence or 0.0,
                "ndvi": ndvi_val,           # ✅ Frontend compatibility
                "ndvi_score": ndvi_val,     # ✅ Alternative naming
                "status": status_label,     # ✅ Urban/Stressed/Healthy
                "location_name": getattr(p, 'location_name', '') or '',  # ✅ Place name
                "zone_radius": 10000,       # ✅ 10km zone in meters
                "created_at": p.created_at
            })
        
        logger.info(f"📊 Heatmap data points: {len(heatmap_data)} (show_urban={show_urban})")
        return heatmap_data
        
    except Exception as e:
        print(f"Analytics Error: {e}")
        return []

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
        active_farmers = db.query(func.count(func.distinct(Prediction.farmer_id))).scalar() or 0
        
        return {
            "total_scans": total_scans,
            "active_farmers": active_farmers,
            "system_status": "Online",
            "monitoring_mode": "Satellite + Edge AI"
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