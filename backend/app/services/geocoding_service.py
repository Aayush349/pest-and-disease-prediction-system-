"""
🌍 Geocoding Service – Reverse geocode lat/lon → place name
Uses free OpenStreetMap Nominatim API (no API key needed)
"""

import requests
import time
from typing import Dict, Optional, List

# ============================================================
# 🗺️ IN-MEMORY CACHE (avoid Nominatim rate limits)
# ============================================================
_geocode_cache: Dict[str, Dict] = {}

NOMINATIM_URL = "https://nominatim.openstreetmap.org"
HEADERS = {"User-Agent": "AgroGuard/1.0 (crop-disease-app)"}


def reverse_geocode(lat: float, lon: float) -> Dict[str, str]:
    """
    Convert latitude/longitude → human-readable place name.
    Returns: {"place_name": "City, State", "village": "...", "district": "...", "state": "..."}
    """
    cache_key = f"{round(lat, 3)}_{round(lon, 3)}"

    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    try:
        resp = requests.get(
            f"{NOMINATIM_URL}/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "zoom": 14},
            headers=HEADERS,
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            addr = data.get("address", {})

            village = addr.get("village") or addr.get("town") or addr.get("city") or addr.get("suburb", "")
            district = addr.get("county") or addr.get("state_district", "")
            state = addr.get("state", "")

            place_name = ", ".join(filter(None, [village, district, state]))

            result = {
                "place_name": place_name or data.get("display_name", "Unknown Location"),
                "village": village,
                "district": district,
                "state": state,
            }
            _geocode_cache[cache_key] = result
            return result
    except Exception as e:
        print(f"[Geocoding] Error: {e}")

    # Fallback
    fallback = {"place_name": f"Lat {lat:.3f}, Lon {lon:.3f}", "village": "", "district": "", "state": ""}
    _geocode_cache[cache_key] = fallback
    return fallback


def get_nearby_places(lat: float, lon: float, radius_km: int = 10) -> List[Dict]:
    """
    Find nearby named places within a radius.
    Uses Nominatim search around the given coordinates.
    """
    cache_key = f"nearby_{round(lat, 3)}_{round(lon, 3)}"
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    try:
        # Use a bounding box approach (~0.09 deg ≈ 10km)
        delta = radius_km * 0.009  # approx degrees per km
        resp = requests.get(
            f"{NOMINATIM_URL}/search",
            params={
                "format": "json",
                "viewbox": f"{lon - delta},{lat + delta},{lon + delta},{lat - delta}",
                "bounded": 1,
                "limit": 5,
                "addressdetails": 1,
            },
            headers=HEADERS,
            timeout=5,
        )
        if resp.status_code == 200:
            places = []
            for item in resp.json()[:5]:
                name = item.get("display_name", "").split(",")[0]
                dist_lat = float(item.get("lat", lat))
                dist_lon = float(item.get("lon", lon))
                # Rough distance calculation
                import math
                d = math.sqrt((dist_lat - lat) ** 2 + (dist_lon - lon) ** 2) * 111  # km approx
                direction = _get_compass(lat, lon, dist_lat, dist_lon)
                places.append({
                    "name": name,
                    "distance_km": round(d, 1),
                    "direction": direction,
                    "label": f"{name} ({round(d, 1)}km {direction})",
                })
            _geocode_cache[cache_key] = places
            return places
    except Exception as e:
        print(f"[Nearby] Error: {e}")

    return []


def _get_compass(lat1: float, lon1: float, lat2: float, lon2: float) -> str:
    """Get compass direction from point 1 to point 2"""
    import math
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    angle = math.degrees(math.atan2(dlon, dlat)) % 360
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int((angle + 22.5) / 45) % 8
    return directions[idx]
