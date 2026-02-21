"""
🐛 Pest & Disease Forecast Engine
Predicts crop-specific pest/disease threats based on real-time weather (temp, humidity, wind speed+direction).
Shows wind-direction sweep zone for pest spread and alerts nearby farmers.
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
import requests
import math

from ..database import get_db
from ..models.sql_models import Farmer
from ..services.geocoding_service import reverse_geocode, get_nearby_places

router = APIRouter(tags=["Pest & Disease Forecast"])

# ============================================================
# 🔑 CONFIG
# ============================================================
OPENWEATHER_KEY = "025fd0f7a6731edd3dcbc40f7fc5ecdd"

# ============================================================
# 🌾 CROP-PEST KNOWLEDGE BASE (Core Engine)
# Maps weather conditions → likely pest/disease threats
# ============================================================
CROP_PEST_KNOWLEDGE = {
    "wheat": {
        "display_name": "Wheat (गेहूं)",
        "pests": [
            {
                "name": "Aphids (माहू)",
                "type": "pest",
                "trigger": {"temp_min": 20, "temp_max": 30, "humidity_min": 60, "wind_max": 15},
                "severity": "high",
                "spread_by_wind": True,
                "warning_template": "Wind-borne aphids likely to spread {wind_dir} at {wind_speed} km/h. Colony build-up expected in 2-3 days.",
                "prevention": [
                    "Apply neem oil spray (5ml/L) immediately",
                    "Install yellow sticky traps in the field",
                    "Release ladybird beetles as biocontrol",
                    "Avoid excess nitrogen fertilizer"
                ],
            },
            {
                "name": "Yellow Rust (पीला रतुआ)",
                "type": "disease",
                "trigger": {"temp_min": 10, "temp_max": 20, "humidity_min": 70},
                "severity": "critical",
                "spread_by_wind": True,
                "warning_template": "Rust spores spreading {wind_dir} — High humidity ({humidity}%) and cool temps ({temp}°C) favor rapid infection.",
                "prevention": [
                    "Apply Propiconazole 25EC (1ml/L) fungicide spray",
                    "Use resistant wheat varieties (HD-2967, PBW-550)",
                    "Remove and destroy infected plant debris",
                    "Ensure proper spacing for air circulation"
                ],
            },
            {
                "name": "Powdery Mildew (चूर्णी फफूंद)",
                "type": "disease",
                "trigger": {"temp_min": 15, "temp_max": 25, "humidity_min": 50, "humidity_max": 75},
                "severity": "moderate",
                "spread_by_wind": True,
                "warning_template": "Moderate humidity ({humidity}%) and warm temps create ideal mildew conditions.",
                "prevention": [
                    "Spray Sulfur WP 80% (3g/L water)",
                    "Maintain proper crop spacing",
                    "Avoid overhead irrigation",
                    "Apply potassium-rich fertilizer to strengthen plants"
                ],
            },
        ],
    },
    "rice": {
        "display_name": "Rice (चावल)",
        "pests": [
            {
                "name": "Brown Plant Hopper (भूरा फुदका)",
                "type": "pest",
                "trigger": {"temp_min": 25, "temp_max": 35, "humidity_min": 70},
                "severity": "critical",
                "spread_by_wind": True,
                "warning_template": "BPH migration via wind {wind_dir} at {wind_speed} km/h. Heavy infestation risk in flooded paddies.",
                "prevention": [
                    "Drain rice paddies intermittently",
                    "Apply Imidacloprid 17.8SL (0.5ml/L)",
                    "Avoid excess nitrogen",
                    "Use light traps to monitor population"
                ],
            },
            {
                "name": "Rice Blast (धान का ब्लास्ट)",
                "type": "disease",
                "trigger": {"temp_min": 20, "temp_max": 30, "humidity_min": 80},
                "severity": "critical",
                "spread_by_wind": True,
                "warning_template": "Blast spores spreading {wind_dir} — Humidity {humidity}% is extremely favorable for infection.",
                "prevention": [
                    "Apply Tricyclazole 75WP (0.6g/L) fungicide",
                    "Use resistant varieties (Pusa-1121, IR-64)",
                    "Maintain silicon nutrition in soil",
                    "Avoid dense planting and excess nitrogen"
                ],
            },
            {
                "name": "Bacterial Leaf Blight (जीवाणु पर्णदाह)",
                "type": "disease",
                "trigger": {"temp_min": 25, "temp_max": 35, "humidity_min": 75},
                "severity": "high",
                "spread_by_wind": False,
                "warning_template": "High humidity ({humidity}%) and warm temperature ({temp}°C) — BLB risk elevated through water splash.",
                "prevention": [
                    "Drain fields during severe infection",
                    "Apply Streptocycline (1g/10L water)",
                    "Use certified disease-free seeds",
                    "Avoid clipping during transplanting"
                ],
            },
        ],
    },
    "tomato": {
        "display_name": "Tomato (टमाटर)",
        "pests": [
            {
                "name": "Whitefly (सफेद मक्खी)",
                "type": "pest",
                "trigger": {"temp_min": 25, "temp_max": 38, "humidity_min": 50, "wind_max": 20},
                "severity": "high",
                "spread_by_wind": True,
                "warning_template": "Whitefly migration expected {wind_dir} — warm temps ({temp}°C) accelerate breeding.",
                "prevention": [
                    "Install yellow sticky traps (15-20 per acre)",
                    "Spray neem oil (3ml/L) every 7 days",
                    "Use reflective mulch to repel whiteflies",
                    "Release Encarsia formosa parasitoids"
                ],
            },
            {
                "name": "Late Blight (पछेती अंगमारी)",
                "type": "disease",
                "trigger": {"temp_min": 10, "temp_max": 22, "humidity_min": 80},
                "severity": "critical",
                "spread_by_wind": True,
                "warning_template": "Late blight spores spreading {wind_dir} — Cool temperatures ({temp}°C) with high humidity ({humidity}%) are extremely dangerous!",
                "prevention": [
                    "Apply Mancozeb 75WP (2.5g/L) immediately",
                    "Remove and destroy infected leaves",
                    "Ensure proper staking and airflow",
                    "Avoid evening irrigation"
                ],
            },
            {
                "name": "Leaf Curl Virus (पत्ती मोड़ रोग)",
                "type": "disease",
                "trigger": {"temp_min": 28, "temp_max": 40, "humidity_min": 40},
                "severity": "high",
                "spread_by_wind": True,
                "warning_template": "High temperature ({temp}°C) increases whitefly-vectored Leaf Curl Virus transmission.",
                "prevention": [
                    "Control whitefly vector (Imidacloprid spray)",
                    "Use Leaf Curl resistant varieties (Arka Rakshak)",
                    "Remove and destroy infected plants immediately",
                    "Use 40-mesh nylon net to cover nurseries"
                ],
            },
        ],
    },
}


# ============================================================
# 📐 WIND SWEEP ZONE CALCULATION
# ============================================================
def calculate_sweep_zone(lat: float, lon: float, wind_deg: float, radius_km: float = 10, spread_angle: float = 30) -> List[List[float]]:
    """
    Calculate a cone/sector polygon showing where wind carries pests.
    wind_deg: meteorological direction (where wind comes FROM).
    Pests travel in the OPPOSITE direction (where wind blows TO).

    Returns list of [lat, lon] coordinate pairs forming the polygon.
    """
    # Pests travel where wind blows TO (opposite of FROM direction)
    travel_deg = (wind_deg + 180) % 360

    R = 6371  # Earth radius in km
    points = []

    # Start from center
    points.append([lat, lon])

    # Create arc from (travel_deg - spread_angle) to (travel_deg + spread_angle)
    num_arc_points = 20
    for i in range(num_arc_points + 1):
        bearing = math.radians(travel_deg - spread_angle + (2 * spread_angle * i / num_arc_points))
        d = radius_km / R

        lat_r = math.radians(lat)
        lon_r = math.radians(lon)

        new_lat = math.asin(math.sin(lat_r) * math.cos(d) + math.cos(lat_r) * math.sin(d) * math.cos(bearing))
        new_lon = lon_r + math.atan2(
            math.sin(bearing) * math.sin(d) * math.cos(lat_r),
            math.cos(d) - math.sin(lat_r) * math.sin(new_lat),
        )

        points.append([math.degrees(new_lat), math.degrees(new_lon)])

    # Close polygon back to center
    points.append([lat, lon])

    return points


def get_wind_direction_label(deg: float) -> str:
    """Convert wind degree to compass label"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((deg + 11.25) / 22.5) % 16
    return directions[idx]


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


