#!/usr/bin/env python3
"""
WhatsApp Notification Service
Sends disease prediction alerts via Twilio WhatsApp API
Handles errors gracefully to prevent app crashes
"""

from typing import Dict, Any, Optional
import os
from ..utils.logger import Logger

logger = Logger(__name__)

# Try to import Twilio, but don't fail if not available
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("⚠️ Twilio library not installed. WhatsApp notifications will be disabled.")


def send_whatsapp_notification(
    phone_number: str,
    disease: str,
    confidence: float,
    treatment: list,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Send WhatsApp notification with disease prediction results.
    
    Args:
        phone_number: Recipient's phone number (format: +1234567890)
        disease: Detected disease name
        confidence: Prediction confidence (0-1)
        treatment: List of treatment steps
        language: Language code (default: en)
    
    Returns:
        Dict with status: {"success": bool, "message": str, "error": str|None}
    """
    
    # Check if Twilio is available
    if not TWILIO_AVAILABLE:
        error_msg = "Twilio library not installed. Run: pip install twilio"
        logger.warning(f"⚠️ WhatsApp notification skipped: {error_msg}")
        return {
            "success": False,
            "message": "WhatsApp notification disabled",
            "error": error_msg
        }
    
    # Get Twilio credentials from environment
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    
    # Validate credentials
    if not all([account_sid, auth_token, twilio_whatsapp_number]):
        error_msg = "Twilio credentials not configured in .env file"
        logger.warning(f"⚠️ WhatsApp notification skipped: {error_msg}")
        return {
            "success": False,
            "message": "WhatsApp not configured",
            "error": error_msg
        }
    
    # Validate phone number format
    if not phone_number or not phone_number.startswith("+"):
        error_msg = "Invalid phone number format. Must start with '+' and country code"
        logger.warning(f"⚠️ WhatsApp notification skipped: {error_msg}")
        return {
            "success": False,
            "message": "Invalid phone number",
            "error": error_msg
        }
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Format WhatsApp message
        disease_clean = disease.replace("___", " ").replace("_", " ").title()
        confidence_pct = round(confidence * 100, 1)
        
        # Build treatment summary (max 3 steps for SMS brevity)
        treatment_summary = ""
        if treatment and len(treatment) > 0:
            treatment_steps = treatment[:3]  # Limit to 3 steps
            treatment_summary = "\\n".join([f"{i+1}. {step}" for i, step in enumerate(treatment_steps)])
        
        # Create message
        message_body = f"""🌾 *AgroGuard Disease Alert*

🔍 *Disease Detected:* {disease_clean}
📊 *Confidence:* {confidence_pct}%

💊 *Treatment Steps:*
{treatment_summary}

📱 View full report in the AgroGuard app.
"""
        
        # Format recipient number for WhatsApp
        recipient_whatsapp = f"whatsapp:{phone_number}"
        
        # Send message
        message = client.messages.create(
            from_=twilio_whatsapp_number,
            body=message_body,
            to=recipient_whatsapp
        )
        
        logger.success(f"✅ WhatsApp notification sent to {phone_number}. SID: {message.sid}")
        
        return {
            "success": True,
            "message": "WhatsApp notification sent successfully",
            "error": None,
            "message_sid": message.sid
        }
        
    except TwilioRestException as e:
        # Handle Twilio-specific errors
        error_msg = str(e)
        
        # Check for common error codes
        if "21211" in error_msg or "not a valid" in error_msg.lower():
            user_msg = "Invalid phone number. Please check the number format."
        elif "21608" in error_msg or "unverified" in error_msg.lower():
            user_msg = "Phone number not verified in Twilio free trial. Please verify or upgrade to paid plan."
        elif "20003" in error_msg or "authenticate" in error_msg.lower():
            user_msg = "Twilio authentication failed. Please check credentials."
        elif "insufficient" in error_msg.lower() or "balance" in error_msg.lower():
            user_msg = "SMS not sent because of credit limit exhausted. Please upgrade to paid plan."
        else:
            user_msg = "WhatsApp message could not be sent. Please try again later."
        
        logger.error(f"❌ Twilio WhatsApp error: {error_msg}")
        
        return {
            "success": False,
            "message": user_msg,
            "error": error_msg
        }
        
    except Exception as e:
        # Handle any other unexpected errors
        error_msg = str(e)
        logger.error(f"❌ Unexpected error sending WhatsApp: {error_msg}")
        
        return {
            "success": False,
            "message": "SMS not sent due to technical error. Please try again later.",
            "error": error_msg
        }


def is_whatsapp_configured() -> bool:
    """Check if WhatsApp/Twilio is properly configured."""
    if not TWILIO_AVAILABLE:
        return False
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    
    return all([account_sid, auth_token, twilio_whatsapp_number])
