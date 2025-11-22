"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ===============================================================
#  DISEASE PREDICTION SCHEMAS
# ===============================================================

class PredictionResponse(BaseModel):
    """Disease prediction response"""

    disease: str = Field(..., description="Predicted disease name")
    confidence: float = Field(
        ..., ge=0, le=1, description="Confidence score (0-1)"
    )

    # OPTIONAL — because disease.py does NOT return top5
    top5: Optional[List[Dict[str, Any]]] = Field(
        None, description="Top 5 model predictions"
    )

    treatment: List[str] = Field(
        ..., description="Treatment recommendations"
    )

    # OPTIONAL — disease.py does not return prevention
    prevention: Optional[List[str]] = Field(
        None, description="Prevention tips"
    )
    
    # ✅ NEW FIELDS (Audio & Language Support)
    language: Optional[str] = "en"
    audio_url: Optional[str] = Field(
        None, description="URL to generated audio file (Agro-Voice)"
    )

    # OPTIONAL fields — disease.py includes these
    all_predictions: Optional[Dict[str, float]] = None
    filtered_predictions: Optional[Dict[str, float]] = None

    success: bool = True


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    success: bool = False


# ===============================================================
#  CHAT SCHEMAS
# ===============================================================

class ChatMessage(BaseModel):
    """Single chat message"""
    role: str
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat request"""
    message: str
    farmer_id: str
    image_path: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response"""
    message: str
    disease: Optional[str] = None
    confidence: Optional[float] = None
    treatment: Optional[List[str]] = None
    provider: str = "openai"
    success: bool = True


# ===============================================================
#  FARMER SCHEMAS
# ===============================================================

class FarmerCreate(BaseModel):
    name: str
    phone: str
    location: str


class FarmerResponse(BaseModel):
    id: str
    name: str
    phone: str
    location: str
    created_at: str


# ===============================================================
#  HEALTH CHECK
# ===============================================================

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    timestamp: str










# """
# Pydantic schemas for request/response validation
# """

# from pydantic import BaseModel, Field
# from typing import List, Optional, Dict, Any


# # ===============================================================
# #  DISEASE PREDICTION SCHEMAS
# # ===============================================================

# class PredictionResponse(BaseModel):
#     """Disease prediction response"""

#     disease: str = Field(..., description="Predicted disease name")
#     confidence: float = Field(
#         ..., ge=0, le=1, description="Confidence score (0-1)"
#     )

#     # OPTIONAL — because disease.py does NOT return top5
#     top5: Optional[List[Dict[str, Any]]] = Field(
#         None, description="Top 5 model predictions"
#     )

#     treatment: List[str] = Field(
#         ..., description="Treatment recommendations"
#     )

#     # OPTIONAL — disease.py does not return prevention
#     prevention: Optional[List[str]] = Field(
#         None, description="Prevention tips"
#     )

#     # OPTIONAL fields — disease.py includes these
#     all_predictions: Optional[Dict[str, float]] = None
#     filtered_predictions: Optional[Dict[str, float]] = None

#     success: bool = True


# class ErrorResponse(BaseModel):
#     """Error response"""
#     error: str
#     detail: Optional[str] = None
#     success: bool = False


# # ===============================================================
# #  CHAT SCHEMAS
# # ===============================================================

# class ChatMessage(BaseModel):
#     """Single chat message"""
#     role: str
#     content: str
#     timestamp: Optional[str] = None


# class ChatRequest(BaseModel):
#     """Chat request"""
#     message: str
#     farmer_id: str
#     image_path: Optional[str] = None


# class ChatResponse(BaseModel):
#     """Chat response"""
#     message: str
#     disease: Optional[str] = None
#     confidence: Optional[float] = None
#     treatment: Optional[List[str]] = None
#     provider: str = "openai"
#     success: bool = True


# # ===============================================================
# #  FARMER SCHEMAS
# # ===============================================================

# class FarmerCreate(BaseModel):
#     name: str
#     phone: str
#     location: str


# class FarmerResponse(BaseModel):
#     id: str
#     name: str
#     phone: str
#     location: str
#     created_at: str


# # ===============================================================
# #  HEALTH CHECK
# # ===============================================================

# class HealthResponse(BaseModel):
#     status: str = "healthy"
#     version: str
#     timestamp: str





# """
# Pydantic schemas for request/response validation
# """

# from pydantic import BaseModel, Field
# from typing import List, Optional, Dict, Any

# # ============= Disease Prediction =============

# class PredictionResponse(BaseModel):
#     """Disease prediction response"""
#     disease: str = Field(..., description="Predicted disease name")
#     confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
#     top5: List[Dict[str, Any]] = Field(..., description="Top 5 predictions")
#     treatment: List[str] = Field(..., description="Treatment recommendations")
#     prevention: List[str] = Field(..., description="Prevention tips")
#     success: bool = True

# class ErrorResponse(BaseModel):
#     """Error response"""
#     error: str
#     detail: Optional[str] = None
#     success: bool = False

# # ============= Chat =============

# class ChatMessage(BaseModel):
#     """Single chat message"""
#     role: str = Field(..., description="'user' or 'assistant'")
#     content: str = Field(..., description="Message content")
#     timestamp: Optional[str] = None

# class ChatRequest(BaseModel):
#     """Chat request"""
#     message: str = Field(..., min_length=1, max_length=1000)
#     farmer_id: str = Field(..., description="Farmer ID")
#     image_path: Optional[str] = None

# class ChatResponse(BaseModel):
#     """Chat response"""
#     message: str = Field(..., description="AI response")
#     disease: Optional[str] = None
#     confidence: Optional[float] = None
#     treatment: Optional[List[str]] = None
#     provider: str = Field("openai", description="LLM provider used")
#     success: bool = True

# # ============= Farmer =============

# class FarmerCreate(BaseModel):
#     """Create farmer"""
#     name: str = Field(..., min_length=1, max_length=100)
#     phone: str = Field(..., pattern=r'^\d{10}$', description="10-digit phone")
#     location: str = Field(..., min_length=1, max_length=200)

# class FarmerResponse(BaseModel):
#     """Farmer response"""
#     id: str
#     name: str
#     phone: str
#     location: str
#     created_at: str

# # ============= Health Check =============

# class HealthResponse(BaseModel):
#     """Health check response"""
#     status: str = "healthy"
#     version: str
#     timestamp: str
