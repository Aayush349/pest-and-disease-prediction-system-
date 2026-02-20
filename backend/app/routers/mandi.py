#!/usr/bin/env python3
"""
Mandi Bhav (Market Prices) Router
Fetches real-time agricultural commodity prices from OGD India
With TTL caching to avoid rate-limiting
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
import time
import os
from loguru import logger

router = APIRouter(tags=["Mandi Bhav"])

# OGD API Configuration
OGD_API_KEY = os.getenv("OGD_API_KEY", "579b464db66ec23bdd000001c7a19d86a1f44591589fc7153a4c8926")
OGD_BASE_URL = "https://api.data.gov.in/resource"
MANDI_PRICES_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"

# ─── In-memory TTL cache ───────────────────────────────────────────
CACHE: Dict[str, Any] = {}        # key → {"data": ..., "ts": float}
CACHE_TTL_SECONDS = 300           # 5 minute TTL


def _cache_key(commodity, state, district, limit):
    return f"{commodity}|{state}|{district}|{limit}"


def _get_cached(key: str):
    entry = CACHE.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL_SECONDS:
        logger.info(f"Cache HIT for {key}")
        return entry["data"]
    return None


def _set_cache(key: str, data):
    CACHE[key] = {"data": data, "ts": time.time()}


# ─── Core OGD fetch (single place) ─────────────────────────────────
def fetch_mandi_prices(
    commodity: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """Fetch mandi prices from OGD platform with caching"""

    key = _cache_key(commodity, state, district, limit)
    cached = _get_cached(key)
    if cached:
        return cached

    url = f"{OGD_BASE_URL}/{MANDI_PRICES_RESOURCE_ID}"

    params = {
        "api-key": OGD_API_KEY,
        "format": "json",
        "limit": limit,
        "offset": 0
    }

    if commodity:
        params["filters[commodity]"] = commodity
    if state:
        params["filters[state]"] = state
    if district:
        params["filters[district]"] = district

    try:
        logger.info(f"OGD FETCH: commodity={commodity}, state={state}, district={district}, limit={limit}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        logger.success(f"✓ Fetched {len(data.get('records', []))} price records")
        _set_cache(key, data)
        return data
    except requests.Timeout:
        logger.error("OGD API timeout")
        raise HTTPException(status_code=504, detail="Government API request timed out. Please try again.")
    except requests.RequestException as e:
        logger.error(f"OGD API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data from Government API: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ─── Hardcoded filter lists (avoid hitting OGD just for dropdowns) ──
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chhattisgarh", "Goa", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttrakhand", "West Bengal",
    "Chandigarh", "Delhi", "Jammu and Kashmir", "Ladakh",
    "Puducherry",
]

COMMON_COMMODITIES = [
    "Arhar (Tur/Red Gram)(Whole)", "Bajra(Pearl Millet/Cumbu)",
    "Banana", "Bengal Gram(Gram)(Whole)", "Bhindi(Ladies Finger)",
    "Bitter gourd", "Bottle gourd", "Brinjal", "Cabbage",
    "Capsicum", "Carrot", "Cauliflower", "Coconut",
    "Coriander(Leaves)", "Cotton", "Drumstick", "Garlic",
    "Ginger(Dry)", "Ginger(Green)", "Green Chilli",
    "Green Gram (Moong)(Whole)", "Groundnut", "Guava",
    "Jowar(Sorghum)", "Lemon", "Maize", "Mango",
    "Masoor Dal", "Methi(Fenugreek Leaves)", "Mousambi(Sweet Lime)",
    "Mushrooms", "Onion", "Orange", "Paddy(Dhan)(Common)",
    "Papaya", "Peas(Green)", "Pomegranate", "Potato",
    "Ragi (Finger Millet)", "Rice", "Sesame(Til/Gingelly)",
    "Soyabean", "Spinach", "Sugarcane", "Sunflower",
    "Sweet Potato", "Tamarind Fruit", "Tomato", "Turmeric",
    "Turmeric(Bulb)", "Urad (Beans)(Whole)", "Watermelon", "Wheat",
]


# ─── Endpoints ──────────────────────────────────────────────────────

@router.get("/prices")
async def get_mandi_prices(
    commodity: Optional[str] = Query(None, description="Commodity name"),
    state: Optional[str] = Query(None, description="State name"),
    district: Optional[str] = Query(None, description="District name"),
    limit: int = Query(50, ge=1, le=100, description="Number of records")
):
    """Get current mandi prices (cached for 5 min)"""

    data = fetch_mandi_prices(commodity, state, district, limit)

    return {
        "success": True,
        "count": len(data.get("records", [])),
        "data": data.get("records", []),
        "metadata": {
            "source": "Open Government Data Platform India",
            "api_version": data.get("version", "1.0"),
            "timestamp": datetime.now().isoformat()
        }
    }


@router.get("/commodities")
async def get_available_commodities():
    """
    Returns a hardcoded list of common Indian mandi commodities.
    No OGD call needed — avoids rate limiting.
    """
    return {
        "success": True,
        "commodities": COMMON_COMMODITIES,
        "count": len(COMMON_COMMODITIES)
    }


@router.get("/states")
async def get_available_states():
    """
    Returns a hardcoded list of Indian states.
    No OGD call needed — avoids rate limiting.
    """
    return {
        "success": True,
        "states": INDIAN_STATES,
        "count": len(INDIAN_STATES)
    }


@router.get("/districts")
async def get_districts_by_state(
    state: str = Query(..., description="State name to get districts for")
):
    """Get list of districts for a specific state (cached)"""

    try:
        data = fetch_mandi_prices(state=state, limit=100)
        records = data.get("records", [])

        districts = sorted(set(r.get("district", "") for r in records if r.get("district")))

        logger.info(f"Found {len(districts)} unique districts in {state}")

        return {
            "success": True,
            "state": state,
            "districts": districts,
            "count": len(districts)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching districts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch districts list")


@router.get("/health")
async def check_api_health():
    """Check if OGD API is accessible"""

    try:
        data = fetch_mandi_prices(limit=1)
        return {
            "success": True,
            "status": "healthy",
            "message": "OGD API is accessible",
            "records_fetched": len(data.get("records", []))
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }
