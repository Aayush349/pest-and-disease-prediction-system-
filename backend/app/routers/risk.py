from fastapi import APIRouter, Query, Depends
import requests
import joblib
from pathlib import Path
from typing import Optional
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from ..config import get_settings
from ..database import get_db
from ..models.sql_models import Prediction
from ..utils.sms import send_sms 
from ..utils.ndvi_fetcher import get_satellite_health 
from ..utils.mongo_sync import sync_to_cloud

router = APIRouter(tags=["Prediction Model (Environmental)"])
OPENWEATHER_KEY = "025fd0f7a6731edd3dcbc40f7fc5ecdd"

# --- CROP MAPPING (From File 3) ---
CROP_RISKS = {
    "tomato": ["Cold_Wet_Risk", "Warm_Humid_Risk", "High_Heat_Risk"],
    "potato": ["Cold_Wet_Risk"],
    "pepper": ["Warm_Humid_Risk"],
    "corn": ["Rainy_Risk", "Cold_Wet_Risk"],
    "wheat": ["Rainy_Risk"],
    "default": ["Cold_Wet_Risk", "Rainy_Risk"]
}

RISK_DISPLAY = {
    "Cold_Wet_Risk": "Fungal Blight (Late/Early)",
    "Warm_Humid_Risk": "Bacterial Rot / Spot",
    "Moderate_Dry_Risk": "Powdery Mildew",
    "Rainy_Risk": "Rust / Scab / Leaf Spot",
    "High_Heat_Risk": "Viral Infection / Mites",
    "No_Risk": "None"
}

# --- MODEL LOADING (From File 3) ---
try:
    project_root = Path(__file__).resolve().parents[3] 
    model_path = project_root / "ml" / "models" / "weather_risk_model.pkl"
    risk_model = joblib.load(model_path) if model_path.exists() else None
except Exception as e:
    risk_model = None

