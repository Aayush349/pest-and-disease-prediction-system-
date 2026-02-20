# backend/app/models/sql_models.py

from sqlalchemy import Column, String, Float, DateTime, Integer, Text, JSON, Boolean
from datetime import datetime
import uuid
from ..database import Base
from sqlalchemy.sql import func

def generate_uuid():
    return str(uuid.uuid4())

class Farmer(Base):
    __tablename__ = "farmers"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    location = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Prediction(Base):
    """
    Updated Prediction Model
    - Stores Geo-Location (Lat/Long) for Heatmaps
    - Stores Farmer ID for tracking
    """
    __tablename__ = "predictions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    farmer_id = Column(String(36), nullable=False) # Frontend se aayega
    disease = Column(String(200), nullable=False)
    confidence = Column(Float, nullable=False)
    
    # ✅ NEW FIELDS: Location for Heatmap
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    # Additional fields for risk analysis and map visualization
    ndvi_score = Column(Float, nullable=True)
    field_health = Column(String(100), nullable=True)
    combined_risk = Column(String(100), nullable=True)
    # ✅ NEW: NDVI-based classification fields
    status = Column(String(50), nullable=True)  # "Urban", "Stressed", "Healthy"
    is_agricultural = Column(Boolean, default=True)  # True for farms, False for urban
    description = Column(Text, nullable=True)
    fallback_reason = Column(Text)
    advisory_source = Column(String(100), nullable=True)
    model_used = Column(String(100), nullable=True)
    top5 = Column(JSON, nullable=True)
    treatment = Column(JSON, nullable=True)
    prevention = Column(JSON, nullable=True)
    image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    crop_stage = Column(String, nullable=True) # <--- Add this line
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    knowledge_source = Column(String, default="yolo")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    farmer_id = Column(String(36), nullable=False)
    prediction_id = Column(String(36), nullable=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    disease_context = Column(String(200), nullable=True)
    llm_provider = Column(String(50), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

















# # backend/app/models/sql_models.py

# from sqlalchemy import Column, String, Float, DateTime, Integer, Text, JSON
# from datetime import datetime
# import uuid
# from ..database import Base

# # Helper function to generate string UUIDs
# def generate_uuid():
#     return str(uuid.uuid4())

# class Farmer(Base):
#     """Farmer model"""
#     __tablename__ = "farmers"
    
#     # Changed UUID to String(36) for SQLite compatibility
#     id = Column(String(36), primary_key=True, default=generate_uuid)
#     name = Column(String(100), nullable=False)
#     phone = Column(String(20), unique=True, nullable=False)
#     location = Column(String(200), nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# class Prediction(Base):
#     """Disease prediction history"""
#     __tablename__ = "predictions"
    
#     id = Column(String(36), primary_key=True, default=generate_uuid)
#     farmer_id = Column(String(36), nullable=False)
#     disease = Column(String(200), nullable=False)
#     confidence = Column(Float, nullable=False)
#     top5 = Column(JSON, nullable=True)
#     treatment = Column(JSON, nullable=True)
#     prevention = Column(JSON, nullable=True)
#     image_path = Column(String(500), nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow)

# class ChatHistory(Base):
#     """Chat conversation history"""
#     __tablename__ = "chat_history"
    
#     id = Column(String(36), primary_key=True, default=generate_uuid)
#     farmer_id = Column(String(36), nullable=False)
#     prediction_id = Column(String(36), nullable=True)
#     role = Column(String(20), nullable=False)  # 'user' or 'assistant'
#     content = Column(Text, nullable=False)
#     disease_context = Column(String(200), nullable=True)
#     llm_provider = Column(String(50), nullable=True)
#     tokens_used = Column(Integer, nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow)