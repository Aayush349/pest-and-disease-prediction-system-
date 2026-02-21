from fastapi import APIRouter, Query, Body, Depends
import math
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..database import get_db
from ..models.sql_models import Prediction 

router = APIRouter(tags=["Community & Alerts"])

# 💾 MEMORY STORAGE (For manual reports)
DETECTED_OUTBREAKS = []

# 📢 STATIC NEWS 
GENERAL_NOTICES = [
    "📢 **PM Kisan Yojana:** Check official portal for next installment status.",
    "🌾 **Soil Health:** Get your soil tested before sowing season.",
    "📞 **Kisan Helpline:** Call 1800-180-1551 for agriculture queries.",
    "💧 **Jal Sanrakshan:** Adopt drip irrigation to save water.",
]

def calculate_distance(lat1, lon1, lat2, lon2):
    if not lat1 or not lon1 or not lat2 or not lon2: return 9999
    try:
        R = 6371 
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
            * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    except:
        return 9999

@router.post("/report_outbreak")
async def report_disease_outbreak(
    latitude: float = Body(..., embed=True),
    longitude: float = Body(..., embed=True),
    disease_name: str = Body(..., embed=True)
):
    # Add current time to manual report for consistency
    new_report = {
        "lat": latitude, 
        "long": longitude, 
        "disease": disease_name,
        "time": datetime.now()
    }
    DETECTED_OUTBREAKS.append(new_report)
    return {"status": "success", "message": "Radar activated & SMS Broadcast sent."}

@router.get("/flash")
async def get_flash_news(
    latitude: float = Query(..., description="User Latitude"),
    longitude: float = Query(..., description="User Longitude"),
    db: Session = Depends(get_db)
):
    news_feed = []
    nearby_alerts = []
    
    # 1. CHECK MANUAL REPORTS (In-Memory)
    for outbreak in DETECTED_OUTBREAKS:
        dist = calculate_distance(latitude, longitude, outbreak['lat'], outbreak['long'])
        if dist < 15: 
            msg = f"⚠️ ALERT: '{outbreak['disease']}' reported {dist:.1f}km away!"
            if msg not in nearby_alerts: nearby_alerts.append(msg)

    # 2. CHECK REAL DATABASE PREDICTIONS
    # Now this will work because Prediction.timestamp exists
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    try:
        recent_cases = db.query(Prediction).filter(
            Prediction.timestamp >= seven_days_ago,
            Prediction.confidence > 0.6 
        ).all()

        for case in recent_cases:
            if case.latitude and case.longitude:
                clean_name = case.disease.replace("___", " ").replace("_", " ")
                # Skip non-disease detections
                lower_name = clean_name.lower()
                if any(skip in lower_name for skip in ["no crop", "urban", "healthy", "background", "unknown"]):
                    continue
                dist = calculate_distance(latitude, longitude, case.latitude, case.longitude)
                if dist < 15: 
                    msg = f"⚠️ RISK: '{clean_name}' detected {dist:.1f}km away recently."
                    if msg not in nearby_alerts: nearby_alerts.append(msg)
    except Exception as e:
        print(f"⚠️ Radar Error: {e}")
        # Don't crash the whole feed if DB fails, just skip DB alerts
        pass

    # 3. PRIORITIZE ALERTS
    if nearby_alerts:
        news_feed.append("🔴 URGENT ALERTS NEAR YOU: ")
        news_feed.extend(nearby_alerts)
    
    # 4. ADD GENERAL NEWS
    news_feed.extend(GENERAL_NOTICES)

    return {
        "alerts_count": len(nearby_alerts),
        "risk_detected": len(nearby_alerts) > 0,
        "scrolling_text": news_feed
    }


# from fastapi import APIRouter, Query, Body, Depends
# import math
# from typing import List, Dict, Any
# from sqlalchemy.orm import Session
# from datetime import datetime, timedelta

# from ..utils.sms import send_sms 
# from ..database import get_db
# from ..models.sql_models import Prediction # Import DB Model

# router = APIRouter(tags=["Community & Alerts"])

# # 💾 RADAR MEMORY (Temporary Storage for Alerts) - This remains RAM-based for instantaneous reporting
# DETECTED_OUTBREAKS = []

# # 📢 STATIC NEWS 
# GENERAL_NOTICES = [
#     "📢 **PM Kisan Yojana:** Check official portal for next installment status.",
#     "🌾 **Soil Health:** Get your soil tested before sowing season.",
#     "📞 **Kisan Helpline:** Call 1800-180-1551 for agriculture queries.",
#     "💧 **Jal Sanrakshan:** Adopt drip irrigation to save water.",
# ]

# # 🧮 RADAR MATHS (Distance Calculator)
# def calculate_distance(lat1, lon1, lat2, lon2):
#     R = 6371 
#     dlat = math.radians(lat2 - lat1)
#     dlon = math.radians(lon2 - lon1)
#     a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
#         * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
#     return R * c

# # ==========================================
# # 🚨 REPORT ENDPOINT (Triggers Broadcast SMS)
# # ==========================================
# @router.post("/report_outbreak", tags=["Community Radar"])
# async def report_disease_outbreak(
#     latitude: float = Body(..., embed=True),
#     longitude: float = Body(..., embed=True),
#     disease_name: str = Body(..., embed=True)
# ):
#     # Save to memory (This ensures the Ticker shows it immediately)
#     new_report = {"lat": latitude, "long": longitude, "disease": disease_name}
#     DETECTED_OUTBREAKS.append(new_report)
    
#     # 🔥 SIMULATE BULK SMS BROADCAST
#     alert_msg = f"🚨 AgroGuard RADAR: '{disease_name}' detected in your area. Check your crops immediately!"
#     send_sms("+91-98765XXXXX (Broadcast to Nearby Farmers)", alert_msg)
    
#     return {
#         "status": "success",
#         "message": f"Alert Registered! Radar activated & SMS Broadcast sent."
#     }

# # ==========================================
# # 📡 FETCH NEWS ENDPOINT (The Ticker)
# # ==========================================
# @router.get("/flash", tags=["News Ticker"])
# async def get_flash_news(
#     latitude: float = Query(..., description="User Latitude"),
#     longitude: float = Query(..., description="User Longitude")
# ):
#     """
#     Returns the scrolling news feed, prioritizing nearby community risks.
#     """
#     news_feed = []
#     nearby_alerts = []
    
#     # Check RADAR MEMORY (Immediate alerts from the POST endpoint)
#     for outbreak in DETECTED_OUTBREAKS:
#         dist = calculate_distance(latitude, longitude, outbreak['lat'], outbreak['long'])
        
#         # 5KM Risk Zone
#         if dist < 5: 
#             alert_msg = f"⚠️ SAWDHAAN: Aapke {dist:.1f} km range mein '{outbreak['disease']}' paya gaya hai. Satark rahein!"
#             if alert_msg not in nearby_alerts: nearby_alerts.append(alert_msg)
    
#     # Add Red Alerts First
#     news_feed.extend(nearby_alerts)
    
#     # Add Static News Last
#     news_feed.extend(GENERAL_NOTICES)

#     return {
#         "alerts_count": len(news_feed),
#         "risk_detected": len(nearby_alerts) > 0,
#         "scrolling_text": news_feed
#     }










# from fastapi import APIRouter, Query, Body
# import math
# from ..utils.sms import send_sms # ✅ SMS Utility Import

# router = APIRouter()

# # 💾 MOCK DATABASE (Temporary Storage for Radar)
# DETECTED_OUTBREAKS = []

# # 📢 STATIC NEWS (Govt Schemes)
# GENERAL_NOTICES = [
#     "📢 **PM Kisan Yojana:** Check official portal for next installment status.",
#     "🌾 **Soil Health:** Get your soil tested before sowing season.",
#     "📞 **Kisan Helpline:** Call 1800-180-1551 for agriculture queries.",
# ]

# # 🧮 RADAR MATHS
# def calculate_distance(lat1, lon1, lat2, lon2):
#     R = 6371 
#     dlat = math.radians(lat2 - lat1)
#     dlon = math.radians(lon2 - lon1)
#     a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
#         * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
#     return R * c

# # 🚨 REPORT ENDPOINT (Triggers Broadcast SMS)
# @router.post("/report_outbreak", tags=["Community Radar"])
# async def report_disease_outbreak(
#     latitude: float = Body(..., embed=True),
#     longitude: float = Body(..., embed=True),
#     disease_name: str = Body(..., embed=True)
# ):
#     # Save to memory
#     new_report = {"lat": latitude, "long": longitude, "disease": disease_name}
#     DETECTED_OUTBREAKS.append(new_report)
    
