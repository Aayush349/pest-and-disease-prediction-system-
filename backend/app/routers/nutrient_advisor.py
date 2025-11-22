from fastapi import APIRouter, Query
import requests
from datetime import datetime, timedelta
# 👇 NEW: Import translator utility (Assuming it's available in ml/)
from ..ml.translator import translate_response 

router = APIRouter(tags=["Nutrient & Water Advisor"])
OPENWEATHER_KEY = "025fd0f7a6731edd3dcbc40f7fc5ecdd"

# 🧠 SCIENTIFIC NPK & WATER RULES (Same as before)
NUTRIENT_GUIDELINES = {
    "vegetative": {"water_Liters_per_acre": 5000, "N_ratio": 3, "K_ratio": 1},
    "flowering": {"water_Liters_per_acre": 7500, "N_ratio": 1, "K_ratio": 2},
    "fruiting": {"water_Liters_per_acre": 9000, "N_ratio": 1, "K_ratio": 3},
    "default": {"water_Liters_per_acre": 6000, "N_ratio": 2, "K_ratio": 1}
}

@router.get("/get_nutrient_prescription")
async def get_nutrient_prescription(
    crop_stage: str = Query(..., description="Current crop stage (e.g., flowering)"),
    latitude: float = Query(..., description="Farm Lat"),
    longitude: float = Query(..., description="Farm Long"),
    language: str = Query("en", description="Target Language Code (e.g., hi, ta)") # 👈 ADDED LANGUAGE
):
    """
    Provides exact NPK and Water quantity based on environmental factors and crop stage.
    """
    stage = crop_stage.lower()
    guideline = NUTRIENT_GUIDELINES.get(stage, NUTRIENT_GUIDELINES['default'])
    
    # 1. Fetch Real-Time Weather
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_KEY}&units=metric"
        resp = requests.get(url).json()
        curr_humidity = resp['main']['humidity']
        curr_temp = resp['main']['temp']
    except:
        curr_humidity = 60
        curr_temp = 25
    
    # 2. Water Adjustment Logic
    water_demand_factor = 1.0
    if curr_temp > 30 and curr_humidity < 50:
        water_demand_factor = 1.3
    elif curr_humidity > 90 and curr_temp < 20:
        water_demand_factor = 0.7

    final_water = round(guideline['water_Liters_per_acre'] * water_demand_factor, 0)
    
    # 3. Final English Advisory Message
    english_advisory = f"Maintain the {guideline['N_ratio']}:{guideline['N_ratio']}:{guideline['K_ratio']} ratio for optimal {stage} growth. Correct nutrient balance prevents diseases."
    
    # 4. TRANSLATION STEP
    if language != 'en':
        final_advisory_message = translate_response(english_advisory, language)
    else:
        final_advisory_message = english_advisory
    
    # 5. Final Prescription
    return {
        "crop_stage_analyzed": stage.upper(),
        "environmental_impact": {
            "temp": f"{curr_temp}°C",
            "humidity": f"{curr_humidity}%",
        },
        "fertilizer_prescription": {
            "ratio_npk": f"{guideline['N_ratio']}:{guideline['N_ratio']}:{guideline['K_ratio']}",
            "primary_focus": "Potassium (K)" if guideline['K_ratio'] > guideline['N_ratio'] else "Nitrogen (N)",
            "advisory": final_advisory_message # 👈 Translated
        },
        "water_irrigation": {
            "recommended_liters_per_acre": f"{final_water} Liters",
            "reason": f"Adjusted for current weather conditions ({water_demand_factor:.1f}x multiplier applied)."
        },
        "language_used": language # 👈 New field
    }



# from fastapi import APIRouter, Query
# import requests
# from datetime import datetime, timedelta

# router = APIRouter(tags=["Nutrient & Water Advisor"])
# OPENWEATHER_KEY = "025fd0f7a6731edd3dcbc40f7fc5ecdd" # Your OpenWeather Key

# # 🧠 SCIENTIFIC NPK & WATER RULES
# NUTRIENT_GUIDELINES = {
#     "vegetative": {"water_Liters_per_acre": 5000, "N_ratio": 3, "K_ratio": 1}, # Growth stage, needs high Nitrogen (N)
#     "flowering": {"water_Liters_per_acre": 7500, "N_ratio": 1, "K_ratio": 2}, # Needs high Potassium (K)
#     "fruiting": {"water_Liters_per_acre": 9000, "N_ratio": 1, "K_ratio": 3},  # Highest water/potassium demand
#     "default": {"water_Liters_per_acre": 6000, "N_ratio": 2, "K_ratio": 1}
# }

# @router.get("/get_nutrient_prescription")
# async def get_nutrient_prescription(
#     crop_stage: str = Query(..., description="Current crop stage (e.g., flowering)"),
#     latitude: float = Query(..., description="Farm Lat"),
#     longitude: float = Query(..., description="Farm Long")
# ):
#     """
#     Provides exact NPK and Water quantity based on environmental factors and crop stage.
#     """
#     stage = crop_stage.lower()
#     guideline = NUTRIENT_GUIDELINES.get(stage, NUTRIENT_GUIDELINES['default'])
    
#     # 1. Fetch Real-Time Weather for water loss calculation
#     try:
#         url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_KEY}&units=metric"
#         resp = requests.get(url).json()
#         curr_humidity = resp['main']['humidity']
#         curr_temp = resp['main']['temp']
#     except:
#         curr_humidity = 60
#         curr_temp = 25
    
#     # 2. Water Adjustment (Environmental Condition Logic)
#     water_demand_factor = 1.0
#     if curr_temp > 30 and curr_humidity < 50:
#         water_demand_factor = 1.3  # Hot & Dry -> Needs 30% more water
#     elif curr_humidity > 90 and curr_temp < 20:
#         water_demand_factor = 0.7  # Cool & Wet (Fungus Risk) -> Needs 30% less water
    
#     final_water = round(guideline['water_Liters_per_acre'] * water_demand_factor, 0)
    
#     # 3. Final Prescription
#     return {
#         "crop_stage_analyzed": stage.upper(),
#         "environmental_impact": {
#             "temp": f"{curr_temp}°C",
#             "humidity": f"{curr_humidity}%",
#         },
#         "fertilizer_prescription": {
#             "ratio_npk": f"{guideline['N_ratio']}:{guideline['N_ratio']}:{guideline['K_ratio']}",
#             "primary_focus": "Potassium (K)" if guideline['K_ratio'] > guideline['N_ratio'] else "Nitrogen (N)",
#             "advisory": f"Maintain the {guideline['N_ratio']}:{guideline['N_ratio']}:{guideline['K_ratio']} ratio for optimal {stage} growth. Correct nutrient balance prevents diseases."
#         },
#         "water_irrigation": {
#             "recommended_liters_per_acre": f"{final_water} Liters",
#             "reason": f"Adjusted for current weather conditions ({water_demand_factor:.1f}x multiplier applied)."
#         }
#     }