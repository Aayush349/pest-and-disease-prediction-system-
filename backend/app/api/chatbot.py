from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..ml.chatbot_agent import ChatbotAgent
from ..utils.logger import Logger

router = APIRouter(tags=["Chatbot"])
logger = Logger(__name__)

# Initialize chatbot
chatbot = ChatbotAgent()

class ChatMessage(BaseModel):
    message: str
    image_analysis: Optional[dict] = None

@router.post("/message")
async def send_message(request: ChatMessage):
    """Send message to chatbot"""
    try:
        response = chatbot.get_response(
            message=request.message,
            image_analysis=request.image_analysis
        )
        
        if not response.get("success"):
            raise HTTPException(status_code=500, detail=response.get("error"))
        
        return {
            "success": True,
            "data": response
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/explain-disease")
async def explain_disease(disease: str, image_analysis: dict):
    """Get detailed explanation of disease"""
    try:
        response = chatbot.explain_disease(disease, image_analysis)
        
        if not response.get("success"):
            raise HTTPException(status_code=500, detail=response.get("error"))
        
        return {
            "success": True,
            "data": response
        }
        
    except Exception as e:
        logger.error(f"Explanation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
