# backend/build_knowledge_base.py

import json
import time
import sys
from pathlib import Path

# Add 'app' to python path so we can import from it
sys.path.append(str(Path(__file__).parent))

from app.ml.llm_provider import query_llm 

# The 51 classes your YOLO model detects
DISEASE_CLASSES = [
    "Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust", "Apple___healthy",
    "Blueberry___healthy", "Cherry_(including_sour)___Powdery_mildew", "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot", "Corn_(maize)___Common_rust_", 
    "Corn_(maize)___Northern_Leaf_Blight", "Corn_(maize)___healthy", "Grape___Black_rot", 
    "Grape___Esca_(Black_Measles)", "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", "Grape___healthy", 
    "Orange___Haunglongbing_(Citrus_greening)", "Peach___Bacterial_spot", "Peach___healthy", 
    "Pepper,_bell___Bacterial_spot", "Pepper,_bell___healthy", "Potato___Early_blight", 
    "Potato___Late_blight", "Potato___healthy", "Raspberry___healthy", "Soybean___healthy", 
    "Squash___Powdery_mildew", "Strawberry___Leaf_scorch", "Strawberry___healthy", 
    "Tomato___Bacterial_spot", "Tomato___Early_blight", "Tomato___Late_blight", "Tomato___Leaf_Mold", 
    "Tomato___Septoria_leaf_spot", "Tomato___Spider_mites Two-spotted_spider_mite", 
    "Tomato___Target_Spot", "Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato___Tomato_mosaic_virus", 
    "Tomato___healthy", "bacterial_leaf_blight", "bacterial_leaf_streak", "bacterial_panicle_blight", 
    "blast", "brown_spot", "dead_heart", "downy_mildew", "hispa", "normal", "tungro", 
    "Cassava CB (Cassava Blight)", "Cassava CM (Cassava Mosaic)", "Cassava Healthy leaf"
]

def generate_disease_info(disease_name):
    """Asks the LLM for structured data about a disease"""
    
    if "healthy" in disease_name.lower() or "normal" in disease_name.lower():
        return {
            "description": "The plant looks healthy and vigorous.",
            "symptoms": ["No signs of disease", "Green leaves"],
            "treatment": ["Maintain regular watering", "Monitor for pests"],
            "prevention": ["Good field hygiene", "Proper spacing"]
        }

    print(f"🤖 Asking AI about: {disease_name}...")
    
    prompt = f"""
    Provide agricultural advice for the plant disease: "{disease_name}".
    Return ONLY a JSON object with this exact structure (no markdown, no extra text):
    {{
        "description": "Short 1-sentence description",
        "symptoms": ["Symptom 1", "Symptom 2"],
        "treatment": ["Specific chemical cure", "Organic cure"],
        "prevention": ["Prevention tip 1", "Prevention tip 2"]
    }}
    Make the advice practical for a farmer.
    """

    try:
        response = query_llm(prompt)
        
        # Handle different response types
        if isinstance(response, dict):
            text_response = response.get("text", "")
        else:
            text_response = str(response)

        # Clean up markdown
        text_response = text_response.replace("```json", "").replace("```", "").strip()
        
        return json.loads(text_response)
    except Exception as e:
        print(f"❌ Failed to generate for {disease_name}: {e}")
        # Keep the fallback so we can retry later
        return {
            "description": "Information temporarily unavailable.",
            "treatment": ["USE_API_FALLBACK"] 
        }

def main():
    # Correct path based on your screenshot: backend/../ml/knowledge_base/diseases.json
    kb_path = Path(__file__).parent.parent / "ml/knowledge_base/diseases.json"
    
    print(f"📂 Targeting Knowledge Base at: {kb_path}")

    # Load existing data
    if kb_path.exists():
        with open(kb_path, "r") as f:
            data = json.load(f)
    else:
        print("⚠️ File not found, creating new...")
        data = {}

    print(f"🚀 Starting Knowledge Base Enrichment for {len(DISEASE_CLASSES)} diseases...")

    for disease in DISEASE_CLASSES:
        # Skip if we already have good data
        if disease in data:
            current_treatment = data[disease].get("treatment", [])
            # Checks if it's a string "USE_API_FALLBACK" or a list containing it
            is_fallback = False
            if isinstance(current_treatment, list) and "USE_API_FALLBACK" in current_treatment:
                is_fallback = True
            elif isinstance(current_treatment, str) and "USE_API_FALLBACK" in current_treatment:
                is_fallback = True
                
            if not is_fallback:
                print(f"✅ Skipping {disease} (Already has data)")
                continue

        # Generate new data
        info = generate_disease_info(disease)
        data[disease] = info
        
        # Save progress immediately
        with open(kb_path, "w") as f:
            json.dump(data, f, indent=4)
            
        # Sleep to be nice to the API
        time.sleep(1) 

    print(f"🎉 Knowledge Base built successfully!")

if __name__ == "__main__":
    main()