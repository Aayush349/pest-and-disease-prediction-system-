import ee
import json
from pathlib import Path

# --- GLOBAL FLAG TO PREVENT RE-AUTH ---
GEE_INITIALIZED = False

def init_gee():
    """
    Google Earth Engine Initialization Logic.
    Prioritizes Default Auth (Browser) -> Then Service Account.
    """
    global GEE_INITIALIZED
    if GEE_INITIALIZED:
        return True

    try:
        # ✅ YOUR PROJECT ID
        MY_PROJECT_ID = 'youtube-automation-483920' 

        # METHOD 1: Default Auth
        try:
            ee.Initialize(project=MY_PROJECT_ID)
            print("✅ GEE Connected via Default Auth")
            GEE_INITIALIZED = True
            return True
        except Exception as e:
            print(f"⚠️ Default Auth Failed, trying credentials file... ({e})")

        # METHOD 2: Service Account (Fallback)
        cred_path = Path(__file__).parent / "credentials.json"
        if cred_path.exists():
            with open(cred_path) as f:
                creds_data = json.load(f)
            
            client_email = creds_data.get('client_email')
            credentials = ee.ServiceAccountCredentials(client_email, str(cred_path))
            ee.Initialize(credentials, project=MY_PROJECT_ID)
            print("✅ GEE Connected via Service Account")
            GEE_INITIALIZED = True
            return True
        else:
            print("❌ No credentials.json found and Default Auth failed.")
            return False

    except Exception as e:
        print(f"❌ GEE Critical Init Error: {e}")
        return False

def get_satellite_health(lat: float, lon: float):
    """
    Generates NDVI Health Score AND Map Tile URL for Frontend.
    """
    # 1. Connection Check
    if not init_gee():
        return {
            "ndvi": 0.0, 
            "status": "Satellite Offline", 
            "tile_url": None,
            "error": "Authentication Failed"
        }

    try:
        # 2. Define Area of Interest (AOI)
        point = ee.Geometry.Point([lon, lat])
        
        # 3. Fetch Satellite Image (Using Harmonized Sentinel-2)
        s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(point)
              .filterDate('2024-01-01', '2025-12-31') 
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) 
              .median()) 

        # 4. Calculate NDVI
        ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')

        # 5. Generate Map Tile URL
        vis_params = {
            'min': 0.0,
            'max': 0.8,
            'palette': ['red', 'orange', 'yellow', 'green', 'darkgreen']
        }
        map_id = ndvi.getMapId(vis_params)
        tile_url = map_id['tile_fetcher'].url_format

        # 6. Calculate Numerical Score
        stats = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(), 
            geometry=point, 
            scale=10
        ).getInfo()
        
        val = stats.get('NDVI', 0)
        if val is None: val = 0.0

        # 7. Determine Health Status
        if val > 0.5: status = "Healthy"
        elif val > 0.3: status = "Moderate Stress"
        else: status = "High Stress"

        return {
            "ndvi": round(val, 3), 
            "status": status,
            "tile_url": tile_url,
            "provider": "Sentinel-2 Satellite"
        }

    except Exception as e:
        print(f"⚠️ GEE Processing Error: {e}")
        return {
            "ndvi": 0.0, 
            "status": "Data Unavailable (Cloud/Server Error)", 
            "tile_url": None,
            "error": str(e)
        }


# import ee
# import os
# from pathlib import Path

# # Step 1: Initialization logic jo backend ke liye stable hai
# def init_gee():
#     """
#     Initialize Google Earth Engine using Service Account.
#     Aapko 'app/utils/credentials.json' file rakhni hogi.
#     """
#     try:
#         if not ee.data._initialized:
#             # Path setup: credentials file ka location
#             current_dir = Path(__file__).parent
#             cred_path = current_dir / "credentials.json"
            
#             if not cred_path.exists():
#                 print(f"❌ ERROR: Credentials file not found at {cred_path}")
#                 return False
                
#             # Service Account se initialize [Hackathon stability ke liye]
#             # Apne service account ki email yahan dalo
#             service_account = "agroguard-service-account@your-project.iam.gserviceaccount.com"
#             credentials = ee.ServiceAccountCredentials(service_account, str(cred_path))
#             ee.Initialize(credentials)
#             print("✅ Earth Engine Initialized Successfully")
#         return True
#     except Exception as e:
#         print(f"❌ GEE Initialization Failed: {e}")
#         return False

# # Step 2: Core NDVI Logic jo tere PPT ke "Macro-Level" vision ko support karega
# def get_satellite_health(lat: float, lon: float):
#     """
#     User ke coordinates ke liye NDVI score aur Stress level nikalna.
#     """
#     if not init_gee():
#         return {"error": "GEE not initialized"}

#     try:
#         # User point (Buffer logic for speed)
#         point = ee.Geometry.Point([lon, lat])
        
#         # Sentinel-2 Collection (As per your original GEE script)
#         s2_col = (ee.ImageCollection('COPERNICUS/S2_SR')
#                   .filterBounds(point)
#                   .filterDate('2024-01-01', '2025-12-31') # Latest available data
#                   .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))

#         # Median image nikalo taaki badal (clouds) ka asar na ho
#         image = s2_col.median()

#         # NDVI Formula: (NIR - Red) / (NIR + Red)
#         # Sentinel-2 mein B8 NIR hai aur B4 Red hai
#         ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')

#         # Point se value extract karna (Radius=30m for accuracy)
#         stats = ndvi.reduceRegion(
#             reducer=ee.Reducer.mean(),
#             geometry=point,
#             scale=10 # 10 meter resolution of Sentinel-2
#         ).getInfo()

#         ndvi_val = stats.get('NDVI', 0)
        
#         if ndvi_val is None:
#             return {"ndvi": 0, "status": "No Data", "risk": "Unknown"}

#         # Logic based on your PPT and Script
#         # Stress < 0.3 | Moderate 0.3-0.5 | Healthy > 0.5
#         if ndvi_val < 0.3:
#             status = "High Stress (Crop at Risk)"
#             risk_level = "High"
#         elif ndvi_val < 0.5:
#             status = "Moderate Stress"
#             risk_level = "Medium"
#         else:
#             status = "Healthy Vegetation"
#             risk_level = "Low"

#         return {
#             "ndvi": round(ndvi_val, 3),
#             "status": status,
#             "risk_score": risk_level,
#             "provider": "Copernicus Sentinel-2"
#         }

#     except Exception as e:
#         return {"error": str(e), "status": "Processing Error"}