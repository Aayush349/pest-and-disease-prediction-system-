"""
Chat endpoints with disease context
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from pydantic import BaseModel
from pathlib import Path
import shutil
import uuid
from ..config import get_settings
from ..ml.chatbot_agent import process_chat_with_image, process_chat_without_image
from ..utils.logger import Logger

router = APIRouter(prefix="/api/chat", tags=["chat"])
settings = get_settings()
logger = Logger(__name__)

class ChatRequest(BaseModel):
    """Chat request without image"""
    message: str
    farmer_id: str

@router.post("/message")
async def chat_message(request: ChatRequest):
    """
    Send text-only message to chatbot
    
    **Example:**
    ```
    {
        "message": "How do I prevent early blight?",
        "farmer_id": "farmer_123"
    }
    ```
    """
    
    try:
        if not request.message or len(request.message) == 0:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        logger.info(f"Processing chat from {request.farmer_id}")
        
        result = process_chat_without_image(request.message)
        
        if not result.get("success"):
            logger.error(f"Chat failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        logger.success(f"✓ Chat response generated via {result.get('provider')}")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/with-image")
async def chat_with_image(
    file: UploadFile = File(...),
    message: str = Query(...),
    farmer_id: str = Query(...)
):
    """
    Send image + question to chatbot
    
    **Example:**
    ```
    curl -X POST "http://localhost:8000/api/chat/with-image" \
      -F "file=@disease.jpg" \
      -F "message=What should I do?" \
      -F "farmer_id=farmer_123"
    ```
    """
    
    # Validate
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only JPG/PNG allowed")
    
    if not message or len(message) == 0:
        raise HTTPException(status_code=400, detail="Message required")
    
    # Save image
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = upload_dir / unique_filename
    
    try:
        logger.info(f"Processing chat with image from {farmer_id}")
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process
        result = process_chat_with_image(str(file_path), message)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        logger.success(f"✓ Chat with image complete")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat with image error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if file_path.exists():
            file_path.unlink()
