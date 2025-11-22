import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os
from pathlib import Path # ✅ Path fix ke liye zaroori

# --- 1. ADVANCED DATA GENERATION (Covering ALL 51 Disease Types) ---
def generate_comprehensive_data(n_samples=10000):
    np.random.seed(42)
    
    # Weather Variables (Randomly Generated based on nature)
    temperature = np.random.uniform(5, 45, n_samples)  # 5°C to 45°C
    humidity = np.random.uniform(20, 100, n_samples)   # 20% to 100%
    rainfall = np.random.choice([0, 1], size=n_samples, p=[0.7, 0.3]) # Rain: 0=No, 1=Yes
    
    risk_categories = []
    
    # --- THE CORE LOGIC (Mapping 51 Diseases to 5 Weather Conditions) ---
    for t, h, r in zip(temperature, humidity, rainfall):
        
        # 1. Fungal Blight Risk (Tomato/Potato Late Blight, Downy Mildew)
        # Condition: Thand (10-24°C) + Bahut Nami (>85%)
        if 10 <= t <= 24 and h > 85:
            risk_categories.append("Cold_Wet_Risk")
            
        # 2. Bacterial/Rot Risk (Grape Rot, Bacterial Spots, Citrus Greening)
        # Condition: Garmi (28-38°C) + Chipchipa Humidity (>70%)
        elif 28 <= t <= 38 and h > 70:
            risk_categories.append("Warm_Humid_Risk")
            
        # 3. Powdery Mildew Risk (Apple/Cherry/Squash/Grape Mildew)
        # Condition: Moderate Temp (20-30°C) + Kam Nami (40-60%)
        elif 20 <= t <= 30 and 40 <= h <= 60:
            risk_categories.append("Moderate_Dry_Risk")
            
        # 4. Rust & Scab Risk (Corn/Wheat/Apple Rust, Apple Scab)
        # Condition: Moderate Temp + Baarish (Rain is the trigger)
        elif 15 <= t <= 28 and r == 1:
            risk_categories.append("Rainy_Risk")
            
        # 5. Viral/Pest Risk (Mosaic Virus, Spider Mites)
        # Condition: Bahut Garmi (>35°C) + Dry (Stress conditions for plant)
        elif t > 35 and h < 50:
            risk_categories.append("High_Heat_Risk")
            
        # Safe Condition
        else:
            risk_categories.append("No_Risk")
            
    df = pd.DataFrame({
        'temperature': temperature,
        'humidity': humidity,
        'rainfall': rainfall,
        'prediction': risk_categories
    })
    
    return df

# --- 2. TRAIN MODEL ---
print("🌱 Generating Dataset covering 51 Disease conditions...")
df = generate_comprehensive_data()



X = df[['temperature', 'humidity', 'rainfall']]
y = df['prediction']

# Split for validation (Optional, good for checking accuracy)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("🧠 Training Random Forest Model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Check Accuracy
acc = accuracy_score(y_test, model.predict(X_test))
print(f"✅ Model Accuracy: {acc * 100:.2f}%")

# --- 3. SAVE MODEL (CORRECTED PATH LOGIC) ---
# Current file location: AGROGUARD/ml/scripts/train_weather_model.py
current_dir = Path(__file__).resolve().parent 

# Go up one level to 'ml', then into 'models'
# Target: AGROGUARD/ml/models/
models_dir = current_dir.parent / "models"

# Create folder if it doesn't exist
models_dir.mkdir(parents=True, exist_ok=True)

model_path = models_dir / "weather_risk_model.pkl"
joblib.dump(model, model_path)

print(f"💾 Universal Weather Model Saved at: {model_path}")

# --- 4. TEST PREDICTION ---
print("\n🔍 Testing Logic:")
print("Test 1 (Cold+Wet) ->", model.predict([[15, 90, 0]])[0]) # Expect: Cold_Wet_Risk (Blight)
print("Test 2 (Hot+Humid) ->", model.predict([[35, 75, 0]])[0]) # Expect: Warm_Humid_Risk (Rot)