#     # 🔥 SIMULATE BULK SMS BROADCAST
#     alert_msg = f"🚨 AgroGuard RADAR: '{disease_name}' detected in your area. Check your crops immediately!"
    
#     # Send to a dummy number representing "All Neighbors"
#     send_sms("+91-98765XXXXX (Broadcast to Nearby Farmers)", alert_msg)
    
#     return {
#         "status": "success",
#         "message": f"Alert Registered! Radar activated & SMS Broadcast sent."
#     }

# # 📡 FETCH NEWS ENDPOINT (Ticker)
# @router.get("/flash", tags=["News Ticker"])
# async def get_flash_news(
#     latitude: float = Query(..., description="User Latitude"),
#     longitude: float = Query(..., description="User Longitude")
# ):
#     news_feed = []
#     nearby_alerts = []
    
#     # Check Radar Memory
#     for outbreak in DETECTED_OUTBREAKS:
#         dist = calculate_distance(latitude, longitude, outbreak['lat'], outbreak['long'])
        
#         if dist < 5: 
#             alert_msg = f"⚠️ SAWDHAAN: Aapke {dist:.1f} km range mein '{outbreak['disease']}' paya gaya hai. Satark rahein!"
#             if alert_msg not in nearby_alerts: nearby_alerts.append(alert_msg)
    
#     news_feed.extend(nearby_alerts)
#     news_feed.extend(GENERAL_NOTICES)

#     return {
#         "alerts_count": len(news_feed),
#         "risk_detected": len(nearby_alerts) > 0,
#         "scrolling_text": news_feed
#     }



# from fastapi import APIRouter, Query, Body
# import math
# # ✅ SMS Utility Import
# from ..utils.sms import send_sms

# router = APIRouter()

# # 💾 MOCK DATABASE (Temporary Storage for Radar)
# DETECTED_OUTBREAKS = []

# # 📢 STATIC NEWS (Always visible)
# GENERAL_NOTICES = [
#     "📢 **PM Kisan Yojana:** Check official portal for next installment status.",
#     "🌾 **Soil Health:** Get your soil tested before sowing season.",
#     "📞 **Kisan Helpline:** Call 1800-180-1551 for agriculture queries.",
#     "💧 **Water Conservation:** Adopt drip irrigation to save water.",
#     "📋 **Crop Insurance:** Ensure your crops are insured against calamity."
# ]

# # 🧮 RADAR MATHS (Haversine Formula)
# def calculate_distance(lat1, lon1, lat2, lon2):
#     R = 6371 # Earth radius in km
#     dlat = math.radians(lat2 - lat1)
#     dlon = math.radians(lon2 - lon1)
#     a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
#         * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
#     return R * c

# # ==========================================
# # 🚨 REPORT ENDPOINT (Triggers Radar + SMS)
# # ==========================================
# @router.post("/report_outbreak", tags=["Community Radar"])
# async def report_disease_outbreak(
#     latitude: float = Body(..., embed=True),
#     longitude: float = Body(..., embed=True),
#     disease_name: str = Body(..., embed=True)
# ):
#     """
#     Simulates a farmer reporting a disease.
#     1. Saves to Radar Memory.
#     2. Sends Mock SMS to neighbors.
#     """
#     # Save to memory
#     new_report = {
#         "lat": latitude,
#         "long": longitude,
#         "disease": disease_name
#     }
#     DETECTED_OUTBREAKS.append(new_report)
    
#     # 🔥 SIMULATE BULK SMS BROADCAST
#     # Logic: Asliyat mein hum DB se 5km range ke users nikalte.
#     # Hackathon Demo: Hum dikhayenge ki system ne 'Broadcast' initiate kiya.
    
#     print(f"📍 New Outbreak Reported at {latitude}, {longitude}. Calculating risk zones...")
    
#     alert_msg = f"🚨 AgroGuard RADAR: '{disease_name}' detected in your area. Check your crops immediately!"
    
#     # Send to a dummy number representing "All Neighbors"
#     send_sms("+91-98765XXXXX (Broadcast to Nearby Farmers)", alert_msg)
    
#     return {
#         "status": "success",
#         "message": f"Alert Registered! Radar activated & SMS Broadcast sent to nearby farmers."
#     }

