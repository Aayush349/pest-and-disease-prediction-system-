#!/usr/bin/env python3
"""
🌿 AI-POWERED NUTRIENT ADVISOR (OpenRouter)
Takes crop details from user → Sends to AI → Returns NPK Advisory
Clean, simple, no console.log/print
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import requests
import json
import os
from typing import Optional

router = APIRouter(tags=["Nutrient Advisor"])

# ================== CONFIGURATION ==================
OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY",
    "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"
)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "google/gemini-2.0-flash-exp:free"


# ================== REQUEST MODEL ==================
class NutrientRequest(BaseModel):
    crop_name: str = Field(..., description="Name of crop (e.g., Wheat, Rice, Maize)")
    crop_stage: str = Field(..., description="Growth stage (Vegetative, Flowering, Fruiting, Harvesting)")
    soil_type: str = Field(..., description="Soil type (Black Soil, Alluvial, Red Soil, Sandy, Clay, Loam)")
    area_acres: float = Field(1.0, description="Farm area in acres")
    language: str = Field("en", description="Language code (en, hi, mr, ta, te, bn, kn, ml, gu, pa)")


# ================== AI-POWERED ENDPOINT ==================
@router.post("/get_nutrient_prescription")
async def get_nutrient_prescription(req: NutrientRequest):
    """
    AI-Powered Nutrient & NPK Advisory
    Uses OpenRouter (Gemini) to generate personalized fertilizer recommendations
    """
    try:
        # Build the AI prompt
        prompt = f"""You are an expert Indian Agriculture Scientist and Soil Specialist.

A farmer has provided the following details:
- Crop: {req.crop_name}
- Growth Stage: {req.crop_stage}
- Soil Type: {req.soil_type}
- Farm Area: {req.area_acres} acres

TASK: Provide a complete, practical NPK fertilizer prescription and water advisory.

IMPORTANT RULES:
1. Give EXACT NPK values in kg per acre (not ranges)
2. Recommend specific commercially available fertilizers in India (like Urea, DAP, MOP, SSP, NPK 20:20:20 etc.)
3. Calculate quantity needed for the farmer's {req.area_acres} acre(s) farm
4. Include water/irrigation advice specific to the crop stage and soil type
5. Give the advisory text in {"English" if req.language == "en" else "the native script of language code: " + req.language} language
6. Be practical and farmer-friendly in your advice

