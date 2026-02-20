#!/usr/bin/env python3
"""
Mandi Bhav (Market Prices) Router
Fetches real-time agricultural commodity prices from OGD India
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
from functools import lru_cache
import os
from loguru import logger

router = APIRouter(tags=["Mandi Bhav"])

# OGD API Configuration
OGD_API_KEY = os.getenv("OGD_API_KEY", "579b464db66ec23bdd000001ce2613d1e78d44a174639d88517ace56")
OGD_BASE_URL = "https://api.data.gov.in/resource"
MANDI_PRICES_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"

def fetch_mandi_prices(
    commodity: Optional[str] = None,
    state: Optional[str] = None, 
    district: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """Fetch mandi prices from OGD platform"""
    
    url = f"{OGD_BASE_URL}/{MANDI_PRICES_RESOURCE_ID}"
    
    params = {
        "api-key": OGD_API_KEY,
        "format": "json",
        "limit": limit,
        "offset": 0
    }
    
    # Add filters if provided
    if commodity:
        params["filters[commodity]"] = commodity
    if state:
        params["filters[state]"] = state
    if district:
        params["filters[district]"] = district
    
    try:
        logger.info(f"Fetching mandi prices: commodity={commodity}, state={state}, district={district}")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        logger.success(f"✓ Fetched {len(data.get('records', []))} price records")
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


@router.get("/prices")
async def get_mandi_prices(
    commodity: Optional[str] = Query(None, description="Commodity name (e.g., Wheat, Rice, Paddy)"),
    state: Optional[str] = Query(None, description="State name (e.g., Punjab, Maharashtra)"),
    district: Optional[str] = Query(None, description="District name"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to fetch")
):
    """
    Get current mandi prices for agricultural commodities
    
    **Example Queries**:
    - `/api/mandi/prices?commodity=Wheat&state=Punjab`
    - `/api/mandi/prices?commodity=Rice&limit=20`
    - `/api/mandi/prices?state=Maharashtra&district=Pune`
    
    **Returns**:
    - List of mandi price records with min, max, and modal prices
    - Prices are typically in ₹/Quintal (100 kg)
    """
    
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
    Get list of available commodities in the mandi database
    
    **Returns**: List of unique commodity names
    """
    
    try:
        # Fetch sample data to extract unique commodities
        data = fetch_mandi_prices(limit=100)
        records = data.get("records", [])
        
        # Extract unique commodities
        commodities = list(set(r.get("commodity", "") for r in records if r.get("commodity")))
        commodities.sort()
        
        logger.info(f"Found {len(commodities)} unique commodities")
        
        return {
            "success": True,
            "commodities": commodities,
            "count": len(commodities)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching commodities: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch commodities list")


@router.get("/states")
async def get_available_states():
    """
    Get list of states with mandi price data
    
    **Returns**: List of unique state names
    """
    
    try:
        data = fetch_mandi_prices(limit=100)
        records = data.get("records", [])
        
        # Extract unique states
        states = list(set(r.get("state", "") for r in records if r.get("state")))
        states.sort()
        
        logger.info(f"Found {len(states)} unique states")
        
        return {
            "success": True,
            "states": states,
            "count": len(states)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching states: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch states list")


@router.get("/districts")
async def get_districts_by_state(
    state: str = Query(..., description="State name to get districts for")
):
    """
    Get list of districts for a specific state
    
    **Parameters**:
    - `state`: State name (e.g., Punjab, Maharashtra)
    
    **Returns**: List of districts with mandi data in that state
    """
    
    try:
        data = fetch_mandi_prices(state=state, limit=100)
        records = data.get("records", [])
        
        # Extract unique districts
        districts = list(set(r.get("district", "") for r in records if r.get("district")))
        districts.sort()
        
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