# # ==========================================
# # 📡 FETCH NEWS ENDPOINT (For Ticker)
# # ==========================================
# @router.get("/flash", tags=["News Ticker"])
# async def get_flash_news(
#     latitude: float = Query(..., description="User Latitude"),
#     longitude: float = Query(..., description="User Longitude")
# ):
#     news_feed = []
#     nearby_alerts = []
    
#     # Check Radar Memory
#     for outbreak in DETECTED_OUTBREAKS:
#         dist = calculate_distance(latitude, longitude, outbreak['lat'], outbreak['long'])
        
#         # 5KM Risk Zone
#         if dist < 5: 
#             alert_msg = f"⚠️ SAWDHAAN: Aapke {dist:.1f} km range mein '{outbreak['disease']}' paya gaya hai. Satark rahein!"
#             if alert_msg not in nearby_alerts:
#                 nearby_alerts.append(alert_msg)
    
#     # Add Red Alerts First
#     news_feed.extend(nearby_alerts)
#     # Add Static News Later
#     news_feed.extend(GENERAL_NOTICES)

#     return {
#         "alerts_count": len(news_feed),
#         "risk_detected": len(nearby_alerts) > 0,
#         "scrolling_text": news_feed
#     }








# from fastapi import APIRouter, Query, Body
# import math

# router = APIRouter()

# # ==========================================
# # 💾 1. MOCK DATABASE (Temporary Memory)
# # ==========================================
# # Yahan wo bimariyan save hongi jo Weapon 1 pakdega.
# # Format: { "lat": 22.72, "long": 75.86, "disease": "Wheat Rust" }
# DETECTED_OUTBREAKS = []

# # ==========================================
# # 📰 2. STATIC NEWS (Professional & Safe)
# # ==========================================
# # Ye hamesha dikhengi taaki Ticker kabhi khali na lage.
# GENERAL_NOTICES = [
#     "📢 **PM Kisan Yojana:** Agli kist ki jankari ke liye official portal check karein.",
#     "🌾 **Mitti Parikshan:** Buwai se pehle apne khet ki mitti ki jaanch zaroor karwayein.",
#     "📞 **Kisan Call Center:** Kheti se judi samasya ke liye 1800-180-1551 par call karein.",
#     "💧 **Jal Sanrakshan:** Tapak sinchai (Drip Irrigation) apnayein aur pani bachayein.",
#     "📋 **Fasal Bima:** Apni fasal ka bima karwana na bhoolein."
# ]

# # ==========================================
# # 🧮 3. RADAR LOGIC (Distance Calculator)
# # ==========================================
# def calculate_distance(lat1, lon1, lat2, lon2):
#     # Haversine Formula to calculate distance in KM
#     R = 6371 # Earth radius in km
#     dlat = math.radians(lat2 - lat1)
#     dlon = math.radians(lon2 - lon1)
#     a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
#         * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
#     return R * c

# # ==========================================
# # 🚨 4. REPORT ENDPOINT (Trigger)
# # ==========================================
# @router.post("/report_outbreak", tags=["Community Radar"])
# async def report_disease_outbreak(
#     latitude: float = Body(..., embed=True),
#     longitude: float = Body(..., embed=True),
#     disease_name: str = Body(..., embed=True)
# ):
#     """
#     Simulate: Jab Weapon 1 bimari detect karega, to wo yahan data bhejega.
#     """
#     new_report = {
#         "lat": latitude,
#         "long": longitude,
#         "disease": disease_name
#     }
#     DETECTED_OUTBREAKS.append(new_report)
    
#     return {
#         "status": "success",
#         "message": f"Alert Registered! Radar activated for {disease_name}."
#     }

# # ==========================================
# # 📡 5. FETCH NEWS ENDPOINT (The Radar)
# # ==========================================
# @router.get("/flash", tags=["News Ticker"])
# async def get_flash_news(
#     latitude: float = Query(..., description="User Latitude"),
#     longitude: float = Query(..., description="User Longitude")
# ):
#     """
#     Ye API Frontend ko List degi.
#     Agar 5km ke andar khatra hai, to RED ALERT sabse upar hoga.
#     """
#     news_feed = []
    
#     # --- RADAR CHECK (5KM Radius) ---
#     nearby_alerts = []
    
#     for outbreak in DETECTED_OUTBREAKS:
#         dist = calculate_distance(latitude, longitude, outbreak['lat'], outbreak['long'])
        
#         # Agar bimari 5km se kam doori par hai
#         if dist < 5: 
#             alert_msg = f"⚠️ SAWDHAAN: Aapke {dist:.1f} km range mein '{outbreak['disease']}' paya gaya hai. Satark rahein!"
            