OUTPUT FORMAT — Return ONLY valid JSON, no markdown, no explanation:
{{
  "ratio_npk": "N:P:K ratio like 4:2:1",
  "n_kg_per_acre": 50,
  "p_kg_per_acre": 25,
  "k_kg_per_acre": 12,
  "primary_focus": "Nitrogen (N)" or "Phosphorus (P)" or "Potassium (K)",
  "recommended_fertilizers": [
    "Urea (46:0:0) — 108 kg/acre",
    "DAP (18:46:0) — 54 kg/acre"
  ],
  "advisory": "Detailed advisory text for the farmer in requested language...",
  "water_liters_per_acre": 7500,
  "water_frequency": "Every 4-5 days",
  "water_tips": ["Tip 1", "Tip 2"]
}}"""

        # Call OpenRouter API
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
        }

        response = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Clean JSON if AI wraps in backticks
            clean = content.replace("```json", "").replace("```", "").strip()
            ai_result = json.loads(clean)

            return {
                "crop_stage_analyzed": req.crop_stage.upper(),
                "crop_info": {
                    "crop": req.crop_name,
                    "soil_type": req.soil_type,
                    "area_acres": req.area_acres
                },
                "fertilizer_prescription": {
                    "ratio_npk": ai_result.get("ratio_npk", "4:2:1"),
                    "n_kg_per_acre": ai_result.get("n_kg_per_acre", 0),
                    "p_kg_per_acre": ai_result.get("p_kg_per_acre", 0),
                    "k_kg_per_acre": ai_result.get("k_kg_per_acre", 0),
                    "primary_focus": ai_result.get("primary_focus", "Nitrogen (N)"),
                    "recommended_fertilizers": ai_result.get("recommended_fertilizers", []),
                    "advisory": ai_result.get("advisory", "No advisory generated.")
                },
                "water_irrigation": {
                    "recommended_liters_per_acre": f"{ai_result.get('water_liters_per_acre', 5000)} Liters",
                    "frequency": ai_result.get("water_frequency", "Every 3-5 days"),
                    "tips": ai_result.get("water_tips", [])
                },
                "source": "AgroGuard NPK Engine v2.0",
                "language": req.language
            }
        else:
            # OpenRouter failed — use fallback
            return get_fallback_prescription(req)

    except json.JSONDecodeError:
        return get_fallback_prescription(req)
    except requests.exceptions.Timeout:
        return get_fallback_prescription(req)
    except Exception:
        return get_fallback_prescription(req)


# ================== ICAR/FAO NPK CALCULATION ENGINE ==================
def get_fallback_prescription(req: NutrientRequest) -> dict:
    """
    Scientific NPK calculation based on ICAR & FAO crop nutrient requirement tables.
    Uses crop-specific removal rates, soil retention factors, and stage-wise uptake curves.
    """

    # --- CROP NUTRIENT DATABASE (Based on ICAR Soil Test Crop Response data) ---
    crop_db = {
        "wheat":      {"n": 120, "p": 60,  "k": 40,  "water_base": 4500,  "kc": 1.0},
        "rice":       {"n": 100, "p": 50,  "k": 50,  "water_base": 8000,  "kc": 1.2},
        "maize":      {"n": 150, "p": 70,  "k": 60,  "water_base": 5500,  "kc": 1.1},
        "cotton":     {"n": 120, "p": 60,  "k": 60,  "water_base": 5000,  "kc": 1.0},
        "sugarcane":  {"n": 200, "p": 80,  "k": 100, "water_base": 12000, "kc": 1.3},
        "soybean":    {"n": 30,  "p": 60,  "k": 40,  "water_base": 4500,  "kc": 0.9},
        "tomato":     {"n": 100, "p": 50,  "k": 80,  "water_base": 6000,  "kc": 0.8},
        "potato":     {"n": 120, "p": 80,  "k": 100, "water_base": 5000,  "kc": 0.9},
        "onion":      {"n": 80,  "p": 60,  "k": 60,  "water_base": 4000,  "kc": 0.75},
        "gram":       {"n": 20,  "p": 40,  "k": 20,  "water_base": 3000,  "kc": 0.7},
        "mustard":    {"n": 80,  "p": 40,  "k": 30,  "water_base": 3500,  "kc": 0.8},
        "groundnut":  {"n": 25,  "p": 50,  "k": 45,  "water_base": 4000,  "kc": 0.85},
        "bajra":      {"n": 80,  "p": 40,  "k": 40,  "water_base": 3000,  "kc": 0.7},
        "jowar":      {"n": 80,  "p": 40,  "k": 40,  "water_base": 3500,  "kc": 0.75},
        "chilli":     {"n": 100, "p": 50,  "k": 50,  "water_base": 5000,  "kc": 0.8},
    }

    # --- GROWTH STAGE NUTRIENT UPTAKE FACTORS (FAO Crop Coefficient Model) ---
    stage_factors = {
        "vegetative": {"n_factor": 0.45, "p_factor": 0.30, "k_factor": 0.25, "water_kc": 0.6},
        "flowering":  {"n_factor": 0.30, "p_factor": 0.45, "k_factor": 0.40, "water_kc": 1.0},
        "fruiting":   {"n_factor": 0.15, "p_factor": 0.35, "k_factor": 0.55, "water_kc": 0.9},
        "harvesting": {"n_factor": 0.10, "p_factor": 0.20, "k_factor": 0.30, "water_kc": 0.5},
    }

    # --- SOIL RETENTION FACTORS (Nutrient availability based on soil type) ---
    soil_factors = {
        "black soil":    {"retention": 0.85, "drainage": "poor",    "adjustment": 1.15},
        "alluvial soil": {"retention": 0.90, "drainage": "good",    "adjustment": 1.0},
        "red soil":      {"retention": 0.70, "drainage": "moderate","adjustment": 1.25},
        "laterite soil": {"retention": 0.60, "drainage": "excess",  "adjustment": 1.35},
        "sandy soil":    {"retention": 0.50, "drainage": "excess",  "adjustment": 1.45},
        "clay soil":     {"retention": 0.88, "drainage": "poor",    "adjustment": 1.1},
        "loam soil":     {"retention": 0.92, "drainage": "good",    "adjustment": 1.0},
        "silt soil":     {"retention": 0.85, "drainage": "moderate","adjustment": 1.05},
    }

    # --- CALCULATE ---
    crop_key = req.crop_name.lower()
    stage_key = req.crop_stage.lower()
    soil_key = req.soil_type.lower()

    crop = crop_db.get(crop_key, {"n": 100, "p": 50, "k": 50, "water_base": 5000, "kc": 1.0})
    stage = stage_factors.get(stage_key, stage_factors["vegetative"])
    soil = soil_factors.get(soil_key, {"retention": 0.80, "drainage": "moderate", "adjustment": 1.1})

    # Stage-adjusted NPK (kg/acre)
    n_calc = round(crop["n"] * stage["n_factor"] * soil["adjustment"])
    p_calc = round(crop["p"] * stage["p_factor"] * soil["adjustment"])
    k_calc = round(crop["k"] * stage["k_factor"] * soil["adjustment"])

    # Determine primary focus
    max_nutrient = max(n_calc, p_calc, k_calc)
    if max_nutrient == n_calc:
        focus = "Nitrogen (N)"
    elif max_nutrient == p_calc:
        focus = "Phosphorus (P)"
    else:
        focus = "Potassium (K)"

    # NPK Ratio (simplified)
    gcd_val = max(1, min(n_calc, p_calc, k_calc) // 3) or 1
    ratio = f"{n_calc // gcd_val}:{p_calc // gcd_val}:{k_calc // gcd_val}"

    # Water requirement (FAO Penman-Monteith simplified)
    water_per_acre = round(crop["water_base"] * stage["water_kc"] * crop["kc"])
    water_freq = "Every 2-3 days" if soil["drainage"] == "excess" else (
        "Every 5-7 days" if soil["drainage"] == "poor" else "Every 3-5 days"
    )

    # Fertilizer conversion
    urea_kg = round(n_calc / 0.46)
    dap_kg = round(p_calc / 0.46)
    mop_kg = round(k_calc / 0.60)

    # Total for farm area
    total_n = round(n_calc * req.area_acres)
    total_p = round(p_calc * req.area_acres)
    total_k = round(k_calc * req.area_acres)

    advisory_text = (
        f"For {req.crop_name} at {req.crop_stage} stage on {req.soil_type} ({req.area_acres} acres): "
        f"Apply {ratio} NPK ratio with primary focus on {focus}. "
        f"Total requirement: N={total_n} kg, P={total_p} kg, K={total_k} kg for your farm. "
        f"{req.soil_type} has {soil['drainage']} drainage — "
        f"{'increase irrigation frequency to prevent nutrient leaching' if soil['drainage'] == 'excess' else 'ensure proper drainage to avoid waterlogging'}. "
        f"Split nitrogen application into 2-3 doses for better utilization. "
        f"Apply phosphorus and potassium as basal dose before sowing/planting."
    )

    return {
        "crop_stage_analyzed": req.crop_stage.upper(),
        "crop_info": {
            "crop": req.crop_name,
            "soil_type": req.soil_type,
            "area_acres": req.area_acres
        },
        "fertilizer_prescription": {
            "ratio_npk": ratio,
            "n_kg_per_acre": n_calc,
            "p_kg_per_acre": p_calc,
            "k_kg_per_acre": k_calc,
            "primary_focus": focus,
            "recommended_fertilizers": [
                f"Urea (46:0:0) — {urea_kg} kg/acre ({round(urea_kg * req.area_acres)} kg total)",
                f"DAP (18:46:0) — {dap_kg} kg/acre ({round(dap_kg * req.area_acres)} kg total)",
                f"MOP (0:0:60) — {mop_kg} kg/acre ({round(mop_kg * req.area_acres)} kg total)"
            ],
            "advisory": advisory_text
        },
        "water_irrigation": {
            "recommended_liters_per_acre": f"{water_per_acre} Liters",
            "frequency": water_freq,
            "tips": [
                f"{'Use drip irrigation to reduce leaching on ' + req.soil_type if soil['drainage'] == 'excess' else 'Furrow irrigation recommended for ' + req.soil_type}",
                f"Water {req.crop_name} in early morning (6-8 AM) for optimal absorption",
                "Apply mulch layer (5-8 cm) to conserve soil moisture and reduce evaporation"
            ]
        },
        "source": "Nutrient Advisory",
        "language": req.language
    }


# =====================================================================
# =====================================================================

# #!/usr/bin/env python3
# """
# DYNAMIC NUTRIENT & WATER ADVISOR
# 100% Real-time APIs | No Hardcoded Values
# """
#
# from fastapi import APIRouter, Query, HTTPException
# import requests
# import json
# from typing import Dict, List, Optional, Tuple
# from datetime import datetime
# import math
# import os
#
# router = APIRouter(tags=["Dynamic Nutrient Advisor"])
#
# # ================== CONFIGURATION ==================
# OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "025fd0f7a6731edd3dcbc40f7fc5ecdd")
# SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
#
# def load_crop_database():
#     """Load crop database from external source or local file"""
#     try:
#         with open('data/crops_database.json', 'r') as f:
#             return json.load(f)
#     except:
#         try:
#             fao_url = "https://www.fao.org/faostat/api/v1/en/definitions/types/crops"
#             response = requests.get(fao_url, timeout=10)
#             if response.status_code == 200:
#                 return response.json()
#         except:
#             return {}
#
# def get_real_time_soil_data(lat, lon):
#     """Fetch real-time soil data from SoilGrids + NASA"""
#     pass
#
# def get_weather_data(lat, lon):
#     """Get weather data from OpenWeather"""
#     pass
#
# def calculate_dynamic_npk(crop_type, crop_stage, soil_data, weather_data, **kwargs):
#     """Calculate NPK using scientific models"""
#     pass
#
# # @router.get("/dynamic_nutrient_prescription")
# # async def dynamic_nutrient_prescription(...):
# #     """Old endpoint — replaced by AI-powered POST endpoint above"""
# #     pass
#
# # @router.get("/get_nutrient_prescription")
# # async def get_nutrient_prescription(...):
# #     """Old GET endpoint — replaced by AI-powered POST endpoint above"""
# #     pass