# --- API ENDPOINT ---
@router.get("/predict_outbreak")
async def predict_disease_risk(
    latitude: float = Query(..., description="Farm Lat"),
    longitude: float = Query(..., description="Farm Long"),
    crop_name: str = Query("tomato", description="Crop Name"),
    farmer_id: Optional[str] = Query(None, description="Optional Farmer ID for tracking"),
    farmer_phone: Optional[str] = Query(None, description="Phone for SMS Alert"),
    db: Session = Depends(get_db)
):
    # ---------------------------------------------------------
    # STEP 1: Weather Data Fetching
    # ---------------------------------------------------------
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_KEY}&units=metric"
        resp = requests.get(url)
        w_data = resp.json()
        curr_temp = w_data['main']['temp']
        curr_humidity = w_data['main']['humidity']
        is_raining = 1 if 'rain' in w_data else 0 
    except:
        curr_temp, curr_humidity, is_raining = 25.0, 60.0, 0

    # ---------------------------------------------------------
    # STEP 2: Satellite Analysis (Macro Level - From File 1 & 2)
    # ---------------------------------------------------------
    sat_report = get_satellite_health(latitude, longitude)
    ndvi_val = sat_report.get('ndvi', 0.0)
    sat_status = sat_report.get('status', 'Unknown')
    tile_url = sat_report.get('tile_url')
    provider = sat_report.get('provider', 'Satellite')

    # Street view link (useful for UI)
    street_view = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}"

    # Handle cases where satellite data is unavailable
    sat_available = sat_status not in ("Satellite Offline", "Data Unavailable", "Data Unavailable (Cloud/Server Error)")

    if not sat_available:
        land_type = "UNKNOWN"
        base_status = "UNKNOWN"
        status_color = "gray"
        land_msg = "⚠️ Satellite data unavailable. Proceeding with weather-only analysis."
        is_farm = True
    else:
        # Land Classification using NDVI (same thresholds as before)
        if ndvi_val < 0.22:
            land_type = "URBAN/CONCRETE"
            base_status = "NEUTRAL"
            status_color = "blue"
            land_msg = "📍 Non-agricultural zone. Satellite detects urban land."
            is_farm = False
        elif ndvi_val < 0.45:
            land_type = "AGRICULTURAL (STRESSED)"
            base_status = "WARNING"
            status_color = "yellow"
            land_msg = f"⚠️ Low vegetation vigor ({ndvi_val}). Crop is stressed."
            is_farm = True
        else:
            land_type = "AGRICULTURAL (HEALTHY)"
            base_status = "SAFE"
            status_color = "green"
            land_msg = "✅ Satellite confirms lush healthy crops."
            is_farm = True

    # ---------------------------------------------------------
    # STEP 3: AI Model Prediction (From File 3)
    # ---------------------------------------------------------
    if risk_model:
        env_prediction = risk_model.predict([[curr_temp, curr_humidity, is_raining]])[0]
    else:
        env_prediction = "No_Risk"

    # ---------------------------------------------------------
    # STEP 4: Risk Logic Integration (Hybrid)
    # ---------------------------------------------------------
    user_crop = crop_name.lower()
    
    # 4A. Determine Crop Susceptibility
    matched_key = "default"
    for key in CROP_RISKS:
        if key in user_crop: matched_key = key; break
    vulnerable_diseases = CROP_RISKS[matched_key]
    display_condition = RISK_DISPLAY.get(env_prediction, env_prediction)

    # 4B. Calculate Final Alert Status
    alert_status = "STABLE"
    message = f"{land_msg} Weather ({curr_temp}°C) is safe."

    if not is_farm:
        # If Urban, override everything to Neutral
        alert_status = "NEUTRAL"
        message = land_msg
        env_prediction = "N/A (Urban Area)"
    else:
        # If Farm, Apply AI + Weather Logic
        if env_prediction in vulnerable_diseases:
            alert_status = "HIGH RISK"
            status_color = "red"
            message = f"⚠️ ALERT: Weather favors '{display_condition}' in {user_crop}."
        elif env_prediction != "No_Risk":
            alert_status = "MODERATE"
            status_color = "yellow"
            message = f"ℹ️ Caution: Weather favors '{display_condition}'."

        # 4C. Combine with Satellite Stress (File 3 Logic)
        if land_type == "AGRICULTURAL (STRESSED)":
            if alert_status == "HIGH RISK":
                alert_status = "CRITICAL (Weather + Satellite Warning)"
            elif alert_status == "STABLE":
                alert_status = "ELEVATED (Satellite Stress Detected)"
                message = f"⚠️ Weather is safe, but Satellite detects crop stress (NDVI: {ndvi_val})."

    # ---------------------------------------------------------
    # STEP 5: SMS Alert Trigger
    # ---------------------------------------------------------
    sms_sent_status = False
    # Send SMS if High Risk/Critical OR if requested explicitly in logic
    if ("RISK" in alert_status or "CRITICAL" in alert_status) and is_farm:
        if farmer_phone:
            sms_body = f"AgroGuard Alert: {alert_status} for {user_crop}. {display_condition}. NDVI: {ndvi_val}. Check app."
            send_sms(farmer_phone, sms_body)
            sms_sent_status = True

    # ---------------------------------------------------------
    # STEP 6: Persist locally (SQLite) and trigger cloud sync
    # ---------------------------------------------------------
    try:
        new_record = Prediction(
            # Standard Fields
            id=str(uuid.uuid4()),
            farmer_id=farmer_phone if farmer_phone else "guest",
            disease=display_condition if is_farm else "No Crop/Urban",
            confidence=0.85 if is_farm else 1.0,
            latitude=latitude,
            longitude=longitude,

            # ✅ MISSING FIELDS ADDED HERE:
            ndvi_score=ndvi_val,
            field_health=land_type,
            combined_risk=alert_status,

            # Metadata
            top5=None,
            treatment={"advisory": message},
            prevention=None,
            image_path=None,
            created_at=datetime.utcnow()
        )

        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        # Fire-and-forget cloud sync
        record_dict = {
            "id": str(new_record.id),
            "latitude": latitude,
            "longitude": longitude,
            "risk_summary": alert_status,
            "disease": f"Risk Scan: {alert_status}",
            "ndvi_score": ndvi_val,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            sync_to_cloud(record_dict)
        except Exception as e:
            print(f"Cloud Sync skipped: {e}")

    except Exception as e:
        print(f"DB Error: {e}")
        # Pass, taaki kam se kam JSON response frontend tak pahunch jaye
        pass

    # ---------------------------------------------------------
    # STEP 7: Final JSON Response (Merged Structure)
    # ---------------------------------------------------------
    return {
        "land_context": {
            "type": land_type,
            "ndvi_score": ndvi_val,
            "marker_color": status_color,
            "street_view_url": street_view
        },
        "weather_snapshot": { 
            "temperature": f"{curr_temp}°C", 
            "humidity": f"{curr_humidity}%",
            "rain": "Yes" if is_raining else "No"
        },
        "ai_forecast": {
            "predicted_condition": env_prediction,
            "disease_name": display_condition if is_farm else "None",
            "risk_level": alert_status,
        },
        "advisory": message,
        "sms_status": "Sent Successfully" if sms_sent_status else "Not Required/No Phone"
    }

# from fastapi import APIRouter, Query
# import requests
# import joblib
# from pathlib import Path
# from typing import Optional
# from ..config import get_settings
# from ..utils.sms import send_sms 
# from ..utils.ndvi_fetcher import get_satellite_health # ✅ Import Sahi Hai

# router = APIRouter(tags=["Prediction Model (Environmental)"])
# OPENWEATHER_KEY = "025fd0f7a6731edd3dcbc40f7fc5ecdd"

# # --- CROP MAPPING ---
# CROP_RISKS = {
#     "tomato": ["Cold_Wet_Risk", "Warm_Humid_Risk", "High_Heat_Risk"],
#     "potato": ["Cold_Wet_Risk"],
#     "pepper": ["Warm_Humid_Risk"],
#     "corn": ["Rainy_Risk", "Cold_Wet_Risk"],
#     "wheat": ["Rainy_Risk"],
#     "default": ["Cold_Wet_Risk", "Rainy_Risk"]
# }

# RISK_DISPLAY = {
#     "Cold_Wet_Risk": "Fungal Blight (Late/Early)",
#     "Warm_Humid_Risk": "Bacterial Rot / Spot",
#     "Moderate_Dry_Risk": "Powdery Mildew",
#     "Rainy_Risk": "Rust / Scab / Leaf Spot",
#     "High_Heat_Risk": "Viral Infection / Mites",
#     "No_Risk": "None"
# }

# # --- MODEL LOADING ---
# try:
#     project_root = Path(__file__).resolve().parents[3] 
#     model_path = project_root / "ml" / "models" / "weather_risk_model.pkl"
#     risk_model = joblib.load(model_path) if model_path.exists() else None
# except Exception as e:
#     risk_model = None

# # --- API ENDPOINT ---
# @router.get("/predict_outbreak")
# async def predict_disease_risk(
#     latitude: float = Query(..., description="Farm Lat"),
#     longitude: float = Query(..., description="Farm Long"),
#     crop_name: str = Query("tomato", description="Crop Name"),
#     farmer_phone: Optional[str] = Query(None, description="Phone for SMS Alert")
# ):
#     # ---------------------------------------------------------
#     # STEP 1: Pehle Weather Data Fetch Karo (Zaroori Hai!)
#     # ---------------------------------------------------------
#     try:
#         url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_KEY}&units=metric"
#         resp = requests.get(url)
#         w_data = resp.json()
#         curr_temp = w_data['main']['temp']
#         curr_humidity = w_data['main']['humidity']
#         is_raining = 1 if 'rain' in w_data else 0 
#     except:
#         # Fallback agar API fail ho jaye
#         curr_temp = 25.0; curr_humidity = 60.0; is_raining = 0

#     # ---------------------------------------------------------
#     # STEP 2: Satellite Logic (NDVI) Fetch Karo
#     # ---------------------------------------------------------
#     sat_report = get_satellite_health(latitude, longitude)

#     # ---------------------------------------------------------
#     # STEP 3: AI Model Prediction
#     # ---------------------------------------------------------
#     env_prediction = risk_model.predict([[curr_temp, curr_humidity, is_raining]])[0] if risk_model else "No_Risk"
    
#     # ---------------------------------------------------------
#     # STEP 4: Risk Logic & Advisory Message Generate Karo
#     # ---------------------------------------------------------
#     user_crop = crop_name.lower()
#     matched_key = "default"
#     for key in CROP_RISKS:
#         if key in user_crop: matched_key = key; break
    
#     vulnerable_diseases = CROP_RISKS[matched_key]
#     display_condition = RISK_DISPLAY.get(env_prediction, env_prediction)
    
#     # Default Message
#     message = f"✅ Weather ({curr_temp}°C) is currently safe for {user_crop}."
#     alert_status = "STABLE"

#     # Agar Weather Risk hai
#     if env_prediction in vulnerable_diseases:
#         alert_status = "HIGH RISK"
#         message = f"⚠️ ALERT: Weather favors '{display_condition}' in {user_crop}."
#     elif env_prediction != "No_Risk":
#         alert_status = "MODERATE"
#         message = f"ℹ️ Caution: Weather favors '{display_condition}'."

#     # ---------------------------------------------------------
#     # STEP 5: Final Combined Risk (Weather + Satellite)
#     # ---------------------------------------------------------
#     # Agar Satellite bhi Stress dikha raha hai, toh Risk badha do
#     if sat_report['status'] == "High Stress" or sat_report['status'] == "Moderate Stress":
#         if alert_status == "HIGH RISK":
#             alert_status = "CRITICAL (Weather + Satellite Warning)"
#         else:
#             alert_status = "ELEVATED (Satellite Stress Detected)"
        
#         message += f" 🛰️ Satellite also detects stress in the field."

#     # ---------------------------------------------------------
#     # STEP 6: SMS Alert Send Karo
#     # ---------------------------------------------------------
#     sms_sent_status = False
#     if "RISK" in alert_status or "CRITICAL" in alert_status:
#         if farmer_phone:
#             sms_body = f"AgroGuard: {alert_status} for {user_crop}. {display_condition} likely. Check app for remedies."
#             send_sms(farmer_phone, sms_body)
#             sms_sent_status = True

#     # ---------------------------------------------------------
#     # STEP 7: Final Return
#     # ---------------------------------------------------------
#     return {
#         "weather_snapshot": { "temperature": f"{curr_temp}°C", "humidity": f"{curr_humidity}%" },
#         "satellite_analysis": sat_report,
#         "ai_forecast": {
#             "environmental_condition": env_prediction,
#             "risk_level": alert_status,
#         },
#         "advisory": message,
#         "sms_alert": "Sent Successfully" if sms_sent_status else "Not Needed/No Phone"
#     }


# from fastapi import APIRouter, Query
# import requests
# import joblib
# import numpy as np
# from pathlib import Path
# from typing import Optional
# from ..config import get_settings
# from ..utils.sms import send_sms # ✅ SMS Import
# from ..utils.ndvi_fetcher import get_satellite_health

# router = APIRouter(tags=["Prediction Model (Environmental)"])
# OPENWEATHER_KEY = "025fd0f7a6731edd3dcbc40f7fc5ecdd"

# # --- CROP MAPPING (Shortened for display, but full logic remains) ---
# CROP_RISKS = {
#     "tomato": ["Cold_Wet_Risk", "Warm_Humid_Risk", "High_Heat_Risk"],
#     "potato": ["Cold_Wet_Risk"],
#     "pepper": ["Warm_Humid_Risk"],
#     "corn": ["Rainy_Risk", "Cold_Wet_Risk"],
#     "wheat": ["Rainy_Risk"],
#     "default": ["Cold_Wet_Risk", "Rainy_Risk"]
# }

# RISK_DISPLAY = {
#     "Cold_Wet_Risk": "Fungal Blight (Late/Early)",
#     "Warm_Humid_Risk": "Bacterial Rot / Spot",
#     "Moderate_Dry_Risk": "Powdery Mildew",
#     "Rainy_Risk": "Rust / Scab / Leaf Spot",
#     "High_Heat_Risk": "Viral Infection / Mites",
#     "No_Risk": "None"
# }

# # --- ROBUST MODEL LOADING (Your Logic) ---
# try:
#     project_root = Path(__file__).resolve().parents[3] 
#     model_path = project_root / "ml" / "models" / "weather_risk_model.pkl"
#     risk_model = joblib.load(model_path) if model_path.exists() else None
#     if risk_model: print(f"✅ Risk Model Loaded: {model_path}")
#     else: print("⚠️ WARNING: Risk Model NOT found.")
# except Exception as e:
#     print(f"❌ Model Load Error: {e}")
#     risk_model = None

# # --- API ENDPOINT ---
# @router.get("/predict_outbreak")
# async def predict_disease_risk(
#     latitude: float = Query(..., description="Farm Lat"),
#     longitude: float = Query(..., description="Farm Long"),
#     crop_name: str = Query("tomato", description="Crop Name"),
#     farmer_phone: Optional[str] = Query(None, description="Phone for SMS Alert")
# ):
    


#    # 2. Satellite Logic (New Integration)
#     sat_report = get_satellite_health(latitude, longitude)

#     # 3. Hybrid Risk Logic (Macro + Micro)
#     env_prediction = risk_model.predict([[curr_temp, curr_humidity, is_raining]])[0] if risk_model else "No_Risk"
    
#     # Combined Alert Status
#     if env_prediction != "No_Risk" and sat_report['status'] == "High Stress":
#         final_risk = "CRITICAL (Weather + Satellite Warning)"
#     else:
#         final_risk = "STABLE"

    
         
# # async def predict_disease_risk(
# #     latitude: float = Query(..., description="Farm Lat"),
# #     longitude: float = Query(..., description="Farm Long"),
# #     crop_name: str = Query("tomato", description="Crop Name"),
# #     farmer_phone: Optional[str] = Query(None, description="Phone for SMS Alert") # ✅ PHONE FIXED: Optional String
# # ):
#     # A. Fetch Weather (Existing Code)
#     try:
#         url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_KEY}&units=metric"
#         resp = requests.get(url)
#         w_data = resp.json()
#         curr_temp = w_data['main']['temp']; curr_humidity = w_data['main']['humidity']; is_raining = 1 if 'rain' in w_data else 0 
#     except:
#         curr_temp = 25.0; curr_humidity = 60.0; is_raining = 0
        
#     # B. AI Prediction & Logic
#     env_prediction = risk_model.predict([[curr_temp, curr_humidity, is_raining]])[0] if risk_model else "No_Risk"
#     user_crop = crop_name.lower()
#     matched_key = "default";
#     for key in CROP_RISKS:
#         if key in user_crop: matched_key = key; break
#     vulnerable_diseases = CROP_RISKS[matched_key]
#     display_condition = RISK_DISPLAY.get(env_prediction, env_prediction)
    
#     alert_status = "SAFE"
#     sms_sent_status = False
    
#     if env_prediction in vulnerable_diseases:
#         alert_status = "HIGH RISK"
#         message = f"⚠️ ALERT: Current weather favors '{display_condition}' which attacks {user_crop}."
        
#         # 👇 SMS TRIGGER LOGIC
#         if farmer_phone:
#             sms_body = f"AgroGuard Alert: High risk of {display_condition} for your {user_crop} crop. Take preventive measures immediately."
#             send_sms(farmer_phone, sms_body)
#             sms_sent_status = True
            
#     elif env_prediction != "No_Risk":
#         alert_status = "MODERATE"
#         message = f"ℹ️ Note: Weather favors '{display_condition}', but {user_crop} is generally resistant."
#     else:
#         message = f"✅ Weather ({curr_temp}°C, {curr_humidity}%) is safe for {user_crop}."


#     return {
#         "weather_snapshot": { "temperature": f"{curr_temp}°C", "humidity": f"{curr_humidity}%" },
#         "ai_forecast": {
#             "environmental_condition": env_prediction,
#             "risk_level": alert_status,
#         },
#         "advisory": message,
#         "sms_alert": "Sent Successfully" if sms_sent_status else "Not Needed/No Phone"
#     }
# return {
#         "weather_snapshot": { "temperature": f"{curr_temp}°C", "humidity": f"{curr_humidity}%" },
#         "satellite_analysis": sat_report, # New Satellite Data
#         "ai_forecast": {
#             "environmental_condition": env_prediction,
#             "risk_level": final_risk,
#         },
#         "advisory": f"{sat_report['status']} detected via Satellite. {message}"
#     }

   


# from fastapi import APIRouter, Query
# import requests
# import joblib
# import numpy as np
# from pathlib import Path
# from ..config import get_settings
# # ✅ SMS Utility Import
# from ..utils.sms import send_sms

# router = APIRouter(tags=["Prediction Model (Environmental)"])
# OPENWEATHER_KEY = "025fd0f7a6731edd3dcbc40f7fc5ecdd"

# # --- 1. COMPLETE CROP MAPPING (51 Diseases Logic) ---
# CROP_RISKS = {
#     # Solanaceous
#     "tomato": ["Cold_Wet_Risk", "Warm_Humid_Risk", "High_Heat_Risk"],
#     "potato": ["Cold_Wet_Risk", "Early_Blight_Risk"],
#     "pepper": ["Warm_Humid_Risk"],
#     "capsicum": ["Warm_Humid_Risk"],
    
#     # Fruits
#     "apple": ["Rainy_Risk", "Moderate_Dry_Risk"],
#     "grape": ["Warm_Humid_Risk", "Rainy_Risk"],
#     "cherry": ["Moderate_Dry_Risk"],
#     "peach": ["Warm_Humid_Risk"],
#     "strawberry": ["Rainy_Risk"],
#     "orange": ["Warm_Humid_Risk"],
#     "blueberry": ["No_Risk"],
#     "raspberry": ["No_Risk"],
    
#     # Grains
#     "corn": ["Rainy_Risk", "Cold_Wet_Risk"],
#     "maize": ["Rainy_Risk", "Cold_Wet_Risk"],
#     "wheat": ["Rainy_Risk"],
#     "rice": ["Warm_Humid_Risk", "Rainy_Risk"],
    
#     # Veggies/Others
#     "soybean": ["No_Risk"],
#     "squash": ["Moderate_Dry_Risk"],
#     "pumpkin": ["Moderate_Dry_Risk"],
#     "cassava": ["Warm_Humid_Risk"],
#     "sugarcane": ["Rainy_Risk"],
    
#     # Fallback
#     "default": ["Cold_Wet_Risk", "Rainy_Risk"]
# }

# RISK_DISPLAY = {
#     "Cold_Wet_Risk": "Fungal Blight (Late/Early)",
#     "Warm_Humid_Risk": "Bacterial Rot / Spot",
#     "Moderate_Dry_Risk": "Powdery Mildew",
#     "Rainy_Risk": "Rust / Scab / Leaf Spot",
#     "High_Heat_Risk": "Viral Infection / Mites",
#     "No_Risk": "None"
# }

# # --- 2. ROBUST MODEL LOADING ---
# try:
#     # Find model path dynamically
#     current_file = Path(__file__).resolve()
#     # Go up to find 'ml' folder from 'backend/app/routers/risk.py'
#     # Root is usually 4 levels up depending on structure, let's try direct paths
#     project_root = current_file.parents[3] 
    
#     # List of possible locations to check
#     possible_paths = [
#         project_root / "ml" / "models" / "weather_risk_model.pkl",
#         Path("ml/models/weather_risk_model.pkl"),
#         Path("backend/ml/models/weather_risk_model.pkl")
#     ]
    
#     risk_model = None
#     for p in possible_paths:
#         if p.exists():
#             risk_model = joblib.load(p)
#             print(f"✅ Risk Model Loaded from: {p}")
#             break
            
#     if not risk_model:
#         print("⚠️ WARNING: Risk Model NOT found. Please run train_weather_model.py")

# except Exception as e:
#     print(f"❌ Model Load Error: {e}")
#     risk_model = None

# # --- 3. API ENDPOINT ---
# @router.get("/predict_outbreak")
# async def predict_disease_risk(
#     latitude: float = Query(..., description="Farm Lat"),
#     longitude: float = Query(..., description="Farm Long"),
#     crop_name: str = Query("tomato", description="Crop Name"),
#     farmer_phone: str = Query(None, description="Optional: Phone for SMS Alert")
# ):
#     """
#     Predicts disease risk based on live weather & trained ML model.
#     Triggers SMS if risk is HIGH.
#     """
#     # A. Fetch Live Weather
#     try:
#         url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_KEY}&units=metric"
#         resp = requests.get(url)
#         w_data = resp.json()
        
#         curr_temp = w_data['main']['temp']
#         curr_humidity = w_data['main']['humidity']
#         is_raining = 1 if 'rain' in w_data else 0 
#     except:
#         # Mock Data if API fails (Fail-safe)
#         curr_temp = 25.0; curr_humidity = 60.0; is_raining = 0

#     # B. AI Prediction
#     env_prediction = "No_Risk"
#     if risk_model:
#         env_prediction = risk_model.predict([[curr_temp, curr_humidity, is_raining]])[0]
    
#     # C. Logic: Match Environment with Crop Vulnerability
#     user_crop = crop_name.lower()
#     matched_key = "default"
    
#     # Partial string match logic (e.g. "bell pepper" matches "pepper")
#     for key in CROP_RISKS:
#         if key in user_crop:
#             matched_key = key
#             break
            
#     vulnerable_diseases = CROP_RISKS[matched_key]
#     display_condition = RISK_DISPLAY.get(env_prediction, env_prediction)
    
#     # D. Determine Alert Level
#     alert_status = "SAFE"
#     message = f"✅ Weather ({curr_temp}°C, {curr_humidity}%) is safe for {user_crop}."
#     sms_sent_status = False
    
#     if env_prediction in vulnerable_diseases:
#         # 🚨 HIGH RISK
#         alert_status = "HIGH RISK"
#         message = f"⚠️ ALERT: Current weather favors '{display_condition}' which attacks {user_crop}."
        
#         # 👇 TRIGGER SMS (Simulated)
#         if farmer_phone:
#             sms_body = f"AgroGuard ALERT: High risk of {display_condition} detected for your {user_crop} crop. Take preventive measures immediately."
#             send_sms(farmer_phone, sms_body)
#             sms_sent_status = True
            
#     elif env_prediction != "No_Risk":
#         # 🛡️ Moderate (Environment bad, but crop resistant)
#         alert_status = "MODERATE"
#         message = f"ℹ️ Note: Weather favors '{display_condition}', but {user_crop} is generally resistant."

#     return {
#         "weather_snapshot": {
#             "temperature": f"{curr_temp}°C",
#             "humidity": f"{curr_humidity}%",
#             "rain": "Yes" if is_raining else "No"
#         },
#         "ai_forecast": {
#             "environmental_condition": env_prediction,
#             "condition_name": display_condition,
#             "crop_analyzed": user_crop,
#             "risk_level": alert_status,
#         },
#         "advisory": message,
#         "sms_alert": "Sent Successfully" if sms_sent_status else "Not Needed/No Phone"
#     }


















# from fastapi import APIRouter, Query
# import requests
# import joblib
# import numpy as np
# from pathlib import Path
# from ..config import get_settings

# router = APIRouter(tags=["Prediction Model (Environmental)"])
# OPENWEATHER_KEY = "025fd0f7a6731edd3dcbc40f7fc5ecdd"

# # --- 1. MASTER MAPPING (Connecting 51 Diseases to Weather Models) ---
# CROP_RISKS = {
#     # Solanaceous (Nightshades)
#     "tomato": ["Cold_Wet_Risk", "Warm_Humid_Risk", "High_Heat_Risk"], # Blight, Bacterial, Virus
#     "potato": ["Cold_Wet_Risk"], # Late Blight
#     "pepper": ["Warm_Humid_Risk"], # Bacterial Spot
#     "capsicum": ["Warm_Humid_Risk"],

#     # Fruits
#     "apple": ["Rainy_Risk", "Moderate_Dry_Risk"], # Scab, Rust, Mildew
#     "grape": ["Warm_Humid_Risk", "Rainy_Risk"], # Black Rot, Measles
#     "cherry": ["Moderate_Dry_Risk"], # Powdery Mildew
#     "peach": ["Warm_Humid_Risk"], # Bacterial Spot
#     "strawberry": ["Rainy_Risk"], # Leaf Scorch
#     "orange": ["Warm_Humid_Risk"], # Citrus Greening
#     "blueberry": ["No_Risk"], # Generally hardy
#     "raspberry": ["No_Risk"],

#     # Grains
#     "corn": ["Rainy_Risk", "Cold_Wet_Risk"], # Rust, Leaf Blight
#     "maize": ["Rainy_Risk", "Cold_Wet_Risk"],
#     "wheat": ["Rainy_Risk"], # Rust
#     "rice": ["Warm_Humid_Risk", "Rainy_Risk"], # Blast, Bacterial Blight

#     # Vegetables/Others
#     "soybean": ["No_Risk"], # Generally hardy in dataset
#     "squash": ["Moderate_Dry_Risk"], # Powdery Mildew
#     "pumpkin": ["Moderate_Dry_Risk"],
#     "cassava": ["Warm_Humid_Risk"], # Bacterial Blight
#     "sugarcane": ["Rainy_Risk"], 

#     # Default Fallback
#     "default": ["Cold_Wet_Risk", "Rainy_Risk"]
# }

# # Display Names for User (Sundar dikhne ke liye)
# RISK_DISPLAY = {
#     "Cold_Wet_Risk": "Fungal Blight (Late/Early)",
#     "Warm_Humid_Risk": "Bacterial Rot / Spot",
#     "Moderate_Dry_Risk": "Powdery Mildew",
#     "Rainy_Risk": "Rust / Scab / Leaf Spot",
#     "High_Heat_Risk": "Viral Infection / Mites",
#     "No_Risk": "None"
# }

# # --- 2. LOAD MODEL ---
# # Try multiple paths to avoid "File Not Found" error
# possible_paths = [
#     Path("ml/models/weather_risk_model.pkl"),
#     Path("backend/ml/models/weather_risk_model.pkl"),
#     Path("models/weather_risk_model.pkl")
# ]

# risk_model = None
# for p in possible_paths:
#     if p.exists():
#         try:
#             risk_model = joblib.load(p)
#             print(f"✅ Loaded Risk Model from: {p}")
#             break
#         except: pass

# if not risk_model:
#     print("⚠️ WARNING: Risk Model not found. Run train_weather_model.py")

# # --- 3. API ENDPOINT ---
# @router.get("/predict_outbreak")
# async def predict_disease_risk(
#     latitude: float = Query(..., description="Farm Lat"),
#     longitude: float = Query(..., description="Farm Long"),
#     crop_name: str = Query("tomato", description="Crop Name")
# ):
#     """
#     Predicts if CURRENT weather matches the risk profile of YOUR crop.
#     """
#     # A. Fetch Weather
#     try:
#         url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_KEY}&units=metric"
#         resp = requests.get(url)
#         w_data = resp.json()
        
#         curr_temp = w_data['main']['temp']
#         curr_humidity = w_data['main']['humidity']
#         is_raining = 1 if 'rain' in w_data else 0 
#     except:
#         # Mock Data for Demo if API fails
#         curr_temp = 20.0; curr_humidity = 88.0; is_raining = 0

#     # B. AI Prediction
#     env_prediction = "No_Risk"
#     if risk_model:
#         # Predict Weather Condition Class
#         env_prediction = risk_model.predict([[curr_temp, curr_humidity, is_raining]])[0]
    
#     # C. Crop Safety Logic
#     user_crop = crop_name.lower()
    
#     # Find matching risk list (Partial match: "bell pepper" -> "pepper")
#     matched_key = "default"
#     for key in CROP_RISKS:
#         if key in user_crop:
#             matched_key = key
#             break
            
#     vulnerable_diseases = CROP_RISKS[matched_key]
#     display_condition = RISK_DISPLAY.get(env_prediction, env_prediction)
    
#     # D. Determine Alert Level
#     alert_status = "SAFE"
#     message = f"✅ Weather ({curr_temp}°C, {curr_humidity}%) is safe for {user_crop}."
    
#     if env_prediction in vulnerable_diseases:
#         # 🚨 DANGER: Weather matches Crop's Weakness
#         alert_status = "HIGH RISK"
#         message = f"⚠️ ALERT: Current weather favors '{display_condition}' which attacks {user_crop}."
    
#     elif env_prediction != "No_Risk":
#         # 🛡️ Weather is bad, but Crop is strong
#         alert_status = "MODERATE"
#         message = f"ℹ️ Note: Weather favors '{display_condition}', but {user_crop} is generally resistant."

#     return {
#         "weather_snapshot": {
#             "temperature": f"{curr_temp}°C",
#             "humidity": f"{curr_humidity}%",
#             "rain": "Yes" if is_raining else "No"
#         },
#         "ai_forecast": {
#             "environmental_condition": env_prediction,
#             "condition_name": display_condition,
#             "crop_analyzed": user_crop,
#             "risk_level": alert_status,
#         },
#         "advisory": message
#     }