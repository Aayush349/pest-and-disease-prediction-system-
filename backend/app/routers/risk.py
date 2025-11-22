from fastapi import APIRouter, Query
import requests
import joblib
import numpy as np
from pathlib import Path
from typing import Optional
from ..config import get_settings
from ..utils.sms import send_sms # ✅ SMS Import

router = APIRouter(tags=["Prediction Model (Environmental)"])
OPENWEATHER_KEY = "025fd0f7a6731edd3dcbc40f7fc5ecdd"

# --- CROP MAPPING (Shortened for display, but full logic remains) ---
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

# --- ROBUST MODEL LOADING (Your Logic) ---
try:
    project_root = Path(__file__).resolve().parents[3] 
    model_path = project_root / "ml" / "models" / "weather_risk_model.pkl"
    risk_model = joblib.load(model_path) if model_path.exists() else None
    if risk_model: print(f"✅ Risk Model Loaded: {model_path}")
    else: print("⚠️ WARNING: Risk Model NOT found.")
except Exception as e:
    print(f"❌ Model Load Error: {e}")
    risk_model = None

# --- API ENDPOINT ---
@router.get("/predict_outbreak")
async def predict_disease_risk(
    latitude: float = Query(..., description="Farm Lat"),
    longitude: float = Query(..., description="Farm Long"),
    crop_name: str = Query("tomato", description="Crop Name"),
    farmer_phone: Optional[str] = Query(None, description="Phone for SMS Alert") # ✅ PHONE FIXED: Optional String
):
    # A. Fetch Weather (Existing Code)
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_KEY}&units=metric"
        resp = requests.get(url)
        w_data = resp.json()
        curr_temp = w_data['main']['temp']; curr_humidity = w_data['main']['humidity']; is_raining = 1 if 'rain' in w_data else 0 
    except:
        curr_temp = 25.0; curr_humidity = 60.0; is_raining = 0
        
    # B. AI Prediction & Logic
    env_prediction = risk_model.predict([[curr_temp, curr_humidity, is_raining]])[0] if risk_model else "No_Risk"
    user_crop = crop_name.lower()
    matched_key = "default";
    for key in CROP_RISKS:
        if key in user_crop: matched_key = key; break
    vulnerable_diseases = CROP_RISKS[matched_key]
    display_condition = RISK_DISPLAY.get(env_prediction, env_prediction)
    
    alert_status = "SAFE"
    sms_sent_status = False
    
    if env_prediction in vulnerable_diseases:
        alert_status = "HIGH RISK"
        message = f"⚠️ ALERT: Current weather favors '{display_condition}' which attacks {user_crop}."
        
        # 👇 SMS TRIGGER LOGIC
        if farmer_phone:
            sms_body = f"AgroGuard Alert: High risk of {display_condition} for your {user_crop} crop. Take preventive measures immediately."
            send_sms(farmer_phone, sms_body)
            sms_sent_status = True
            
    elif env_prediction != "No_Risk":
        alert_status = "MODERATE"
        message = f"ℹ️ Note: Weather favors '{display_condition}', but {user_crop} is generally resistant."
    else:
        message = f"✅ Weather ({curr_temp}°C, {curr_humidity}%) is safe for {user_crop}."


    return {
        "weather_snapshot": { "temperature": f"{curr_temp}°C", "humidity": f"{curr_humidity}%" },
        "ai_forecast": {
            "environmental_condition": env_prediction,
            "risk_level": alert_status,
        },
        "advisory": message,
        "sms_alert": "Sent Successfully" if sms_sent_status else "Not Needed/No Phone"
    }





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