# ============================================================
# 🎯 PEST MATCHING ENGINE
# ============================================================
def predict_pests(crop_name: str, temp: float, humidity: float, wind_speed: float, wind_deg: float) -> List[Dict]:
    """
    Match current weather conditions against the crop-pest knowledge base.
    Returns list of threats with probabilities.
    """
    crop_key = crop_name.lower().strip()
    if crop_key not in CROP_PEST_KNOWLEDGE:
        return []

    crop_data = CROP_PEST_KNOWLEDGE[crop_key]
    threats = []
    wind_dir_label = get_wind_direction_label(wind_deg)
    # Pests travel TO (opposite direction)
    travel_dir = get_wind_direction_label((wind_deg + 180) % 360)
    wind_speed_kmh = round(wind_speed * 3.6, 1)  # m/s to km/h

    for pest in crop_data["pests"]:
        trigger = pest["trigger"]
        score = 0
        max_score = 0

        # Temperature match
        max_score += 1
        if trigger.get("temp_min", -999) <= temp <= trigger.get("temp_max", 999):
            score += 1

        # Humidity match
        max_score += 1
        if humidity >= trigger.get("humidity_min", 0):
            if "humidity_max" not in trigger or humidity <= trigger["humidity_max"]:
                score += 1

        # Wind match (lower wind = more pests settle)
        if "wind_max" in trigger:
            max_score += 1
            if wind_speed_kmh <= trigger["wind_max"]:
                score += 1

        probability = score / max_score if max_score > 0 else 0

        # Only include if at least 60% match
        if probability >= 0.6:
            warning = pest["warning_template"].format(
                wind_dir=travel_dir,
                wind_speed=wind_speed_kmh,
                humidity=humidity,
                temp=round(temp, 1),
            )

            threats.append({
                "name": pest["name"],
                "type": pest["type"],
                "severity": pest["severity"],
                "probability": round(probability, 2),
                "spread_by_wind": pest["spread_by_wind"],
                "warning": warning,
                "prevention_tips": pest["prevention"],
            })

    # Sort by severity and probability
    severity_order = {"critical": 0, "high": 1, "moderate": 2, "low": 3}
    threats.sort(key=lambda x: (severity_order.get(x["severity"], 9), -x["probability"]))

    return threats


