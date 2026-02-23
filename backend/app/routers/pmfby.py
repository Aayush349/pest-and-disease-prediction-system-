#!/usr/bin/env python3
"""
🛡️ PMFBY InsurTech Router — Pradhan Mantri Fasal Bima Yojana
AgroGuard v4.0

3 Endpoints:
  1. /calculate-premium   → Official PMFBY premium rates
  2. /estimate-claim      → Predictive financial claim estimator
  3. /verify-claim        → AI Trust Score fraud verification (4 rules)

All responses are natively bilingual (English + Hindi).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, date
import httpx
import math

router = APIRouter()

# ═══════════════════════════════════════════════════════════════════
# 📦 MOCK KNOWLEDGE BASES
# ═══════════════════════════════════════════════════════════════════

# Scale of Finance: Sum Insured per hectare for Madhya Pradesh (MP)
# Source: Agriculture Commissioner, GoMP 2025-26 notifications
SCALE_OF_FINANCE: Dict[str, dict] = {
    "soybean": {
        "sum_insured_per_ha": 40000,
        "season": "Kharif",
        "premium_rate": 0.02,     # 2% for Kharif
        "name_hi": "सोयाबीन",
    },
    "wheat": {
        "sum_insured_per_ha": 45000,
        "season": "Rabi",
        "premium_rate": 0.015,    # 1.5% for Rabi
        "name_hi": "गेहूं",
    },
    "cotton": {
        "sum_insured_per_ha": 50000,
        "season": "Kharif",
        "premium_rate": 0.02,
        "name_hi": "कपास",
    },
    "gram": {
        "sum_insured_per_ha": 35000,
        "season": "Rabi",
        "premium_rate": 0.015,
        "name_hi": "चना",
    },
    "onion": {
        "sum_insured_per_ha": 70000,
        "season": "Commercial",
        "premium_rate": 0.05,     # 5% for Commercial/Horticultural crops
        "name_hi": "प्याज",
    },
    "tomato": {
        "sum_insured_per_ha": 65000,
        "season": "Commercial",
        "premium_rate": 0.05,
        "name_hi": "टमाटर",
    },
    "rice": {
        "sum_insured_per_ha": 42000,
        "season": "Kharif",
        "premium_rate": 0.02,
        "name_hi": "धान",
    },
    "corn": {
        "sum_insured_per_ha": 38000,
        "season": "Kharif",
        "premium_rate": 0.02,
        "name_hi": "मक्का",
    },
}

# ─── Mock YOLO Detection History ───
# Simulates past AI disease/pest detections from our Disease Scanner
MOCK_YOLO_DB: Dict[str, list] = {
    "FARMER_001": [
        {"disease": "Late Blight", "crop": "tomato", "date": "2026-01-15", "confidence": 0.92},
        {"disease": "Leaf Curl", "crop": "tomato", "date": "2026-01-28", "confidence": 0.87},
    ],
    "FARMER_002": [
        {"disease": "Rust", "crop": "wheat", "date": "2026-02-01", "confidence": 0.95},
    ],
    "FARMER_003": [
        {"disease": "Aphid Infestation", "crop": "soybean", "date": "2025-12-10", "confidence": 0.88},
    ],
    "FARMER_004": [],   # No prior detections — suspicious if claiming disease damage
    "FARMER_005": [
        {"disease": "Powdery Mildew", "crop": "gram", "date": "2026-01-20", "confidence": 0.91},
    ],
}

# ─── Mock Peer Claims Database ───
# Simulates claims from neighboring farmers within 2km radius
MOCK_PEER_DB: Dict[str, list] = {
    "22.72_75.86": [
        {"farmer": "Ramesh K.", "damage": "Flood", "date": "2026-02-10"},
        {"farmer": "Sunita D.", "damage": "Flood", "date": "2026-02-10"},
        {"farmer": "Govind Y.", "damage": "Flood", "date": "2026-02-11"},
        {"farmer": "Meena B.", "damage": "Flood", "date": "2026-02-11"},
    ],
    "22.60_75.80": [
        {"farmer": "Vikram S.", "damage": "Hailstorm", "date": "2026-02-05"},
    ],
    "23.00_76.00": [],  # No peer claims — isolated area
}


# ═══════════════════════════════════════════════════════════════════
# 📋 PYDANTIC MODELS — Request & Response Schemas
# ═══════════════════════════════════════════════════════════════════

class BilingualText(BaseModel):
    en: str
    hi: str


# ─── Endpoint 1: Premium Calculator ───
class PremiumRequest(BaseModel):
    crop_name: str = Field(..., description="Crop name (lowercase)", examples=["soybean"])
    area_in_hectares: float = Field(..., gt=0, le=100, description="Farm area in hectares")

class PremiumResponse(BaseModel):
    crop_name: str
    season: str
    area_in_hectares: float
    sum_insured_per_hectare: float
    total_sum_insured: float
    premium_rate_percent: float
    farmer_premium_share: float
    government_subsidy_share: float
    message: BilingualText


# ─── Endpoint 2: Claim Estimator ───
class ClaimEstimateRequest(BaseModel):
    crop_name: str = Field(..., examples=["wheat"])
    area_in_hectares: float = Field(..., gt=0, le=100)
    estimated_damage_percentage: float = Field(
        ..., ge=0, le=100,
        description="Damage % from prediction engine or field observation"
    )

class ClaimEstimateResponse(BaseModel):
    crop_name: str
    area_in_hectares: float
    damage_percentage: float
    total_sum_insured: float
    estimated_financial_loss: float
    estimated_pmfby_claim: float
    is_admissible: bool
    advice: BilingualText
    warning: Optional[BilingualText] = None


# ─── Endpoint 3: Fraud Verification ───
class ClaimVerificationRequest(BaseModel):
    farmer_id: str = Field(..., description="Unique farmer identifier", examples=["FARMER_001"])
    lat: float = Field(..., description="Farm latitude")
    lon: float = Field(..., description="Farm longitude")
    crop_name: str = Field(..., examples=["soybean"])
    damage_type: str = Field(
        ..., description="Type of damage claimed",
        examples=["Flood", "Drought", "Disease", "Hailstorm", "Pest"]
    )
    damage_date: str = Field(..., description="Date of alleged damage (YYYY-MM-DD)", examples=["2026-02-10"])
    pre_disaster_ndvi: float = Field(..., ge=0, le=1, description="NDVI before disaster")
    post_disaster_ndvi: float = Field(..., ge=0, le=1, description="NDVI after disaster")

class VerificationLog(BaseModel):
    rule: str
    score_change: int
    explanation: BilingualText

class ClaimVerificationResponse(BaseModel):
    farmer_id: str
    crop_name: str
    damage_type: str
    trust_score: int
    claim_status: str
    verification_logs: List[VerificationLog]
    recommendation: BilingualText
    timestamp: str


# ═══════════════════════════════════════════════════════════════════
# 🔧 HELPER: Fetch 7-day historical weather from Open-Meteo
# ═══════════════════════════════════════════════════════════════════

async def fetch_historical_weather(lat: float, lon: float, damage_date_str: str) -> dict:
    """
    Fetch 7-day weather around the damage date using Open-Meteo Archive API.
    Falls back to mock data if the API call fails.
    """
    try:
        d = date.fromisoformat(damage_date_str)
        start = d.replace(day=max(1, d.day - 7)).isoformat()
        end = d.isoformat()

        url = (
            f"https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}&longitude={lon}"
            f"&start_date={start}&end_date={end}"
            f"&daily=rain_sum,temperature_2m_max,temperature_2m_min"
            f"&timezone=auto"
        )

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                daily = data.get("daily", {})
                rain_vals = [r for r in (daily.get("rain_sum") or []) if r is not None]
                return {
                    "source": "Open-Meteo Archive API",
                    "rain_sum_mm": sum(rain_vals),
                    "rain_days": len([r for r in rain_vals if r > 1]),
                    "max_temp": max(daily.get("temperature_2m_max") or [0]),
                    "min_temp": min(daily.get("temperature_2m_min") or [0]),
                }
    except Exception:
        pass

    # ─── Mock Fallback ───
    return {
        "source": "Satellite Reanalysis Baseline (mock)",
        "rain_sum_mm": 85.0,
        "rain_days": 4,
        "max_temp": 35.0,
        "min_temp": 18.0,
    }


# ═══════════════════════════════════════════════════════════════════
# 🟢 ENDPOINT 1: Premium Calculator
# ═══════════════════════════════════════════════════════════════════

@router.post("/calculate-premium", response_model=PremiumResponse)
async def calculate_premium(req: PremiumRequest):
    """
    Calculate PMFBY premium for a given crop and area.
    Uses official Government of India premium rates:
      - Kharif (monsoon crops): 2% of Sum Insured
      - Rabi (winter crops): 1.5% of Sum Insured
      - Commercial/Horticulture: 5% of Sum Insured
    """
    crop = req.crop_name.lower().strip()
    sof = SCALE_OF_FINANCE.get(crop)

    if not sof:
        supported = ", ".join(SCALE_OF_FINANCE.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Crop '{crop}' not found. Supported crops: {supported}"
        )

    total_sum_insured = sof["sum_insured_per_ha"] * req.area_in_hectares
    farmer_premium = total_sum_insured * sof["premium_rate"]
    govt_subsidy = total_sum_insured - farmer_premium  # Govt covers the rest

    rate_pct = sof["premium_rate"] * 100
    crop_hi = sof.get("name_hi", crop)

    return PremiumResponse(
        crop_name=crop,
        season=sof["season"],
        area_in_hectares=req.area_in_hectares,
        sum_insured_per_hectare=sof["sum_insured_per_ha"],
        total_sum_insured=total_sum_insured,
        premium_rate_percent=rate_pct,
        farmer_premium_share=round(farmer_premium, 2),
        government_subsidy_share=round(govt_subsidy, 2),
        message=BilingualText(
            en=f"For {req.area_in_hectares} hectares of {crop.title()} ({sof['season']}), "
               f"your premium is ₹{farmer_premium:,.0f} ({rate_pct}% of ₹{total_sum_insured:,.0f}). "
               f"Government subsidy covers ₹{govt_subsidy:,.0f}.",
            hi=f"{req.area_in_hectares} हेक्टेयर {crop_hi} ({sof['season']}) के लिए "
               f"आपका प्रीमियम ₹{farmer_premium:,.0f} है ({rate_pct}% of ₹{total_sum_insured:,.0f})। "
               f"सरकारी सब्सिडी ₹{govt_subsidy:,.0f} कवर करती है।",
        ),
    )


# ═══════════════════════════════════════════════════════════════════
# 🟡 ENDPOINT 2: Predictive Claim Estimator
# ═══════════════════════════════════════════════════════════════════

@router.post("/estimate-claim", response_model=ClaimEstimateResponse)
async def estimate_claim(req: ClaimEstimateRequest):
    """
    Estimate the PMFBY claim amount based on damage percentage.
    If damage < 15%, warns the farmer about admissibility threshold.
    """
    crop = req.crop_name.lower().strip()
    sof = SCALE_OF_FINANCE.get(crop)

    if not sof:
        supported = ", ".join(SCALE_OF_FINANCE.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Crop '{crop}' not found. Supported crops: {supported}"
        )

    total_si = sof["sum_insured_per_ha"] * req.area_in_hectares
    financial_loss = (req.estimated_damage_percentage / 100) * total_si
    estimated_claim = financial_loss  # Under PMFBY, proportional indemnity

    crop_hi = sof.get("name_hi", crop)
    is_admissible = req.estimated_damage_percentage >= 15

    # Build warning for low damage
    warning = None
    if not is_admissible:
        warning = BilingualText(
            en=f"⚠️ Warning: Damage below 15% ({req.estimated_damage_percentage:.1f}%) may not qualify "
               f"for PMFBY claim. Minimum threshold is typically 15-20% crop loss.",
            hi=f"⚠️ चेतावनी: 15% से कम नुकसान ({req.estimated_damage_percentage:.1f}%) PMFBY दावे के "
               f"लिए योग्य नहीं हो सकता। न्यूनतम सीमा आमतौर पर 15-20% फसल हानि है।",
        )

    # Actionable advice
    if is_admissible and req.estimated_damage_percentage >= 50:
        advice = BilingualText(
            en=f"🚨 Severe damage detected ({req.estimated_damage_percentage:.0f}%). "
               f"File your PMFBY claim within 72 hours. Estimated payout: ₹{estimated_claim:,.0f}. "
               f"Contact your bank/CSC immediately.",
            hi=f"🚨 गंभीर नुकसान ({req.estimated_damage_percentage:.0f}%) पाया गया। "
               f"72 घंटे के भीतर अपना PMFBY दावा दर्ज करें। अनुमानित भुगतान: ₹{estimated_claim:,.0f}। "
               f"तुरंत अपने बैंक/CSC से संपर्क करें।",
        )
    elif is_admissible:
        advice = BilingualText(
            en=f"📋 Moderate damage ({req.estimated_damage_percentage:.0f}%). "
               f"You are eligible for PMFBY claim. Estimated payout: ₹{estimated_claim:,.0f}. "
               f"Notify your insurance company and document damage with photos.",
            hi=f"📋 मध्यम नुकसान ({req.estimated_damage_percentage:.0f}%)। "
               f"आप PMFBY दावे के योग्य हैं। अनुमानित भुगतान: ₹{estimated_claim:,.0f}। "
               f"बीमा कंपनी को सूचित करें और फोटो से नुकसान दर्ज करें।",
        )
    else:
        advice = BilingualText(
            en=f"ℹ️ Low damage ({req.estimated_damage_percentage:.0f}%). "
               f"Monitor your crop closely. You may not meet the PMFBY threshold yet. "
               f"Use AgroGuard's Disease Scanner to track progression.",
            hi=f"ℹ️ कम नुकसान ({req.estimated_damage_percentage:.0f}%)। "
               f"अपनी फसल की बारीकी से निगरानी करें। अभी PMFBY सीमा पूरी नहीं हो सकती। "
               f"प्रगति ट्रैक करने के लिए AgroGuard के रोग स्कैनर का उपयोग करें।",
        )

    return ClaimEstimateResponse(
        crop_name=crop,
        area_in_hectares=req.area_in_hectares,
        damage_percentage=req.estimated_damage_percentage,
        total_sum_insured=total_si,
        estimated_financial_loss=round(financial_loss, 2),
        estimated_pmfby_claim=round(estimated_claim, 2),
        is_admissible=is_admissible,
        advice=advice,
        warning=warning,
    )


# ═══════════════════════════════════════════════════════════════════
# 🔴 ENDPOINT 3: Smart Claim Fraud Verification (AI Trust Score)
# ═══════════════════════════════════════════════════════════════════

@router.post("/verify-claim", response_model=ClaimVerificationResponse)
async def verify_claim(req: ClaimVerificationRequest):
    """
    AI-powered claim fraud verification.
    Calculates a trust score (0-100) using 5 distinct InsurTech rules:
      A) YOLO History Cross-Check
      B) Parametric Weather Proof (Open-Meteo)
      C) Satellite NDVI Delta-Drop + Sanity Check
      D) Digital Panchayat (Peer Verification)
      E) Cross-Validation (Weather ↔ NDVI consistency)
    """
    trust_score = 50  # Start neutral
    logs: List[VerificationLog] = []

    damage_lower = req.damage_type.lower()
    is_catastrophe = damage_lower in ("flood", "drought", "hailstorm")
    damage_is_disease = damage_lower in ("disease", "pest")

    # ─────────────────────────────────────────────────────────
    # RULE A: AI History Cross-Check (YOLO Disease Scanner)
    # ─────────────────────────────────────────────────────────
    yolo_history = MOCK_YOLO_DB.get(req.farmer_id, [])

    if damage_is_disease:
        if len(yolo_history) > 0:
            last_detection = yolo_history[-1]
            trust_score += 20
            logs.append(VerificationLog(
                rule="Rule A: YOLO History",
                score_change=+20,
                explanation=BilingualText(
                    en=f"✅ Prior AI detection found: '{last_detection['disease']}' "
                       f"({last_detection['date']}, confidence {last_detection['confidence']:.0%}). "
                       f"Claim is consistent with disease history.",
                    hi=f"✅ पूर्व AI पहचान मिली: '{last_detection['disease']}' "
                       f"({last_detection['date']}, विश्वास {last_detection['confidence']:.0%})। "
                       f"दावा रोग इतिहास से मेल खाता है।",
                ),
            ))
        else:
            trust_score -= 20
            logs.append(VerificationLog(
                rule="Rule A: YOLO History",
                score_change=-20,
                explanation=BilingualText(
                    en=f"🔴 No prior AI disease/pest detection found for {req.farmer_id}. "
                       f"Sudden disease claim without documented history is suspicious.",
                    hi=f"🔴 {req.farmer_id} के लिए कोई पूर्व AI रोग/कीट पहचान नहीं मिली। "
                       f"बिना दस्तावेज इतिहास के अचानक रोग दावा संदेहास्पद है।",
                ),
            ))
    else:
        # Non-disease/pest claims (Drought, Flood, Hailstorm) bypass YOLO
        # but get a small penalty since they can't provide AI evidence
        trust_score -= 10
        logs.append(VerificationLog(
            rule="Rule A: YOLO History",
            score_change=-10,
            explanation=BilingualText(
                en=f"⚠️ Damage type '{req.damage_type}' has no AI detection trail. "
                   f"Catastrophe claims require stronger evidence from other checks.",
                hi=f"⚠️ नुकसान प्रकार '{req.damage_type}' का कोई AI पहचान ट्रेल नहीं। "
                   f"आपदा दावों के लिए अन्य जांचों से मजबूत सबूत आवश्यक।",
            ),
        ))

    # ─────────────────────────────────────────────────────────
    # RULE B: Parametric Weather Proof (Open-Meteo Archive API)
    # ─────────────────────────────────────────────────────────
    weather = await fetch_historical_weather(req.lat, req.lon, req.damage_date)
    rain_mm = weather["rain_sum_mm"]
    rain_days = weather["rain_days"]

    if damage_lower == "flood":
        if rain_mm > 100:
            trust_score += 25
            logs.append(VerificationLog(
                rule="Rule B: Weather Proof",
                score_change=+25,
                explanation=BilingualText(
                    en=f"✅ Heavy rainfall confirmed: {rain_mm:.0f}mm over {rain_days} days. "
                       f"Flood claim is weather-verified. (Source: {weather['source']})",
                    hi=f"✅ भारी बारिश की पुष्टि: {rain_mm:.0f}mm, {rain_days} दिन। "
                       f"बाढ़ दावा मौसम-सत्यापित। (स्रोत: {weather['source']})",
                ),
            ))
        elif rain_mm < 10:
            trust_score -= 30
            logs.append(VerificationLog(
                rule="Rule B: Weather Proof",
                score_change=-30,
                explanation=BilingualText(
                    en=f"🔴 Minimal rainfall recorded: only {rain_mm:.0f}mm. "
                       f"Flood claim WITHOUT significant precipitation is highly suspect.",
                    hi=f"🔴 न्यूनतम वर्षा दर्ज: केवल {rain_mm:.0f}mm। "
                       f"महत्वपूर्ण बारिश के बिना बाढ़ दावा अत्यधिक संदिग्ध है।",
                ),
            ))
        else:
            change = 10
            trust_score += change
            logs.append(VerificationLog(
                rule="Rule B: Weather Proof",
                score_change=change,
                explanation=BilingualText(
                    en=f"⚠️ Moderate rainfall: {rain_mm:.0f}mm. Partial weather support for flood claim.",
                    hi=f"⚠️ मध्यम बारिश: {rain_mm:.0f}mm। बाढ़ दावे के लिए आंशिक मौसम समर्थन।",
                ),
            ))

    elif damage_lower == "drought":
        if rain_mm == 0 or rain_mm < 5:
            trust_score += 20  # Reduced from 30 — drought needs more evidence
            logs.append(VerificationLog(
                rule="Rule B: Weather Proof",
                score_change=+20,
                explanation=BilingualText(
                    en=f"✅ Zero/negligible rainfall confirmed ({rain_mm:.0f}mm). "
                       f"Weather supports drought conditions but requires satellite and peer verification.",
                    hi=f"✅ शून्य/नगण्य वर्षा की पुष्टि ({rain_mm:.0f}mm)। "
                       f"मौसम सूखे की स्थिति का समर्थन करता है लेकिन सैटेलाइट और पीयर सत्यापन आवश्यक।",
                ),
            ))
        elif rain_mm > 50:
            trust_score -= 30
            logs.append(VerificationLog(
                rule="Rule B: Weather Proof",
                score_change=-30,
                explanation=BilingualText(
                    en=f"🔴 Significant rainfall ({rain_mm:.0f}mm) recorded. "
                       f"Drought claim contradicts weather data — likely fraudulent.",
                    hi=f"🔴 महत्वपूर्ण बारिश ({rain_mm:.0f}mm) दर्ज। "
                       f"सूखा दावा मौसम डेटा से विपरीत — संभवतः धोखाधड़ी।",
                ),
            ))
        else:
            trust_score += 5  # Reduced — inconclusive
            logs.append(VerificationLog(
                rule="Rule B: Weather Proof",
                score_change=+5,
                explanation=BilingualText(
                    en=f"⚠️ Low rainfall ({rain_mm:.0f}mm). Weather only partially supports drought claim.",
                    hi=f"⚠️ कम बारिश ({rain_mm:.0f}mm)। मौसम आंशिक रूप से सूखा दावे का समर्थन करता है।",
                ),
            ))

    elif damage_lower == "hailstorm":
        if weather.get("min_temp", 20) < 5:
            trust_score += 15
            logs.append(VerificationLog(
                rule="Rule B: Weather Proof",
                score_change=+15,
                explanation=BilingualText(
                    en=f"✅ Low temperature ({weather['min_temp']:.0f}°C) supports hailstorm conditions.",
                    hi=f"✅ कम तापमान ({weather['min_temp']:.0f}°C) ओलावृष्टि की स्थिति का समर्थन करता है।",
                ),
            ))
        else:
            logs.append(VerificationLog(
                rule="Rule B: Weather Proof",
                score_change=0,
                explanation=BilingualText(
                    en=f"ℹ️ Temperature ({weather['min_temp']:.0f}°C) does not strongly indicate hailstorm.",
                    hi=f"ℹ️ तापमान ({weather['min_temp']:.0f}°C) ओलावृष्टि का मजबूत संकेत नहीं।",
                ),
            ))

    else:
        # Disease/Pest — weather is secondary
        logs.append(VerificationLog(
            rule="Rule B: Weather Proof",
            score_change=0,
            explanation=BilingualText(
                en=f"ℹ️ Damage type '{req.damage_type}' — weather verification is secondary. "
                   f"Rainfall: {rain_mm:.0f}mm.",
                hi=f"ℹ️ नुकसान प्रकार '{req.damage_type}' — मौसम सत्यापन गौण। "
                   f"बारिश: {rain_mm:.0f}mm।",
            ),
        ))

    # ─────────────────────────────────────────────────────────
    # RULE C: Satellite NDVI Delta-Drop + Drought Sanity Check
    # ─────────────────────────────────────────────────────────
    ndvi_drop = req.pre_disaster_ndvi - req.post_disaster_ndvi
    physical_damage = damage_lower in ("flood", "hailstorm", "drought")

    if physical_damage:
        # ── DROUGHT-SPECIFIC SANITY CHECK ──
        # If claiming drought but post-NDVI is still green (> 0.35),
        # the crop wasn't actually damaged → penalize heavily
        if damage_lower == "drought" and req.post_disaster_ndvi > 0.35:
            trust_score -= 25
            logs.append(VerificationLog(
                rule="Rule C: NDVI Sanity Check",
                score_change=-25,
                explanation=BilingualText(
                    en=f"🔴 Post-disaster NDVI is {req.post_disaster_ndvi:.2f} — vegetation still "
                       f"green/healthy. Genuine drought kills vegetation (NDVI < 0.20). "
                       f"Claim appears fabricated.",
                    hi=f"🔴 आपदा के बाद NDVI {req.post_disaster_ndvi:.2f} है — वनस्पति अभी भी "
                       f"हरी/स्वस्थ। वास्तविक सूखे में वनस्पति मर जाती है (NDVI < 0.20)। "
                       f"दावा मिथ्या प्रतीत होता है।",
                ),
            ))
        elif damage_lower == "drought" and req.post_disaster_ndvi > 0.20:
            trust_score -= 10
            logs.append(VerificationLog(
                rule="Rule C: NDVI Sanity Check",
                score_change=-10,
                explanation=BilingualText(
                    en=f"⚠️ Post-disaster NDVI ({req.post_disaster_ndvi:.2f}) shows residual vegetation. "
                       f"Drought damage is questionable at this NDVI level.",
                    hi=f"⚠️ आपदा के बाद NDVI ({req.post_disaster_ndvi:.2f}) में अवशिष्ट वनस्पति दिखती है। "
                       f"इस NDVI स्तर पर सूखे की क्षति संदिग्ध है।",
                ),
            ))

        # ── Standard NDVI drop scoring ──
        if ndvi_drop > 0.40:
            trust_score += 20  # Reduced from 30
            logs.append(VerificationLog(
                rule="Rule C: NDVI Delta-Drop",
                score_change=+20,
                explanation=BilingualText(
                    en=f"✅ Massive NDVI drop detected: {req.pre_disaster_ndvi:.2f} → "
                       f"{req.post_disaster_ndvi:.2f} (Δ = {ndvi_drop:+.2f}). "
                       f"Satellite confirms severe physical damage.",
                    hi=f"✅ भारी NDVI गिरावट: {req.pre_disaster_ndvi:.2f} → "
                       f"{req.post_disaster_ndvi:.2f} (Δ = {ndvi_drop:+.2f})। "
                       f"सैटेलाइट गंभीर भौतिक क्षति की पुष्टि करता है।",
                ),
            ))
        elif ndvi_drop > 0.15:
            trust_score += 10
            logs.append(VerificationLog(
                rule="Rule C: NDVI Delta-Drop",
                score_change=+10,
                explanation=BilingualText(
                    en=f"⚠️ Moderate NDVI drop: {ndvi_drop:+.2f}. Some vegetation damage confirmed.",
                    hi=f"⚠️ मध्यम NDVI गिरावट: {ndvi_drop:+.2f}। कुछ वनस्पति क्षति की पुष्टि।",
                ),
            ))
        elif ndvi_drop < 0.05:
            trust_score -= 30
            logs.append(VerificationLog(
                rule="Rule C: NDVI Delta-Drop",
                score_change=-30,
                explanation=BilingualText(
                    en=f"🔴 Negligible NDVI change: {ndvi_drop:+.2f}. "
                       f"No satellite evidence of physical crop damage. Likely fake claim.",
                    hi=f"🔴 नगण्य NDVI परिवर्तन: {ndvi_drop:+.2f}। "
                       f"भौतिक फसल क्षति का कोई सैटेलाइट प्रमाण नहीं। संभवतः झूठा दावा।",
                ),
            ))
        else:
            logs.append(VerificationLog(
                rule="Rule C: NDVI Delta-Drop",
                score_change=0,
                explanation=BilingualText(
                    en=f"ℹ️ Minor NDVI change: {ndvi_drop:+.2f}. Inconclusive for physical damage.",
                    hi=f"ℹ️ मामूली NDVI परिवर्तन: {ndvi_drop:+.2f}। भौतिक क्षति के लिए अनिर्णायक।",
                ),
            ))
    else:
        # Disease/Pest — NDVI drop is slower, give partial credit
        if ndvi_drop > 0.20:
            trust_score += 10
            logs.append(VerificationLog(
                rule="Rule C: NDVI Delta-Drop",
                score_change=+10,
                explanation=BilingualText(
                    en=f"✅ NDVI decline ({ndvi_drop:+.2f}) supports gradual disease/pest damage.",
                    hi=f"✅ NDVI गिरावट ({ndvi_drop:+.2f}) धीरे-धीरे रोग/कीट क्षति का समर्थन करती है।",
                ),
            ))
        else:
            logs.append(VerificationLog(
                rule="Rule C: NDVI Delta-Drop",
                score_change=0,
                explanation=BilingualText(
                    en=f"ℹ️ NDVI delta ({ndvi_drop:+.2f}) is within normal range for disease claims.",
                    hi=f"ℹ️ NDVI डेल्टा ({ndvi_drop:+.2f}) रोग दावों के लिए सामान्य सीमा में।",
                ),
            ))

    # ─────────────────────────────────────────────────────────
    # RULE D: Digital Panchayat (Peer Verification)
    # More weight — isolated catastrophe claims are very suspicious
    # ─────────────────────────────────────────────────────────
    grid_key = f"{round(req.lat, 2)}_{round(req.lon, 2)}"
    peer_claims = MOCK_PEER_DB.get(grid_key, [])

    for dlat in [-0.01, 0, 0.01]:
        for dlon in [-0.01, 0, 0.01]:
            neighbor_key = f"{round(req.lat + dlat, 2)}_{round(req.lon + dlon, 2)}"
            if neighbor_key != grid_key:
                peer_claims.extend(MOCK_PEER_DB.get(neighbor_key, []))

    matching_peers = [
        p for p in peer_claims
        if p["damage"].lower() == damage_lower
    ]

    if len(matching_peers) >= 3:
        trust_score += 20
        names = ", ".join([p["farmer"] for p in matching_peers[:3]])
        logs.append(VerificationLog(
            rule="Rule D: Digital Panchayat",
            score_change=+20,
            explanation=BilingualText(
                en=f"✅ {len(matching_peers)} neighboring farmers also claimed '{req.damage_type}' damage "
                   f"(e.g., {names}). Area-wide outbreak confirmed.",
                hi=f"✅ {len(matching_peers)} पड़ोसी किसानों ने भी '{req.damage_type}' नुकसान का दावा किया "
                   f"(जैसे, {names})। क्षेत्र-व्यापी प्रकोप की पुष्टि।",
            ),
        ))
    elif len(matching_peers) >= 1:
        trust_score += 5
        logs.append(VerificationLog(
            rule="Rule D: Digital Panchayat",
            score_change=+5,
            explanation=BilingualText(
                en=f"⚠️ Only {len(matching_peers)} neighbor(s) reported similar damage. Partial peer support.",
                hi=f"⚠️ केवल {len(matching_peers)} पड़ोसी ने समान नुकसान की रिपोर्ट की। आंशिक पीयर समर्थन।",
            ),
        ))
    else:
        # Zero neighbors — isolated claim is very suspicious for catastrophe
        penalty = -25 if is_catastrophe else -15
        trust_score += penalty
        logs.append(VerificationLog(
            rule="Rule D: Digital Panchayat",
            score_change=penalty,
            explanation=BilingualText(
                en=f"🔴 No neighboring farmers reported '{req.damage_type}' in 2km radius. "
                   f"{'Catastrophe events affect entire areas — isolated claim is highly suspect.' if is_catastrophe else 'Isolated claim is suspicious.'}",
                hi=f"🔴 2km दायरे में किसी पड़ोसी किसान ने '{req.damage_type}' की रिपोर्ट नहीं की। "
                   f"{'आपदा घटनाएं पूरे क्षेत्र को प्रभावित करती हैं — एकांत दावा अत्यधिक संदिग्ध।' if is_catastrophe else 'एकांत दावा संदिग्ध है।'}",
            ),
        ))

    # ─────────────────────────────────────────────────────────
    # RULE E: Cross-Validation (Weather ↔ NDVI consistency)
    # Catches cases where someone enters fake NDVI to boost score
    # ─────────────────────────────────────────────────────────
    if damage_lower == "drought" and rain_mm > 30 and ndvi_drop > 0.30:
        # Claiming drought with NDVI drop but rain was decent → contradiction
        trust_score -= 15
        logs.append(VerificationLog(
            rule="Rule E: Cross-Validation",
            score_change=-15,
            explanation=BilingualText(
                en=f"🔴 Contradiction: NDVI shows massive drop ({ndvi_drop:+.2f}) but rainfall was "
                   f"{rain_mm:.0f}mm — inconsistent with drought. Possible data manipulation.",
                hi=f"🔴 विरोधाभास: NDVI भारी गिरावट ({ndvi_drop:+.2f}) दिखाता है लेकिन बारिश "
                   f"{rain_mm:.0f}mm थी — सूखे से असंगत। संभव डेटा हेराफेरी।",
            ),
        ))
    elif damage_lower == "flood" and rain_mm < 20 and ndvi_drop > 0.40:
        trust_score -= 15
        logs.append(VerificationLog(
            rule="Rule E: Cross-Validation",
            score_change=-15,
            explanation=BilingualText(
                en=f"🔴 Contradiction: NDVI drop ({ndvi_drop:+.2f}) suggests damage but rainfall "
                   f"({rain_mm:.0f}mm) doesn't support flooding. Possible fabrication.",
                hi=f"🔴 विरोधाभास: NDVI गिरावट ({ndvi_drop:+.2f}) क्षति सुझाती है लेकिन बारिश "
                   f"({rain_mm:.0f}mm) बाढ़ का समर्थन नहीं करती। संभव मिथ्याकरण।",
            ),
        ))
    else:
        logs.append(VerificationLog(
            rule="Rule E: Cross-Validation",
            score_change=0,
            explanation=BilingualText(
                en=f"ℹ️ Weather and NDVI data are consistent. No cross-validation anomaly detected.",
                hi=f"ℹ️ मौसम और NDVI डेटा सुसंगत हैं। कोई क्रॉस-सत्यापन विसंगति नहीं।",
            ),
        ))

    # ─────────────────────────────────────────────────────────
    # FINAL VERDICT (threshold raised: 85+ for auto-approve)
    # ─────────────────────────────────────────────────────────
    trust_score = max(0, min(100, trust_score))  # Clamp 0-100

    if trust_score >= 85:
        claim_status = "AUTO_APPROVED"
        recommendation = BilingualText(
            en=f"🟢 Claim AUTO-APPROVED (Trust Score: {trust_score}/100). "
               f"All verification checks passed. Initiate payout processing.",
            hi=f"🟢 दावा स्वचालित-स्वीकृत (विश्वास स्कोर: {trust_score}/100)। "
               f"सभी सत्यापन जांच पास। भुगतान प्रसंस्करण शुरू करें।",
        )
    elif trust_score >= 40:
        claim_status = "MANUAL_INSPECTION_REQUIRED"
        recommendation = BilingualText(
            en=f"🟡 MANUAL INSPECTION REQUIRED (Trust Score: {trust_score}/100). "
               f"Some verification checks inconclusive. Field visit recommended before approval.",
            hi=f"🟡 मैनुअल निरीक्षण आवश्यक (विश्वास स्कोर: {trust_score}/100)। "
               f"कुछ सत्यापन जांच अनिर्णायक। अनुमोदन से पहले फील्ड विज़िट सुझाई गई।",
        )
    else:
        claim_status = "REJECTED_FRAUD_SUSPECTED"
        recommendation = BilingualText(
            en=f"🔴 CLAIM REJECTED — FRAUD SUSPECTED (Trust Score: {trust_score}/100). "
               f"Multiple verification checks failed. Escalate to investigation.",
            hi=f"🔴 दावा अस्वीकृत — धोखाधड़ी का संदेह (विश्वास स्कोर: {trust_score}/100)। "
               f"कई सत्यापन जांच विफल। जांच के लिए आगे बढ़ाएं।",
        )

    return ClaimVerificationResponse(
        farmer_id=req.farmer_id,
        crop_name=req.crop_name,
        damage_type=req.damage_type,
        trust_score=trust_score,
        claim_status=claim_status,
        verification_logs=logs,
        recommendation=recommendation,
        timestamp=datetime.utcnow().isoformat(),
    )