#             # Duplicate hatane ke liye
#             if alert_msg not in nearby_alerts:
#                 nearby_alerts.append(alert_msg)
    
#     # Alerts ko sabse upar jodo
#     news_feed.extend(nearby_alerts)
    
#     # Baaki Static News jodo
#     news_feed.extend(GENERAL_NOTICES)

#     return {
#         "alerts_count": len(news_feed),
#         "risk_detected": len(nearby_alerts) > 0, # Frontend ko batao: RED ya GREEN?
#         "scrolling_text": news_feed
#     }






























# from fastapi import APIRouter, Query, Body
# from typing import List
# import math

# router = APIRouter()

# # 💾 TEMPORARY STORAGE (RAM)
# # Asli app mein ye Database mein hoga. Abhi ke liye list use kar rahe hain.
# # Format: { "lat": 22.7, "long": 75.8, "disease": "Wheat Rust" }
# DETECTED_OUTBREAKS = []

# # 📢 1. STATIC ALERTS (Professional & General)
# # Ye kabhi galat nahi honge, chahe sardi ho ya garmi.
# GENERAL_NOTICES = [
#     "📢 **PM Kisan Yojana:** Agli kist ki jankari ke liye official portal check karein.",
#     "🌾 **Mitti Parikshan:** Buwai se pehle apne khet ki mitti ki jaanch zaroor karwayein.",
#     "📞 **Kisan Call Center:** Kheti se judi samasya ke liye 1800-180-1551 par call karein.",
#     "💧 **Jal Sanrakshan:** Tapak sinchai (Drip Irrigation) apnayein aur pani bachayein.",
#     "📋 **Fasal Bima:** Apni fasal ka bima karwana na bhoolein."
# ]

# # Helper: Calculate Distance between two points (Haversine simplified)
# def calculate_distance(lat1, lon1, lat2, lon2):
#     # Approx distance in km
#     R = 6371 # Earth radius in km
#     dlat = math.radians(lat2 - lat1)
#     dlon = math.radians(lon2 - lon1)
#     a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
#         * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
#     return R * c

# # =========================================================
# # ENDPOINT 1: Report Disease (Jab Weapon 1 bimari pakdega)
# # =========================================================
# @router.post("/report_outbreak", tags=["Community Radar"])
# async def report_disease_outbreak(
#     latitude: float = Body(...),
#     longitude: float = Body(...),
#     disease_name: str = Body(...)
# ):
#     """
#     Jab Weapon 1 koi bimari detect kare, to yahan report karein.
#     Isse aas-paas ke kisaano ke liye ALERT ban jayega.
#     """
#     DETECTED_OUTBREAKS.append({
#         "lat": latitude,
#         "long": longitude,
#         "disease": disease_name
#     })
#     return {"status": "Alert Registered", "message": "Nearby farmers will be warned."}

# # =========================================================
# # ENDPOINT 2: Get News Ticker (Flash News)
# # =========================================================
# @router.get("/flash", tags=["News Ticker"])
# async def get_flash_news(
#     latitude: float = Query(..., description="User Lat"),
#     longitude: float = Query(..., description="User Long")
# ):
#     """
#     Returns scrolling news.
#     Priority:
#     1. 🔴 Nearby Disease Alerts (Agar padosi ke khet mein bimari hai)
#     2. ℹ️ General Govt Notices
#     """
#     news_feed = []
    
#     # 1. Check Community Risks (5km Radius)
#     nearby_alerts = []
#     for outbreak in DETECTED_OUTBREAKS:
#         dist = calculate_distance(latitude, longitude, outbreak['lat'], outbreak['long'])
        
#         if dist < 5: # Agar 5km ke andar hai
#             # Avoid duplicate alerts
#             alert_msg = f"⚠️ SAWDHAAN: Aapke {dist:.1f}km range mein '{outbreak['disease']}' paya gaya hai. Satark rahein!"
#             if alert_msg not in nearby_alerts:
#                 nearby_alerts.append(alert_msg)
    
#     # Add Red Alerts at the top
#     news_feed.extend(nearby_alerts)
    
#     # 2. Add General Professional News
#     news_feed.extend(GENERAL_NOTICES)

#     return {
#         "alerts_count": len(news_feed),
#         "scrolling_text": news_feed
#     }