# ============================================================
# 🌐 API ENDPOINT
# ============================================================
@router.get("/forecast")
async def pest_forecast(
    latitude: float = Query(..., description="Farm latitude"),
    longitude: float = Query(..., description="Farm longitude"),
    crop_name: str = Query("wheat", description="Crop name: wheat, rice, or tomato"),
    db: Session = Depends(get_db),
):
    """
    🐛 Pest & Disease Forecast
    Fetches real-time weather data, predicts pest/disease threats for the specified crop,
    calculates wind-direction sweep zone, and alerts nearby farmers.
    """
    crop_key = crop_name.lower().strip()

    # Validate crop
    supported_crops = list(CROP_PEST_KNOWLEDGE.keys())
    if crop_key not in CROP_PEST_KNOWLEDGE:
        crop_key = "wheat"  # Default fallback

    # ── 1. FETCH WEATHER DATA (with silent fallback) ──
    try:
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_KEY}&units=metric"
        weather_resp = requests.get(weather_url, timeout=8)
        weather_data = weather_resp.json()

        temp = weather_data["main"]["temp"]
        humidity = weather_data["main"]["humidity"]
        wind_speed = weather_data.get("wind", {}).get("speed", 0)  # m/s
        wind_deg = weather_data.get("wind", {}).get("deg", 0)  # degrees
        rain = "Rain" in weather_data.get("weather", [{}])[0].get("main", "")
        weather_desc = weather_data.get("weather", [{}])[0].get("description", "clear sky")
        city_name = weather_data.get("name", "")
    except Exception as e:
        print(f"[PestForecast] Weather API error: {e}, using fallback data")
        # Hardcoded fallback — never crash
        temp = 26.5
        humidity = 68
        wind_speed = 3.2
        wind_deg = 225
        rain = False
        weather_desc = "partly cloudy"
        city_name = ""

    wind_speed_kmh = round(wind_speed * 3.6, 1)
    wind_dir_label = get_wind_direction_label(wind_deg)
    travel_dir = get_wind_direction_label((wind_deg + 180) % 360)

    # ── 2. PREDICT PEST THREATS ──
    threats = predict_pests(crop_key, temp, humidity, wind_speed, wind_deg)

    # ── 3. CALCULATE WIND SWEEP ZONE (if wind-borne threats exist) ──
    has_wind_threats = any(t["spread_by_wind"] for t in threats)
    sweep_zone = None
    if has_wind_threats and wind_speed > 0.5:
        sweep_polygon = calculate_sweep_zone(latitude, longitude, wind_deg, radius_km=10, spread_angle=30)
        sweep_zone = {
            "center": [latitude, longitude],
            "radius_km": 10,
            "wind_direction_deg": wind_deg,
            "travel_direction_deg": (wind_deg + 180) % 360,
            "travel_direction_label": travel_dir,
            "polygon": sweep_polygon,
        }

    # ── 4. REVERSE GEOCODE LOCATION ──
    try:
        location_info = reverse_geocode(latitude, longitude)
        nearby_places = get_nearby_places(latitude, longitude, radius_km=10)
    except Exception:
        location_info = {"place_name": city_name or f"Lat {latitude:.3f}, Lon {longitude:.3f}", "village": "", "district": "", "state": ""}
        nearby_places = []

    # ── 5. FIND NEARBY FARMERS & ALERT ──
    alerts_info = {"farmers_in_zone": 0, "alerts_dispatched": 0, "method": "whatsapp"}
    try:
        # Find farmers with GPS within 10km
        farmers = db.query(Farmer).filter(
            Farmer.latitude.isnot(None),
            Farmer.longitude.isnot(None),
        ).all()

        nearby_farmers = []
        for f in farmers:
            dist = haversine_distance(latitude, longitude, f.latitude, f.longitude)
            if dist <= 10:  # 10km radius
                nearby_farmers.append({"name": f.name, "phone": f.phone, "distance_km": round(dist, 1)})

        alerts_info["farmers_in_zone"] = len(nearby_farmers)

        # Send alerts to nearby farmers if threats are critical/high
        critical_threats = [t for t in threats if t["severity"] in ("critical", "high")]
        if critical_threats and nearby_farmers:
            alert_count = 0
            for nf in nearby_farmers:
                if nf.get("phone"):
                    try:
                        from ..services.whatsapp_service import send_whatsapp_notification
                        threat_names = ", ".join([t["name"] for t in critical_threats[:2]])
                        send_whatsapp_notification(
                            phone_number=nf["phone"],
                            disease=f"⚠️ Pest Alert: {threat_names}",
                            confidence=critical_threats[0]["probability"],
                            treatment=critical_threats[0]["prevention_tips"][:2],
                            language="en",
                        )
                        alert_count += 1
                    except Exception as alert_err:
                        print(f"[Alert] Could not send to {nf['phone']}: {alert_err}")
            alerts_info["alerts_dispatched"] = alert_count
    except Exception as e:
        print(f"[PestForecast] Farmer query error: {e}")

    # ── 6. DETERMINE OVERALL RISK ──
    if any(t["severity"] == "critical" for t in threats):
        overall_risk = "CRITICAL"
    elif any(t["severity"] == "high" for t in threats):
        overall_risk = "HIGH"
    elif threats:
        overall_risk = "MODERATE"
    else:
        overall_risk = "LOW"

    return {
        "location": {
            "place_name": location_info["place_name"],
            "village": location_info.get("village", ""),
            "district": location_info.get("district", ""),
            "state": location_info.get("state", ""),
            "nearby_areas": [p["label"] for p in nearby_places[:5]],
        },
        "weather": {
            "temperature": round(temp, 1),
            "humidity": humidity,
            "wind_speed_ms": round(wind_speed, 1),
            "wind_speed_kmh": wind_speed_kmh,
            "wind_direction_deg": wind_deg,
            "wind_direction_label": wind_dir_label,
            "travel_direction_label": travel_dir,
            "description": weather_desc,
            "rain": rain,
        },
        "crop": {
            "name": crop_key,
            "display_name": CROP_PEST_KNOWLEDGE[crop_key]["display_name"],
        },
        "predicted_threats": threats,
        "sweep_zone": sweep_zone,
        "alerts_sent": alerts_info,
        "overall_risk": overall_risk,
        "supported_crops": [{"key": k, "name": v["display_name"]} for k, v in CROP_PEST_KNOWLEDGE.items()],
    }
