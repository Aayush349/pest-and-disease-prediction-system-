"""
SQLAlchemy database models
FIXED: Converted UUID to String for better SQLite compatibility
"""

from sqlalchemy import Column, String, Float, DateTime, Integer, Text, JSON
from datetime import datetime
import uuid
from ..database import Base

class Farmer(Base):
    """Farmer model"""
    __tablename__ = "farmers"
    
    # UUID ko String bana diya taaki SQLite mein error na aaye
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    location = Column(String(200), nullable=False) 
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Prediction(Base):
    """Disease prediction history"""
    __tablename__ = "predictions"
    
    # Fixed: String ID
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    farmer_id = Column(String, nullable=False) # Ab ye "real_farmer_123" jaisi string accept karega
    
    disease = Column(String(200), nullable=False)
    confidence = Column(Float, nullable=False)

    ndvi_score = Column(Float, nullable=True) 
    field_health = Column(String(100), nullable=True) # "High Stress", "Healthy"
    combined_risk_score = Column(String(100), nullable=True)
    
    # 👇 COLUMNS FOR HEATMAP & RADAR 👇
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    top5 = Column(JSON, nullable=True)
    treatment = Column(JSON, nullable=True)
    prevention = Column(JSON, nullable=True)
    image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatHistory(Base):
    """Chat conversation history"""
    __tablename__ = "chat_history"
    
    # Fixed: String ID
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    farmer_id = Column(String, nullable=False)
    
    prediction_id = Column(String, nullable=True)
    role = Column(String(20), nullable=False) 
    content = Column(Text, nullable=False)
    disease_context = Column(String(200), nullable=True)
    llm_provider = Column(String(50), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)












# """
# SQLAlchemy database models
# """

# from sqlalchemy import Column, String, Float, DateTime, Integer, Text, JSON
# from sqlalchemy.dialects.postgresql import UUID
# from datetime import datetime
# import uuid
# from ..database import Base

# class Farmer(Base):
#     """Farmer model"""
#     __tablename__ = "farmers"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     name = Column(String(100), nullable=False)
#     phone = Column(String(20), unique=True, nullable=False)
#     location = Column(String(200), nullable=False) # Ye "Indore" jaisa text hai
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# class Prediction(Base):
#     """Disease prediction history"""
#     __tablename__ = "predictions"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     farmer_id = Column(UUID(as_uuid=True), nullable=False)
#     disease = Column(String(200), nullable=False)
#     confidence = Column(Float, nullable=False)
    
#     # 👇 NEW COLUMNS ADDED FOR HEATMAP & RADAR 👇
#     latitude = Column(Float, nullable=True)  # Nullable rakha hai agar GPS fail ho jaye
#     longitude = Column(Float, nullable=True)
    
#     top5 = Column(JSON, nullable=True)
#     treatment = Column(JSON, nullable=True)
#     prevention = Column(JSON, nullable=True)
#     image_path = Column(String(500), nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow)

# class ChatHistory(Base):
#     """Chat conversation history"""
#     __tablename__ = "chat_history"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     farmer_id = Column(UUID(as_uuid=True), nullable=False)
#     prediction_id = Column(UUID(as_uuid=True), nullable=True)
#     role = Column(String(20), nullable=False) 
#     content = Column(Text, nullable=False)
#     disease_context = Column(String(200), nullable=True)
#     llm_provider = Column(String(50), nullable=True)
#     tokens_used = Column(Integer, nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow)











# # """
# # SQLAlchemy database models
# # """

# # from sqlalchemy import Column, String, Float, DateTime, Integer, Text, JSON
# # from sqlalchemy.dialects.postgresql import UUID
# # from datetime import datetime
# # import uuid
# # from ..database import Base

# # class Farmer(Base):
# #     """Farmer model"""
# #     __tablename__ = "farmers"
    
# #     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
# #     name = Column(String(100), nullable=False)
# #     phone = Column(String(20), unique=True, nullable=False)
# #     location = Column(String(200), nullable=False)
# #     created_at = Column(DateTime, default=datetime.utcnow)
# #     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# # class Prediction(Base):
# #     """Disease prediction history"""
# #     __tablename__ = "predictions"
    
# #     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
# #     farmer_id = Column(UUID(as_uuid=True), nullable=False)
# #     disease = Column(String(200), nullable=False)
# #     confidence = Column(Float, nullable=False)
# #     top5 = Column(JSON, nullable=True)
# #     treatment = Column(JSON, nullable=True)
# #     prevention = Column(JSON, nullable=True)
# #     image_path = Column(String(500), nullable=True)
# #     created_at = Column(DateTime, default=datetime.utcnow)

# # class ChatHistory(Base):
# #     """Chat conversation history"""
# #     __tablename__ = "chat_history"
    
# #     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
# #     farmer_id = Column(UUID(as_uuid=True), nullable=False)
# #     prediction_id = Column(UUID(as_uuid=True), nullable=True)
# #     role = Column(String(20), nullable=False)  # 'user' or 'assistant'
# #     content = Column(Text, nullable=False)
# #     disease_context = Column(String(200), nullable=True)
# #     llm_provider = Column(String(50), nullable=True)
# #     tokens_used = Column(Integer, nullable=True)
# #     created_at = Column(DateTime, default=datetime.utcnow)
