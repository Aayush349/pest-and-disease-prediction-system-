import json, time, sys
from pathlib import Path
from collections import defaultdict

# Add 'app' to python path so we can import from it
sys.path.append(str(Path(__file__).parent))
from app.ml.llm_provider import query_llm 

# --- COMPLETE MASTER CLASS LIST (100% Coverage of Both Models) ---
RAW_CLASSES = [
    # Model 1 Classes
    'Apple_Apple_scab', 'Apple_Black_rot', 'Apple_Cedar_apple_rust', 'Apple_healthy',
    'Blueberry_healthy', 'Cherry_healthy', 'Cherry_Powdery_mildew',
    'Corn_Cercospora_leaf_spot_Gray_leaf_spot', 'Corn_Common_rust', 'Corn_healthy',
    'Corn_Northern_Leaf_Blight', 'Grape_Black_rot', 'Grape_Esca_(Black_Measles)',
    'Grape_healthy', 'Grape_Leaf_blight_(Isariopsis_Leaf_Spot)',
    'Orange_Haunglongbing_(Citrus_greening)', 'Peach_Bacterial_spot', 'Peach_healthy',
    'Pepper_bell_Bacterial_spot', 'Pepper_bell_healthy', 'Potato_Early_blight',
    'Potato_healthy', 'Potato_Late_blight', 'Raspberry_healthy', 'Soybean_healthy',
    'Squash_Powdery_mildew', 'Strawberry_healthy', 'Strawberry_Leaf_scorch',
    'Tomato_Bacterial_spot', 'Tomato_Early_blight', 'Tomato_healthy',
    'Tomato_Late_blight', 'Tomato_Leaf_Mold', 'Tomato_Septoria_leaf_spot',
    'Tomato_Spider_mites_Two-spotted_spider_mite', 'Tomato_Target_Spot', 
    'Tomato_Tomato_mosaic_virus', 'Tomato_Tomato_Yellow_Leaf_Curl_virus',
    
    # Model 2 Classes
    'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust',
    'Apple___healthy', 'Blueberry___healthy', 'Cassava CB (Cassava Blight)',
    'Cassava CM (Cassava Mosaic)', 'Cassava Healthy leaf',
    'Cherry_(including_sour)___Powdery_mildew', 'Cherry_(including_sour)___healthy',
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Corn_(maize)___Common_rust_',
    'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy',
    'Grape___Black_rot', 'Grape___Esca_(Black_Measles)',
    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy',
    'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot',
    'Peach___healthy', 'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy',
    'Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy',
    'Raspberry___healthy', 'Soybean___healthy', 'Squash___Powdery_mildew',
    'Strawberry___Leaf_scorch', 'Strawberry___healthy', 'Tomato___Bacterial_spot',
    'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold',
    'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite',
    'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
    'Tomato___Tomato_mosaic_virus', 'Tomato___healthy',
    
    # Additional rice diseases
    'bacterial_leaf_blight', 'bacterial_leaf_streak', 'bacterial_panicle_blight',
    'blast', 'brown_spot', 'dead_heart', 'downy_mildew', 'hispa', 'normal', 'tungro'
]

LANGUAGES = ["en", "hi", "mr", "kn", "ta", "te"]

def normalize_key(name):
    """Create canonical key while preserving original labels separately"""
    return name.replace("___", "_").replace(" ", "_").replace("(", "").replace(")", "").replace(",", "").lower()

def is_healthy_plant(disease_name):
    """Check if this is a healthy plant (no disease)"""
    lower_name = disease_name.lower()
    return 'healthy' in lower_name or 'normal' in lower_name

def create_healthy_plant_response(plant_name):
    """Create response for HEALTHY plants - NO TREATMENT, ONLY MAINTENANCE"""
    # Clean plant name for display
    clean_plant = plant_name.replace('_', ' ').title()
    
    return {
        "raw_labels": [],
        "description": {
            "en": f"✅ {clean_plant} plant is healthy and disease-free. No treatment required.",
            "hi": f"✅ {clean_plant} का पौधा स्वस्थ और रोग-मुक्त है। किसी उपचार की आवश्यकता नहीं है।",
            "mr": f"✅ {clean_plant} वनस्पती निरोगी आणि रोगमुक्त आहे. कोणत्याही उपचाराची गरज नाही.",
            "kn": f"✅ {clean_plant} ಸಸ್ಯ ಆರೋಗ್ಯಕರ ಮತ್ತು ರೋಗ-ಮುಕ್ತವಾಗಿದೆ. ಯಾವುದೇ ಚಿಕಿತ್ಸೆ ಅಗತ್ಯವಿಲ್ಲ.",
            "ta": f"✅ {clean_plant} தாவரம் ஆரோக்கியமான மற்றும் நோய் இல்லாதது. எந்த சிகிச்சையும் தேவையில்லை.",
            "te": f"✅ {clean_plant} మొక్క ఆరోగ్యకరమైన మరియు వ్యాధి-రహితంగా ఉంది. ఎలాంటి చికిత్స అవసరం లేదు."
        },
        "treatment": {
            "en": [
                "🎯 NO TREATMENT NEEDED - Plant is healthy",
                "Continue regular organic fertilization schedule",
                "Maintain optimal watering practices",
                "Monitor for early signs of any issues"
            ],
            "hi": [
                "🎯 किसी उपचार की आवश्यकता नहीं - पौधा स्वस्थ है",
                "नियमित जैविक उर्वरक कार्यक्रम जारी रखें",
                "इष्टतम पानी देने की प्रथाएं बनाए रखें",
                "किसी भी समस्या के शुरुआती संकेतों की निगरानी करें"
            ],
            "mr": [
                "🎯 कोणत्याही उपचाराची गरज नाही - वनस्पती निरोगी आहे",
                "नियमित जैविक खत देण्याचे शेड्यूल सुरू ठेवा",
                "इष्टतम पाणी देण्याच्या पद्धती राखा",
                "कोणत्याही समस्येच्या लवकर लक्षणांसाठी निरीक्षण करा"
            ],
            "kn": [
                "🎯 ಯಾವುದೇ ಚಿಕಿತ್ಸೆ ಅಗತ್ಯವಿಲ್ಲ - ಸಸ್ಯ ಆರೋಗ್ಯಕರವಾಗಿದೆ",
                "ನಿಯಮಿತ ಸಾವಯವ ಗೊಬ್ಬರ ಶೆಡ್ಯೂಲ್ ಮುಂದುವರಿಸಿ",
                "ಸೂಕ್ತ ನೀರುಣಿಸುವ ಅಭ್ಯಾಸಗಳನ್ನು ಕಾಪಾಡಿಕೊಳ್ಳಿ",
                "ಯಾವುದೇ ಸಮಸ್ಯೆಯ ಆರಂಭಿಕ ಚಿಹ್ನೆಗಳನ್ನು ಗಮನಿಸಿ"
            ],
            "ta": [
                "🎯 எந்த சிகிச்சையும் தேவையில்லை - தாவரம் ஆரோக்கியமானது",
                "தொடர்ந்து கரிம உரமிடும் அட்டவணையைத் தொடரவும்",
                "மிகவும் உகந்த நீர்ப்பாசன முறைகளைப் பராமரிக்கவும்",
                "எந்தவொரு பிரச்சினைகளின் ஆரம்ப அறிகுறிகளையும் கண்காணிக்கவும்"
            ],
            "te": [
                "🎯 ఎలాంటి చికిత్స అవసరం లేదు - మొక్క ఆరోగ్యకరంగా ఉంది",
                "నియమిత సేంద్రియ ఎరువు షెడ్యూల్ కొనసాగించండి",
                "సరైన నీటిపోయే పద్ధతులను నిర్వహించండి",
                "ఏదైనా సమస్యల ప్రారంభ సంకేతాల కోసం పర్యవేక్షించండి"
            ]
        },
        "prevention": {
            "en": [
                "Continue current organic farming practices",
                "Maintain soil health with compost and mulch",
                "Practice crop rotation to prevent future diseases",
                "Regular inspection for early problem detection"
            ],
            "hi": [
                "वर्तमान जैविक खेती प्रथाओं को जारी रखें",
                "खाद और गीली घास से मिट्टी का स्वास्थ्य बनाए रखें",
                "भविष्य की बीमारियों को रोकने के लिए फसल चक्र का अभ्यास करें",
                "शुरुआती समस्या का पता लगाने के लिए नियमित निरीक्षण"
            ],
            "mr": [
                "सध्याच्या जैविक शेती पद्धती सुरू ठेवा",
                "कंपोस्ट आणि मल्चसह मातीचे आरोग्य राखा",
                "भविष्यातील रोगांपासून बचाव करण्यासाठी पिक फेरपालटाची सवय करा",
                "लवकर समस्येचा शोध घेण्यासाठी नियमित तपासणी"
            ],
            "kn": [
                "ಪ್ರಸ್ತುತ ಸಾವಯವ ಕೃಷಿ ಅಭ್ಯಾಸಗಳನ್ನು ಮುಂದುವರಿಸಿ",
                "ಕೊಪೊಸ್ಟ್ ಮತ್ತು ಗುಂಡಿಯೊಂದಿಗೆ ಮಣ್ಣಿನ ಆರೋಗ್ಯವನ್ನು ಕಾಪಾಡಿಕೊಳ್ಳಿ",
                "ಭವಿಷ್ಯದ ರೋಗಗಳನ್ನು ತಡೆಗಟ್ಟಲು ಬೆಳೆ ಪರ್ಯಾಯ ಅಭ್ಯಾಸ ಮಾಡಿ",
                "ಆರಂಭಿಕ ಸಮಸ್ಯೆಯನ್ನು ಪತ್ತೆಹಚ್ಚಲು ನಿಯಮಿತ ಪರಿಶೀಲನೆ"
            ],
            "ta": [
                "தற்போதைய கரிம வேளாண்மை நடைமுறைகளைத் தொடரவும்",
                "குப்பை உரம் மற்றும் பூச்சுடன் மண்ணின் ஆரோக்கியத்தை பராமரிக்கவும்",
                "எதிர்கால நோய்களைத் தடுக்க பயிர் சுழற்சியை பின்பற்றவும்",
                "ஆரம்ப பிரச்சினை கண்டறிதலுக்கு தினமும் ஆய்வு"
            ],
            "te": [
                "ప్రస్తుత సేంద్రియ వ్యవసాయ పద్ధతులను కొనసాగించండి",
                "కంపోస్ట్ మరియు మల్చ్తో నేల ఆరోగ్యం నిర్వహించండి",
                "భవిష్యత్ వ్యాధులను నిరోధించడానికి పంట భ్రమణం చేయండి",
                "ప్రారంభ సమస్య గుర్తింపు కోసం నియమిత తనిఖీ"
            ]
        }
    }

def generate_multilingual_info(disease_name, existing_raw_labels=None):
    """Generate multilingual info - DIFFERENT LOGIC FOR HEALTHY vs DISEASED"""
    
    # Check if this is a healthy plant
    if is_healthy_plant(disease_name):
        print(f"🌿 Healthy plant detected: {disease_name} - Generating MAINTENANCE info...")
        # Extract plant name (remove 'healthy' suffix)
        plant_name = disease_name.replace('_healthy', '').replace('_normal', '').replace('healthy', '').replace('normal', '').strip('_')
        response = create_healthy_plant_response(plant_name)
    
    else:
        print(f"🤖 Generating LLM advisory for {disease_name}")
        
        clean_name = disease_name.replace("_", " ").replace("___", " ").title()
        
        prompt = f"""
You are an expert Indian agricultural scientist.

For the plant disease: "{clean_name}"

Generate advice in ALL these languages: en, hi, mr, kn, ta, te

STRICT RULES:
1. Treatment MUST contain EXACTLY 4 steps:
   - Step 1–2: ORGANIC / BIO control (with product names)
   - Step 3–4: CHEMICAL / PESTICIDE control (with product names)
2. Mention real fungicide / pesticide names used in India
3. Organic must come BEFORE chemical
4. Keep steps short (1 line each)

Return ONLY valid JSON in this format:

{{
  "description": {{
    "en": "...",
    "hi": "...",
    "mr": "...",
    "kn": "...",
    "ta": "...",
    "te": "..."
  }},
  "treatment": {{
    "en": ["...", "...", "...", "..."],
    "hi": ["...", "...", "...", "..."],
    "mr": ["...", "...", "...", "..."],
    "kn": ["...", "...", "...", "..."],
    "ta": ["...", "...", "...", "..."],
    "te": ["...", "...", "...", "..."]
  }},
  "prevention": {{
    "en": ["...", "...", "..."],
    "hi": ["...", "...", "..."],
    "mr": ["...", "...", "..."],
    "kn": ["...", "...", "..."],
    "ta": ["...", "...", "..."],
    "te": ["...", "...", "..."]
  }}
}}
"""
        
        try:
            llm_res = query_llm(prompt)
            text = llm_res.get("text", str(llm_res)).strip()
            
            if "```" in text:
                text = text.replace("```json", "").replace("```", "").strip()
            
            response = json.loads(text)
            
            # Ensure all languages are present
            for field in ["description", "treatment", "prevention"]:
                if field not in response:
                    # Simple fallback if LLM doesn't provide all fields
                    fallback_desc = {
                        "en": f"Detailed information about {clean_name}",
                        "hi": f"{clean_name} के बारे में विस्तृत जानकारी",
                        "mr": f"{clean_name} बद्दल तपशीलवर्ण माहिती",
                        "kn": f"{clean_name} ಬಗ್ಗೆ ವಿವರವಾದ ಮಾಹಿತಿ",
                        "ta": f"{clean_name} பற்றிய விரிவான தகவல்",
                        "te": f"{clean_name} గురించి వివరణాత్మక సమాచారం"
                    }
                    response[field] = fallback_desc if field == "description" else {"en": ["Info coming soon"], "hi": ["जानकारी जल्द आएगी"], "mr": ["माहिती लवकर येईल"], "kn": ["ಮಾಹಿತಿ ಶೀಘ್ರದಲ್ಲೇ ಬರಲಿದೆ"], "ta": ["தகவல் விரைவில் வரும்"], "te": ["సమాచారం త్వరలో వస్తుంది"]}
                
                # Ensure all 6 languages exist
                for lang in LANGUAGES:
                    if lang not in response[field]:
                        if field == "description":
                            response[field][lang] = f"Information about {clean_name}"
                        elif field == "treatment":
                            response[field][lang] = ["Step 1: Organic remedy", "Step 2: Bio-control", "Step 3: Chemical 1", "Step 4: Chemical 2"]
                        else:  # prevention
                            response[field][lang] = ["Preventive measure 1", "Preventive measure 2", "Preventive measure 3"]
        
        except Exception as e:
            print(f"⚠️ LLM error for {disease_name}: {e}")
            # Simple fallback
            response = {
                "description": {
                    "en": f"Information about {clean_name}",
                    "hi": f"{clean_name} के बारे में जानकारी",
                    "mr": f"{clean_name} बद्दल माहिती",
                    "kn": f"{clean_name} ಬಗ್ಗೆ ಮಾಹಿತಿ",
                    "ta": f"{clean_name} பற்றிய தகவல்",
                    "te": f"{clean_name} గురించి సమాచారం"
                },
                "treatment": {
                    "en": ["Step 1: Neem oil spray", "Step 2: Trichoderma application", "Step 3: Mancozeb fungicide", "Step 4: Copper oxychloride"],
                    "hi": ["चरण 1: नीम तेल स्प्रे", "चरण 2: ट्राइकोडर्मा अनुप्रयोग", "चरण 3: मैंकोजेब कवकनाशी", "चरण 4: कॉपर ऑक्सीक्लोराइड"],
                    "mr": ["चरण 1: निंब तेल स्प्रे", "चरण 2: ट्रायकोडर्मा अनुप्रयोग", "चरण 3: मॅन्कोझेब फंगिसायड", "चरण 4: कॉपर ऑक्सीक्लोराईड"],
                    "kn": ["ಹಂತ 1: ನೀಮ್ ತೈಲ ಸಿಂಪಡಣೆ", "ಹಂತ 2: ಟ್ರೈಕೋಡರ್ಮಾ ಅನ್ವಯ", "ಹಂತ 3: ಮ್ಯಾಂಕೋಜೆಬ್ ಫಂಗಿಸೈಡ್", "ಹಂತ 4: ತಾಮ್ರ ಆಕ್ಸಿಕ್ಲೋರೈಡ್"],
                    "ta": ["படி 1: வேப்ப எண்ணெய் தெளிப்பு", "படி 2: டிரைக்கோடெர்மா பயன்பாடு", "படி 3: மேங்கோசெப் பூஞ்சைக்கொல்லி", "படி 4: தாமிர ஆக்சிக்ளோரைடு"],
                    "te": ["దశ 1: వేప నూనె స్ప్రే", "దశ 2: ట్రైకోడెర్మా అప్లికేషన్", "దశ 3: మ్యాన్కోజెబ్ ఫంగిసైడ్", "దశ 4: రాగి ఆక్సిక్లోరైడ్"]
                },
                "prevention": {
                    "en": ["Crop rotation", "Proper spacing", "Regular monitoring"],
                    "hi": ["फसल चक्र", "उचित दूरी", "नियमित निगरानी"],
                    "mr": ["पिक फेरपालट", "योग्य अंतर", "नियमित निरीक्षण"],
                    "kn": ["ಬೆಳೆ ಪರ್ಯಾಯ", "ಸರಿಯಾದ ಅಂತರ", "ನಿಯಮಿತ ಮೇಲ್ವಿಚಾರಣೆ"],
                    "ta": ["பயிர் சுழற்சி", "சரியான இடைவெளி", "தினமும் கண்காணிப்பு"],
                    "te": ["పంట భ్రమణం", "సరైన అంతరం", "నియమిత పర్యవేక్షణ"]
                }
            }
    
    # raw labels attach
    response["raw_labels"] = existing_raw_labels or []
    
    return response

def check_language_completeness(entry):
    """Check if all 6 languages are present in all fields"""
    if not entry:
        return False
    
    required_fields = ["description", "treatment", "prevention"]
    
    for field in required_fields:
        if field not in entry:
            return False
        
        # Check all languages exist in this field
        if isinstance(entry[field], dict):
            for lang in LANGUAGES:
                if lang not in entry[field]:
                    return False
                # Check content is not empty or placeholder
                content = entry[field][lang]

                # Case 1: description (string)
                if isinstance(content, str):
                    if content.strip() == "":
                        return False

                # Case 2: treatment / prevention (list)
                elif isinstance(content, list):
                    if len(content) == 0:
                        return False
                    # optional: check empty strings inside list
                    if all((not isinstance(i, str) or i.strip() == "") for i in content):
                        return False

                else:
                    return False
        else:
            return False
    
    # Check raw_labels exist
    if "raw_labels" not in entry:
        return False
    
    return True

def main():
    kb_path = Path(__file__).parent.parent / "ml/knowledge_base/diseases.json"
    data = {}
    
    # Load existing data
    if kb_path.exists():
        try:
            with open(kb_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"📖 Loaded existing KB with {len(data)} entries")
        except Exception as e:
            print(f"⚠️ Could not load existing KB: {e}. Starting fresh...")
            data = {}
    else:
        print("📝 Creating new Knowledge Base file...")
    
    # Group raw labels by canonical key
    from collections import defaultdict
    key_to_raw = defaultdict(list)
    
    print(f"\n🔍 Processing {len(RAW_CLASSES)} raw labels...")
    
    for raw_name in RAW_CLASSES:
        key = normalize_key(raw_name)
        key_to_raw[key].append(raw_name)
    
    print(f"📊 Found {len(key_to_raw)} unique diseases after normalization")
    
    # Process each canonical disease
    for i, (key, raw_labels) in enumerate(key_to_raw.items()):
        print(f"\n[{i+1}/{len(key_to_raw)}] Processing: {key}")
        print(f"   📍 Raw labels: {', '.join(raw_labels[:3])}{'...' if len(raw_labels) > 3 else ''}")
        
        # Check if healthy or diseased
        if is_healthy_plant(key):
            print(f"   🌿 STATUS: HEALTHY PLANT - Will generate MAINTENANCE info")
        else:
            print(f"   🦠 STATUS: DISEASED PLANT - Will generate 2 ORGANIC + 2 CHEMICAL treatment")
        
        needs_update = False
        
        if key not in data:
            needs_update = True
            print(f"   ➕ New entry, will generate AI info")
        elif not check_language_completeness(data[key]):
            needs_update = True
            print(f"   🔄 Incomplete/missing languages, will regenerate")
        else:
            # Check if raw_labels need updating
            existing_raw = set(data[key].get("raw_labels", []))
            new_raw = set(raw_labels)
            if not new_raw.issubset(existing_raw):
                # Merge raw labels
                data[key]["raw_labels"] = list(existing_raw.union(new_raw))
                needs_update = True
                print(f"   🔄 Adding {len(new_raw - existing_raw)} new raw labels")
        
        if needs_update:
            # Use the first raw label as display name
            display_name = raw_labels[0]
            
            # Generate or regenerate info with CORRECT LOGIC
            data[key] = generate_multilingual_info(display_name, raw_labels)
            
            # Save incrementally
            with open(kb_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            print(f"   💾 Saved to KB")
            
            # Rate limiting (be nice to API)
            time.sleep(1.5)
        else:
            print(f"   ✅ Already complete in KB")
    
    # Final verification
    print(f"\n" + "="*50)
    print("🔍 FINAL VERIFICATION")
    print("="*50)
    
    incomplete = []
    for key, entry in data.items():
        if not check_language_completeness(entry):
            incomplete.append(key)
    
    if incomplete:
        print(f"⚠️ WARNING: {len(incomplete)} entries still incomplete")
        print("\nIncomplete entries:")
        for key in incomplete[:10]:
            print(f"   ❌ {key}")
        if len(incomplete) > 10:
            print(f"   ... and {len(incomplete) - 10} more")
        
        # Try to fix incomplete entries
        print(f"\n🔄 Attempting to fix incomplete entries...")
        fixed_count = 0
        for key in incomplete:
            if key in key_to_raw:
                print(f"   Fixing: {key}")
                display_name = key_to_raw[key][0]
                data[key] = generate_multilingual_info(display_name, key_to_raw[key])
                fixed_count += 1
                time.sleep(1.5)
        
        if fixed_count > 0:
            with open(kb_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"   ✅ Fixed {fixed_count} entries")
    else:
        print(f"✅ PERFECT! All {len(data)} entries have complete multilingual data!")
    
    # Final statistics
    print(f"\n" + "="*50)
    print("📊 KNOWLEDGE BASE STATISTICS")
    print("="*50)
    print(f"Total unique diseases: {len(data)}")
    
    # Count healthy vs diseased
    healthy_count = sum(1 for key in data if is_healthy_plant(key))
    diseased_count = len(data) - healthy_count
    print(f"🌿 Healthy plant entries: {healthy_count}")
    print(f"🦠 Diseased plant entries: {diseased_count}")
    
    # Verify treatment structure for first few diseased plants
    print(f"\n🔬 Sample verification of diseased plant treatments:")
    count = 0
    for key in data:
        if not is_healthy_plant(key) and count < 3:
            treatment = data[key].get("treatment", {}).get("en", [])
            print(f"   {key}: {len(treatment)} steps")
            if len(treatment) == 4:
                print(f"      ✅ Has 4 steps (2 organic + 2 chemical)")
            else:
                print(f"      ❌ Expected 4 steps, got {len(treatment)}")
            count += 1
    
    print(f"\nTotal raw labels processed: {len(RAW_CLASSES)}")
    print(f"Raw labels in KB: {sum(len(entry.get('raw_labels', [])) for entry in data.values())}")
    
    # Check coverage
    all_raw_in_kb = set()
    for entry in data.values():
        all_raw_in_kb.update(entry.get('raw_labels', []))
    
    missing_raw = set(RAW_CLASSES) - all_raw_in_kb
    if missing_raw:
        print(f"\n⚠️ WARNING: {len(missing_raw)} raw labels not in KB:")
        for label in sorted(list(missing_raw))[:5]:
            print(f"   - {label}")
        if len(missing_raw) > 5:
            print(f"   ... and {len(missing_raw) - 5} more")
    else:
        print(f"\n✅ 100% COVERAGE: All raw labels are in KB!")
    
    print(f"\n🎉 MASTER KNOWLEDGE BASE READY!")
    print(f"✅ Healthy plants: MAINTENANCE only")
    print(f"✅ Diseased plants: 2 ORGANIC + 2 CHEMICAL treatment")
    print(f"📍 Location: {kb_path.absolute()}")

if __name__ == "__main__":
    main()


# import json, time, sys
# from pathlib import Path
# from collections import defaultdict

# # Add 'app' to python path so we can import from it
# sys.path.append(str(Path(__file__).parent))
# from app.ml.llm_provider import query_llm 

# # --- COMPLETE MASTER CLASS LIST (100% Coverage of Both Models) ---
# RAW_CLASSES = [
#     # Model 1 Classes
#     'Apple_Apple_scab', 'Apple_Black_rot', 'Apple_Cedar_apple_rust', 'Apple_healthy',
#     'Blueberry_healthy', 'Cherry_healthy', 'Cherry_Powdery_mildew',
#     'Corn_Cercospora_leaf_spot_Gray_leaf_spot', 'Corn_Common_rust', 'Corn_healthy',
#     'Corn_Northern_Leaf_Blight', 'Grape_Black_rot', 'Grape_Esca_(Black_Measles)',
#     'Grape_healthy', 'Grape_Leaf_blight_(Isariopsis_Leaf_Spot)',
#     'Orange_Haunglongbing_(Citrus_greening)', 'Peach_Bacterial_spot', 'Peach_healthy',
#     'Pepper_bell_Bacterial_spot', 'Pepper_bell_healthy', 'Potato_Early_blight',
#     'Potato_healthy', 'Potato_Late_blight', 'Raspberry_healthy', 'Soybean_healthy',
#     'Squash_Powdery_mildew', 'Strawberry_healthy', 'Strawberry_Leaf_scorch',
#     'Tomato_Bacterial_spot', 'Tomato_Early_blight', 'Tomato_healthy',
#     'Tomato_Late_blight', 'Tomato_Leaf_Mold', 'Tomato_Septoria_leaf_spot',
#     'Tomato_Spider_mites_Two-spotted_spider_mite', 'Tomato_Target_Spot', 
#     'Tomato_Tomato_mosaic_virus', 'Tomato_Tomato_Yellow_Leaf_Curl_virus',
    
#     # Model 2 Classes
#     'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust',
#     'Apple___healthy', 'Blueberry___healthy', 'Cassava CB (Cassava Blight)',
#     'Cassava CM (Cassava Mosaic)', 'Cassava Healthy leaf',
#     'Cherry_(including_sour)___Powdery_mildew', 'Cherry_(including_sour)___healthy',
#     'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Corn_(maize)___Common_rust_',
#     'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy',
#     'Grape___Black_rot', 'Grape___Esca_(Black_Measles)',
#     'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy',
#     'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot',
#     'Peach___healthy', 'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy',
#     'Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy',
#     'Raspberry___healthy', 'Soybean___healthy', 'Squash___Powdery_mildew',
#     'Strawberry___Leaf_scorch', 'Strawberry___healthy', 'Tomato___Bacterial_spot',
#     'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold',
#     'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite',
#     'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
#     'Tomato___Tomato_mosaic_virus', 'Tomato___healthy',
    
#     # Additional rice diseases
#     'bacterial_leaf_blight', 'bacterial_leaf_streak', 'bacterial_panicle_blight',
#     'blast', 'brown_spot', 'dead_heart', 'downy_mildew', 'hispa', 'normal', 'tungro'
# ]

# LANGUAGES = ["en", "hi", "mr", "kn", "ta", "te"]

# def normalize_key(name):
#     """Create canonical key while preserving original labels separately"""
#     # Replace multiple underscores with single, remove spaces, parentheses, commas
#     return name.replace("___", "_").replace(" ", "_").replace("(", "").replace(")", "").replace(",", "").lower()

# def create_fallback_response(disease_name):
#     """Create complete multilingual fallback with all 6 languages - ORGANIC FIRST"""
#     # Extract plant name for better messages
#     plant_name = disease_name.split('_')[0] if '_' in disease_name else disease_name
    
#     return {
#         "raw_labels": [],  # Will be populated later
#         "description": {
#             "en": f"Diagnosis: {disease_name.replace('_', ' ').title()}. Loading organic remedies for {plant_name}...",
#             "hi": f"निदान: {disease_name.replace('_', ' ').title()}। {plant_name} के लिए जैविक उपचार लोड हो रहा है...",
#             "mr": f"निदान: {disease_name.replace('_', ' ').title()}। {plant_name} साठी जैविक उपाय लोड होत आहेत...",
#             "kn": f"ರೋಗ ನಿರ್ಣಯ: {disease_name.replace('_', ' ').title()}। {plant_name} ಗಾಗಿ ಸಾವಯವ ಪರಿಹಾರಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...",
#             "ta": f"நோய் நிர்ணயம்: {disease_name.replace('_', ' ').title()}। {plant_name} க்கான கரிம மருத்துவங்கள் ஏற்றப்படுகின்றன...",
#             "te": f"వ్యాధి నిర్ధారణ: {disease_name.replace('_', ' ').title()}। {plant_name} కోసం సేంద్రియ మందులు లోడ్ అవుతున్నాయి..."
#         },
#         "treatment": {
#             "en": [
#                 f"Step 1 (Organic): Use Neem Oil spray on {plant_name} leaves",
#                 "Step 2 (Biological): Apply Trichoderma viride to soil",
#                 "Step 3 (Management): Remove infected parts carefully",
#                 "Step 4 (Severe Case): Chemical fungicide (Use only if severe)"
#             ],
#             "hi": [
#                 f"चरण 1 (जैविक): {plant_name} की पत्तियों पर नीम तेल का छिड़काव करें",
#                 "चरण 2 (जैविक): मिट्टी में ट्राइकोडर्मा विराइड लगाएं",
#                 "चरण 3 (प्रबंधन): संक्रमित भागों को सावधानी से हटाएं",
#                 "चरण 4 (गंभीर): रासायनिक कवकनाशी (केवल गंभीर स्थिति में)"
#             ],
#             "mr": [
#                 f"चरण 1 (जैविक): {plant_name} च्या पानांवर निंब तेलाचा फवारा करा",
#                 "चरण 2 (जैविक): मातीत ट्रायकोडर्मा व्हिराईड लावा",
#                 "चरण 3 (व्यवस्थापन): संसर्ग झालेले भाग काळजीपूर्वक काढा",
#                 "चरण 4 (गंभीर): रासायनिक फंगिसायड (केवळ गंभीर प्रकरणात)"
#             ],
#             "kn": [
#                 f"ಹಂತ 1 (ಸಾವಯವ): {plant_name} ಎಲೆಗಳ ಮೇಲೆ ನೀಮ್ ತೈಲ ಸಿಂಪಡಿಸಿ",
#                 "ಹಂತ 2 (ಜೈವಿಕ): ಮಣ್ಣಿಗೆ ಟ್ರೈಕೋಡರ್ಮಾ ವಿರೈಡ್ ಅನ್ನು ಲಗತ್ತಿಸಿ",
#                 "ಹಂತ 3 (ನಿರ್ವಹಣೆ): ಸೋಂಕು ಹರಡಿದ ಭಾಗಗಳನ್ನು ಎಚ್ಚರಿಕೆಯಿಂದ ತೆಗೆದುಹಾಕಿ",
#                 "ಹಂತ 4 (ತೀವ್ರ): ರಾಸಾಯನಿಕ ಫಂಗಿಸೈಡ್ (ತೀವ್ರವಾಗಿದ್ದರೆ ಮಾತ್ರ)"
#             ],
#             "ta": [
#                 f"படி 1 (கரிம): {plant_name} இலைகளில் வேப்ப எண்ணெய் தெளிக்கவும்",
#                 "படி 2 (உயிரியல்): மண்ணில் டிரைக்கோடெர்மா விரிடே பயன்படுத்தவும்",
#                 "படி 3 (மேலாண்மை): பாதிக்கப்பட்ட பகுதிகளை கவனமாக அகற்றவும்",
#                 "படி 4 (கடுமையான): ரசாயன பூஞ்சைக்கொல்லி (கடுமையான நிலையில் மட்டும்)"
#             ],
#             "te": [
#                 f"దశ 1 (సేంద్రియ): {plant_name} ఆకులపై వేప నూనె స్ప్రే చేయండి",
#                 "దశ 2 (జీవ): నేలలో ట్రైకోడెర్మా వైరైడ్ వర్తించండి",
#                 "దశ 3 (నిర్వహణ): సోకిన భాగాలను జాగ్రత్తగా తీసివేయండి",
#                 "దశ 4 (తీవ్రమైన): రసాయన ఫంగిసైడ్ (తీవ్రంగా ఉన్నప్పుడు మాత్రమే)"
#             ]
#         },
#         "prevention": {
#             "en": [
#                 "Ensure proper soil drainage and aeration",
#                 "Practice crop rotation with legumes",
#                 "Use disease-resistant native varieties",
#                 "Apply organic compost regularly for soil health"
#             ],
#             "hi": [
#                 "उचित मिट्टी जल निकासी और वायुसंचार सुनिश्चित करें",
#                 "फलियों के साथ फसल चक्र का अभ्यास करें",
#                 "रोग प्रतिरोधी देशी किस्मों का उपयोग करें",
#                 "मिट्टी के स्वास्थ्य के लिए नियमित रूप से जैविक खाद डालें"
#             ],
#             "mr": [
#                 "योग्य मातीचे ड्रेनेज आणि वातीकरण सुनिश्चित करा",
#                 "शेंगदाण्यांसह पिक फेरपालटाची सवय करा",
#                 "रोगप्रतिकारक स्थानिक प्रजाती वापरा",
#                 "मातीच्या आरोग्यासाठी नियमितपणे जैविक कंपोस्ट लावा"
#             ],
#             "kn": [
#                 "ಸರಿಯಾದ ಮಣ್ಣಿನ ಒಳಚರಂಡಿ ಮತ್ತು ಗಾಳಿಯಾಟವನ್ನು ಖಚಿತಪಡಿಸಿ",
#                 "ಕಾಳುಗಳೊಂದಿಗೆ ಬೆಳೆ ಪರ್ಯಾಯ ಅಭ್ಯಾಸ ಮಾಡಿ",
#                 "ರೋಗ ನಿರೋಧಕ ಸ್ಥಳೀಯ ತಳಿಗಳನ್ನು ಬಳಸಿ",
#                 "ಮಣ್ಣಿನ ಆರೋಗ್ಯಕ್ಕಾಗಿ ನಿಯಮಿತವಾಗಿ ಸಾವಯವ ಕೊಪೋಸ್ಟ್ ಅನ್ನು ಲಗತ್ತಿಸಿ"
#             ],
#             "ta": [
#                 "சரியான மண் வடிகால் மற்றும் காற்றோட்டத்தை உறுதி செய்யவும்",
#                 "பருப்பு வகைகளுடன் பயிர் சுழற்சியை பின்பற்றவும்",
#                 "நோய் எதிர்ப்பு உள்ளூர் வகைகளைப் பயன்படுத்தவும்",
#                 "மண் ஆரோக்கியத்திற்கு தினமும் கரிம குப்பை உரம் பயன்படுத்தவும்"
#             ],
#             "te": [
#                 "సరైన నేల డ్రైనేజ్ మరియు వాయు ప్రసరణను నిర్ధారించండి",
#                 "పప్పు పంటలతో పంట భ్రమణం చేయండి",
#                 "రోగ నిరోధక స్థానిక రకాలను ఉపయోగించండి",
#                 "నేల ఆరోగ్యం కోసం నియమితంగా సేంద్రియ కంపోస్ట్ వర్తించండి"
#             ]
#         }
#     }

# def generate_multilingual_info(disease_name, existing_raw_labels=None):
#     """Generate multilingual info for a disease with ORGANIC FIRST approach"""
#     print(f"🤖 Asking AI (Organic Priority) about: {disease_name}...")
    
#     # Clean up name for display
#     display_name = disease_name.replace('_', ' ').replace('___', ' - ').replace(',', '').title()
    
#     # --- ORGANIC FIRST, CHEMICAL LAST PROMPT ---
#     prompt = f"""
#     Act as a Sustainable Agriculture Expert. Provide advice for: "{display_name}".
    
#     CORE PHILOSOPHY: 
#     1. PRIORITIZE SOIL HEALTH. Do not suggest harsh chemicals immediately.
#     2. Step 1 & 2 MUST be Organic/Biological/Home remedies (e.g., Neem, Trichoderma, Sour Buttermilk).
#     3. Suggest Chemical Pesticides ONLY as a "Last Resort" (Step 4) for severe cases.
    
#     Return ONLY JSON with this structure for ALL 6 languages: en, hi, mr, kn, ta, te:
#     {{
#         "description": {{ 
#             "en": "Short description focusing on symptoms (2-3 sentences)",
#             "hi": "लक्षणों पर केंद्रित संक्षिप्त विवरण (2-3 वाक्य)",
#             "mr": "लक्षणांवर लक्ष केंद्रित करणारे संक्षिप्त वर्णन (2-3 वाक्ये)",
#             "kn": "ಲಕ್ಷಣಗಳ ಮೇಲೆ ಕೇಂದ್ರೀಕರಿಸುವ ಸಂಕ್ಷಿಪ್ತ ವಿವರಣೆ (2-3 ವಾಕ್ಯಗಳು)",
#             "ta": "அறிகுறிகளில் கவனம் செலுத்தும் சுருக்கமான விளக்கம் (2-3 வாக்கியங்கள்)",
#             "te": "లక్షణాలపై దృష్టి పెట్టే సంక్షిప్త వివరణ (2-3 వాక్యాలు)"
#         }},
#         "treatment": {{ 
#             "en": [
#                 "Step 1 (Organic): [Specific organic remedy like Neem Oil, Garlic Spray]",
#                 "Step 2 (Biological): [Bio-agent or cultural practice like Trichoderma]",
#                 "Step 3 (Management): [Pruning/Isolation/Soil amendment]",
#                 "Step 4 (Severe Case): [Specific Chemical Name] (Use only if severe, harmful to soil)"
#             ],
#             "hi": [
#                 "चरण 1 (जैविक): [नीम तेल, लहसुन स्प्रे जैसे विशिष्ट जैविक उपचार]",
#                 "चरण 2 (जैविक): [ट्राइकोडर्मा जैसे जैविक एजेंट या सांस्कृतिक अभ्यास]",
#                 "चरण 3 (प्रबंधन): [छंटाई/अलगाव/मिट्टी संशोधन]",
#                 "चरण 4 (गंभीर): [विशिष्ट रासायनिक नाम] (केवल गंभीर होने पर, मिट्टी के लिए हानिकारक)"
#             ],
#             "mr": [
#                 "चरण 1 (जैविक): [निंब तेल, लसूण स्प्रे सारख्या विशिष्ट जैविक उपाय]",
#                 "चरण 2 (जैविक): [ट्रायकोडर्मा सारखे जैविक एजंट किंवा सांस्कृतिक सवय]",
#                 "चरण 3 (व्यवस्थापन): [काटछाट/वेगळेपणा/माती सुधार]",
#                 "चरण 4 (गंभीर): [विशिष्ट रासायनिक नाव] (केवळ गंभीर प्रकरणात, मातीसाठी हानिकारक)"
#             ],
#             "kn": [
#                 "ಹಂತ 1 (ಸಾವಯವ): [ನೀಮ್ ತೈಲ, ಬೆಳ್ಳುಳ್ಳಿ ಸಿಂಪಡಣೆ ನಂತಹ ನಿರ್ದಿಷ್ಟ ಸಾವಯವ ಪರಿಹಾರ]",
#                 "ಹಂತ 2 (ಜೈವಿಕ): [ಟ್ರೈಕೋಡರ್ಮಾ ನಂತಹ ಜೈವಿಕ ಏಜೆಂಟ್ ಅಥವಾ ಸಾಂಸ್ಕೃತಿಕ ಅಭ್ಯಾಸ]",
#                 "ಹಂತ 3 (ನಿರ್ವಹಣೆ): [ಕತ್ತರಿಸುವಿಕೆ/ಪ್ರತ್ಯೇಕತೆ/ಮಣ್ಣಿನ ತಿದ್ದುಪಡಿ]",
#                 "ಹಂತ 4 (ತೀವ್ರ): [ನಿರ್ದಿಷ್ಟ ರಾಸಾಯನಿಕ ಹೆಸರು] (ತೀವ್ರವಾಗಿದ್ದರೆ ಮಾತ್ರ, ಮಣ್ಣಿಗೆ ಹಾನಿಕಾರಕ)"
#             ],
#             "ta": [
#                 "படி 1 (கரிம): [வேப்ப எண்ணெய், பூண்டு தெளிப்பு போன்ற குறிப்பிட்ட கரிம மருந்து]",
#                 "படி 2 (உயிரியல்): [டிரைக்கோடெர்மா போன்ற உயிர் முகவர் அல்லது பண்பாட்டு நடைமுறை]",
#                 "படி 3 (மேலாண்மை): [கத்தரித்தல்/தனிமைப்படுத்தல்/மண் திருத்தம்]",
#                 "படி 4 (கடுமையான): [குறிப்பிட்ட ரசாயன பெயர்] (கடுமையான நிலையில் மட்டுமே, மண்ணுக்கு தீங்கு விளைவிக்கும்)"
#             ],
#             "te": [
#                 "దశ 1 (సేంద్రియ): [వేప నూనె, వెల్లుల్లి స్ప్రే వంటి నిర్దిష్ట సేంద్రియ పరిష్కారం]",
#                 "దశ 2 (జీవ): [ట్రైకోడెర్మా వంటి జీవ ఏజెంట్ లేదా సాంస్కృతిక పద్ధతి]",
#                 "దశ 3 (నిర్వహణ): [కత్తిరించడం/వేరు చేయడం/నేల సవరణ]",
#                 "దశ 4 (తీవ్రమైన): [నిర్దిష్ట రసాయన పేరు] (తీవ్రంగా ఉన్నప్పుడు మాత్రమే, నేలకు హానికరం)"
#             ]
#         }},
#         "prevention": {{
#             "en": [
#                 "Ensure proper soil drainage and aeration",
#                 "Practice crop rotation with legumes",
#                 "Use disease-resistant native varieties",
#                 "Apply organic compost regularly for soil health"
#             ],
#             "hi": [
#                 "उचित मिट्टी जल निकासी और वायुसंचार सुनिश्चित करें",
#                 "फलियों के साथ फसल चक्र का अभ्यास करें",
#                 "रोग प्रतिरोधी देशी किस्मों का उपयोग करें",
#                 "मिट्टी के स्वास्थ्य के लिए नियमित रूप से जैविक खाद डालें"
#             ],
#             "mr": [
#                 "योग्य मातीचे ड्रेनेज आणि वातीकरण सुनिश्चित करा",
#                 "शेंगदाण्यांसह पिक फेरपालटाची सवय करा",
#                 "रोगप्रतिकारक स्थानिक प्रजाती वापरा",
#                 "मातीच्या आरोग्यासाठी नियमितपणे जैविक कंपोस्ट लावा"
#             ],
#             "kn": [
#                 "ಸರಿಯಾದ ಮಣ್ಣಿನ ಒಳಚರಂಡಿ ಮತ್ತು ಗಾಳಿಯಾಟವನ್ನು ಖಚಿತಪಡಿಸಿ",
#                 "ಕಾಳುಗಳೊಂದಿಗೆ ಬೆಳೆ ಪರ್ಯಾಯ ಅಭ್ಯಾಸ ಮಾಡಿ",
#                 "ರೋಗ ನಿರೋಧಕ ಸ್ಥಳೀಯ ತಳಿಗಳನ್ನು ಬಳಸಿ",
#                 "ಮಣ್ಣಿನ ಆರೋಗ್ಯಕ್ಕಾಗಿ ನಿಯಮಿತವಾಗಿ ಸಾವಯವ ಕೊಪೋಸ್ಟ್ ಅನ್ನು ಲಗತ್ತಿಸಿ"
#             ],
#             "ta": [
#                 "சரியான மண் வடிகால் மற்றும் காற்றோட்டத்தை உறுதி செய்யவும்",
#                 "பருப்பு வகைகளுடன் பயிர் சுழற்சியை பின்பற்றவும்",
#                 "நோய் எதிர்ப்பு உள்ளூர் வகைகளைப் பயன்படுத்தவும்",
#                 "மண் ஆரோக்கியத்திற்கு தினமும் கரிம குப்பை உரம் பயன்படுத்தவும்"
#             ],
#             "te": [
#                 "సరైన నేల డ్రైనేజ్ మరియు వాయు ప్రసరణను నిర్ధారించండి",
#                 "పప్పు పంటలతో పంట భ్రమణం చేయండి",
#                 "రోగ నిరోధక స్థానిక రకాలను ఉపయోగించండి",
#                 "నేల ఆరోగ్యం కోసం నియమితంగా సేంద్రియ కంపోస్ట్ వర్తించండి"
#             ]
#         }}
#     }}
    
#     RULES:
#     1. Be specific about symptoms, causes, and remedies
#     2. Step 1-3 MUST be organic/biological solutions
#     3. Step 4 can mention chemical but ONLY as last resort
#     4. Use agricultural terminology appropriate for Indian farmers
#     5. Include organic/sustainable solutions where possible
#     6. Consider regional variations in farming practices
#     """
    
#     try:
#         response = query_llm(prompt)
#         text = response.get("text", str(response))
        
#         # Clean the response
#         text = text.strip()
#         if "```json" in text:
#             text = text.split("```json")[1]
#         if "```" in text:
#             text = text.split("```")[0]
#         text = text.strip()
        
#         if text.startswith("{") and text.endswith("}"):
#             data = json.loads(text)
            
#             # Ensure all languages are present
#             for field in ["description", "treatment", "prevention"]:
#                 if field not in data:
#                     data[field] = create_fallback_response(display_name)[field]
#                 else:
#                     for lang in LANGUAGES:
#                         if lang not in data[field]:
#                             # Use fallback for missing language
#                             fallback = create_fallback_response(display_name)
#                             data[field][lang] = fallback[field][lang]
            
#             # Add raw_labels if provided
#             if existing_raw_labels:
#                 data["raw_labels"] = existing_raw_labels
#             else:
#                 data["raw_labels"] = []
                
#             return data
            
#     except Exception as e:
#         print(f"⚠️ API error for {disease_name}: {e}")
    
#     # Return complete fallback
#     fallback = create_fallback_response(display_name)
#     if existing_raw_labels:
#         fallback["raw_labels"] = existing_raw_labels
#     return fallback

# def check_language_completeness(entry):
#     """Check if all 6 languages are present in all fields"""
#     if not entry:
#         return False
    
#     required_fields = ["description", "treatment", "prevention"]
    
#     for field in required_fields:
#         if field not in entry:
#             return False
        
#         # Check all languages exist in this field
#         if isinstance(entry[field], dict):
#             for lang in LANGUAGES:
#                 if lang not in entry[field]:
#                     return False
#                 # Check content is not empty or placeholder
#                 content = entry[field][lang]

#                 # Case 1: description (string)
#                 if isinstance(content, str):
#                     if content.strip() == "":
#                         return False

#                 # Case 2: treatment / prevention (list)
#                 elif isinstance(content, list):
#                     if len(content) == 0:
#                         return False
#                     # optional: check empty strings inside list
#                     if all((not isinstance(i, str) or i.strip() == "") for i in content):
#                         return False

#                 else:
#                     return False
#         else:
#             return False
    
#     # Check raw_labels exist
#     if "raw_labels" not in entry:
#         return False
    
#     return True

# def main():
#     kb_path = Path(__file__).parent.parent / "ml/knowledge_base/diseases.json"
#     data = {}
    
#     # Load existing data
#     if kb_path.exists():
#         try:
#             with open(kb_path, 'r', encoding='utf-8') as f:
#                 data = json.load(f)
#             print(f"📖 Loaded existing KB with {len(data)} entries")
#         except Exception as e:
#             print(f"⚠️ Could not load existing KB: {e}. Starting fresh...")
#             data = {}
#     else:
#         print("📝 Creating new Knowledge Base file...")
    
#     # Group raw labels by canonical key
#     from collections import defaultdict
#     key_to_raw = defaultdict(list)
    
#     print(f"\n🔍 Processing {len(RAW_CLASSES)} raw labels...")
    
#     for raw_name in RAW_CLASSES:
#         key = normalize_key(raw_name)
#         key_to_raw[key].append(raw_name)
    
#     print(f"📊 Found {len(key_to_raw)} unique diseases after normalization")
    
#     # Process each canonical disease
#     for i, (key, raw_labels) in enumerate(key_to_raw.items()):
#         print(f"\n[{i+1}/{len(key_to_raw)}] Processing: {key}")
#         print(f"   📍 Raw labels: {', '.join(raw_labels[:3])}{'...' if len(raw_labels) > 3 else ''}")
        
#         needs_update = False
        
#         if key not in data:
#             needs_update = True
#             print(f"   ➕ New disease, will generate ORGANIC-FIRST AI info")
#         elif not check_language_completeness(data[key]):
#             needs_update = True
#             print(f"   🔄 Incomplete/missing languages, will regenerate with ORGANIC approach")
#         else:
#             # Check if raw_labels need updating
#             existing_raw = set(data[key].get("raw_labels", []))
#             new_raw = set(raw_labels)
#             if not new_raw.issubset(existing_raw):
#                 # Merge raw labels
#                 data[key]["raw_labels"] = list(existing_raw.union(new_raw))
#                 needs_update = True
#                 print(f"   🔄 Adding {len(new_raw - existing_raw)} new raw labels")
        
#         if needs_update:
#             # Use the first raw label as display name for AI
#             display_name = raw_labels[0]
            
#             # Generate or regenerate info with ORGANIC-FIRST approach
#             data[key] = generate_multilingual_info(display_name, raw_labels)
            
#             # Save incrementally
#             with open(kb_path, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, indent=4, ensure_ascii=False)
            
#             print(f"   💾 Saved to KB")
            
#             # Rate limiting (be nice to API)
#             time.sleep(1.5)
#         else:
#             print(f"   ✅ Already complete in KB")
    
#     # Final verification
#     print(f"\n" + "="*50)
#     print("🔍 FINAL VERIFICATION")
#     print("="*50)
    
#     incomplete = []
#     for key, entry in data.items():
#         if not check_language_completeness(entry):
#             incomplete.append(key)
    
#     if incomplete:
#         print(f"⚠️ WARNING: {len(incomplete)} entries still incomplete")
#         print("\nIncomplete entries:")
#         for key in incomplete[:10]:  # Show first 10
#             print(f"   ❌ {key}")
#         if len(incomplete) > 10:
#             print(f"   ... and {len(incomplete) - 10} more")
        
#         # Try to fix incomplete entries
#         print(f"\n🔄 Attempting to fix incomplete entries...")
#         fixed_count = 0
#         for key in incomplete:
#             if key in key_to_raw:
#                 print(f"   Fixing: {key}")
#                 display_name = key_to_raw[key][0]
#                 data[key] = generate_multilingual_info(display_name, key_to_raw[key])
#                 fixed_count += 1
#                 time.sleep(1.5)
        
#         if fixed_count > 0:
#             with open(kb_path, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, indent=4, ensure_ascii=False)
#             print(f"   ✅ Fixed {fixed_count} entries")
#     else:
#         print(f"✅ PERFECT! All {len(data)} entries have complete multilingual ORGANIC-FIRST data!")
    
#     # Final statistics
#     print(f"\n" + "="*50)
#     print("📊 KNOWLEDGE BASE STATISTICS")
#     print("="*50)
#     print(f"Total unique diseases: {len(data)}")
#     print(f"Total raw labels processed: {len(RAW_CLASSES)}")
#     print(f"Raw labels in KB: {sum(len(entry.get('raw_labels', [])) for entry in data.values())}")
    
#     # Check coverage
#     all_raw_in_kb = set()
#     for entry in data.values():
#         all_raw_in_kb.update(entry.get('raw_labels', []))
    
#     missing_raw = set(RAW_CLASSES) - all_raw_in_kb
#     if missing_raw:
#         print(f"\n⚠️ WARNING: {len(missing_raw)} raw labels not in KB:")
#         for label in sorted(list(missing_raw))[:5]:
#             print(f"   - {label}")
#         if len(missing_raw) > 5:
#             print(f"   ... and {len(missing_raw) - 5} more")
#     else:
#         print(f"\n✅ 100% COVERAGE: All raw labels are in KB!")
    
#     print(f"\n🎉 MASTER ORGANIC-FIRST MULTILINGUAL KNOWLEDGE BASE READY!")
#     print(f"📍 Location: {kb_path.absolute()}")

# if __name__ == "__main__":
#     main()


# import json, time, sys
# from pathlib import Path
# sys.path.append(str(Path(__file__).parent))
# from app.ml.llm_provider import query_llm 

# # --- COMPLETE MASTER CLASS LIST (100% Coverage of Both Models) ---
# RAW_CLASSES = [
#     # Model 1 Classes
#     'Apple_Apple_scab', 'Apple_Black_rot', 'Apple_Cedar_apple_rust', 'Apple_healthy',
#     'Blueberry_healthy', 'Cherry_healthy', 'Cherry_Powdery_mildew',
#     'Corn_Cercospora_leaf_spot_Gray_leaf_spot', 'Corn_Common_rust', 'Corn_healthy',
#     'Corn_Northern_Leaf_Blight', 'Grape_Black_rot', 'Grape_Esca_(Black_Measles)',
#     'Grape_healthy', 'Grape_Leaf_blight_(Isariopsis_Leaf_Spot)',
#     'Orange_Haunglongbing_(Citrus_greening)', 'Peach_Bacterial_spot', 'Peach_healthy',
#     'Pepper_bell_Bacterial_spot', 'Pepper_bell_healthy', 'Potato_Early_blight',
#     'Potato_healthy', 'Potato_Late_blight', 'Raspberry_healthy', 'Soybean_healthy',
#     'Squash_Powdery_mildew', 'Strawberry_healthy', 'Strawberry_Leaf_scorch',
#     'Tomato_Bacterial_spot', 'Tomato_Early_blight', 'Tomato_healthy',
#     'Tomato_Late_blight', 'Tomato_Leaf_Mold', 'Tomato_Septoria_leaf_spot',
#     'Tomato_Spider_mites_Two-spotted_spider_mite', 'Tomato_Target_Spot', 
#     'Tomato_Tomato_mosaic_virus', 'Tomato_Tomato_Yellow_Leaf_Curl_virus',
    
#     # Model 2 Classes
#     'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust',
#     'Apple___healthy', 'Blueberry___healthy', 'Cassava CB (Cassava Blight)',
#     'Cassava CM (Cassava Mosaic)', 'Cassava Healthy leaf',
#     'Cherry_(including_sour)___Powdery_mildew', 'Cherry_(including_sour)___healthy',
#     'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Corn_(maize)___Common_rust_',
#     'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy',
#     'Grape___Black_rot', 'Grape___Esca_(Black_Measles)',
#     'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy',
#     'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot',
#     'Peach___healthy', 'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy',
#     'Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy',
#     'Raspberry___healthy', 'Soybean___healthy', 'Squash___Powdery_mildew',
#     'Strawberry___Leaf_scorch', 'Strawberry___healthy', 'Tomato___Bacterial_spot',
#     'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold',
#     'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite',
#     'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
#     'Tomato___Tomato_mosaic_virus', 'Tomato___healthy',
    
#     # Additional rice diseases
#     'bacterial_leaf_blight', 'bacterial_leaf_streak', 'bacterial_panicle_blight',
#     'blast', 'brown_spot', 'dead_heart', 'downy_mildew', 'hispa', 'normal', 'tungro'
# ]

# LANGUAGES = ["en", "hi", "mr", "kn", "ta", "te"]

# def normalize_key(name):
#     """Create canonical key while preserving original labels separately"""
#     # Replace multiple underscores with single, remove spaces, parentheses, commas
#     return name.replace("___", "_").replace(" ", "_").replace("(", "").replace(")", "").replace(",", "").lower()

# def create_fallback_response(disease_name):
#     """Create complete multilingual fallback with all 6 languages"""
#     # Extract plant name for better messages
#     plant_name = disease_name.split('_')[0] if '_' in disease_name else disease_name
    
#     return {
#         "raw_labels": [],  # Will be populated later
#         "description": {
#             "en": f"Agricultural information about {disease_name}. Detailed description coming soon.",
#             "hi": f"{disease_name} के बारे में कृषि जानकारी। विस्तृत विवरण जल्द ही उपलब्ध होगा।",
#             "mr": f"{disease_name} बद्दल शेती माहिती. तपशीलवर्णन लवकरच उपलब्ध होईल.",
#             "kn": f"{disease_name} ಬಗ್ಗೆ ಕೃಷಿ ಮಾಹಿತಿ. ವಿವರವಾದ ವಿವರ ಶೀಘ್ರದಲ್ಲೇ ಲಭ್ಯವಾಗುತ್ತದೆ.",
#             "ta": f"{disease_name} பற்றிய விவசாய தகவல். விரிவான விளக்கம் விரைவில் கிடைக்கும்.",
#             "te": f"{disease_name} గురించి వ్యవసాయ సమాచారం. వివరణాత్మక వివరం త్వరలో లభిస్తుంది."
#         },
#         "treatment": {
#             "en": [
#                 f"Consult agricultural expert for {plant_name} disease management",
#                 "Use recommended fungicides/pesticides as per local guidelines",
#                 "Remove and destroy infected plant parts"
#             ],
#             "hi": [
#                 f"{plant_name} की बीमारी प्रबंधन के लिए कृषि विशेषज्ञ से सलाह लें",
#                 "स्थानीय दिशानिर्देशों के अनुसार अनुशंसित फफूंदनाशक/कीटनाशक का उपयोग करें",
#                 "संक्रमित पौधे के भागों को हटाकर नष्ट कर दें"
#             ],
#             "mr": [
#                 f"{plant_name} रोग व्यवस्थापनासाठी शेती तज्ञांचा सल्ला घ्या",
#                 "स्थानिक मार्गदर्शक तत्त्वांनुसार शिफारस केलेले फंगीसायड्स/कीटकनाशके वापरा",
#                 "संक्रमित वनस्पती भाग काढून टाका आणि नष्ट करा"
#             ],
#             "kn": [
#                 f"{plant_name} ರೋಗ ನಿರ್ವಹಣೆಗಾಗಿ ಕೃಷಿ ತಜ್ಞರನ್ನು ಸಂಪರ್ಕಿಸಿ",
#                 "ಸ್ಥಳೀಯ ಮಾರ್ಗಸೂಚಿಗಳಿಗೆ ಅನುಗುಣವಾಗಿ ಶಿಫಾರಸು ಮಾಡಿದ ಫಂಗಿಸೈಡ್ಗಳು/ಕೀಟನಾಶಕಗಳನ್ನು ಬಳಸಿ",
#                 "ಸೋಂಕು ಹರಡಿದ ಸಸ್ಯದ ಭಾಗಗಳನ್ನು ತೆಗೆದು ಹಾಕಿ ನಾಶಪಡಿಸಿ"
#             ],
#             "ta": [
#                 f"{plant_name} நோய் மேலாண்மைக்கு விவசாய நிபுணரை அணுகவும்",
#                 "உள்ளூர் வழிகாட்டுதல்களின்படி பரிந்துரைக்கப்பட்ட பூஞ்சைக்கொல்லிகள்/பூச்சிக்கொல்லிகளைப் பயன்படுத்தவும்",
#                 "பாதிக்கப்பட்ட தாவர பகுதிகளை அகற்றி அழிக்கவும்"
#             ],
#             "te": [
#                 f"{plant_name} వ్యాధి నిర్వహణ కోసం వ్యవసాయ నిపుణులను సంప్రదించండి",
#                 "స్థానిక మార్గదర్శకాల ప్రకారం సిఫారసు చేయబడిన ఫంగిసైడ్లు/పురుగుమందులను ఉపయోగించండి",
#                 "సోకిన మొక్క భాగాలను తీసివేసి నాశనం చేయండి"
#             ]
#         },
#         "prevention": {
#             "en": [
#                 "Practice crop rotation regularly",
#                 "Maintain proper field sanitation",
#                 "Use disease-resistant varieties when available",
#                 "Monitor crops regularly for early signs"
#             ],
#             "hi": [
#                 "नियमित रूप से फसल चक्र का अभ्यास करें",
#                 "उचित खेत स्वच्छता बनाए रखें",
#                 "उपलब्ध होने पर रोग प्रतिरोधी किस्मों का उपयोग करें",
#                 "शुरुआती लक्षणों के लिए नियमित रूप से फसलों की निगरानी करें"
#             ],
#             "mr": [
#                 "नियमितपणे पिक फेरपालटाची सवय करा",
#                 "योग्य शेत स्वच्छता राखा",
#                 "उपलब्ध असल्यास रोगप्रतिरोधक प्रजाती वापरा",
#                 "लवकर लक्षणांसाठी नियमितपणे पिकांचे निरीक्षण करा"
#             ],
#             "kn": [
#                 "ನಿಯಮಿತವಾಗಿ ಬೆಳೆ ಪರ್ಯಾಯ ಅಭ್ಯಾಸ ಮಾಡಿ",
#                 "ಸರಿಯಾದ ಹೊಲ ಸ್ವಚ್ಛತೆಯನ್ನು ಕಾಪಾಡಿ",
#                 "ಲಭ್ಯವಿರುವಾಗ ರೋಗ ನಿರೋಧಕ ವಿಧಗಳನ್ನು ಬಳಸಿ",
#                 "ಮುಂಚಿತ ಚಿಹ್ನೆಗಳಿಗಾಗಿ ನಿಯಮಿತವಾಗಿ ಬೆಳೆಗಳನ್ನು ಗಮನಿಸಿ"
#             ],
#             "ta": [
#                 "தொடர்ந்து பயிர் சுழற்சியைப் பின்பற்றவும்",
#                 "சரியான வயல் சுகாதாரத்தை பராமரிக்கவும்",
#                 "கிடைக்கும் போது நோய் எதிர்ப்பு வகைகளைப் பயன்படுத்தவும்",
#                 "ஆரம்ப கால அறிகுறிகளுக்கு பயிர்களை தினமும் கண்காணிக்கவும்"
#             ],
#             "te": [
#                 "నియమితంగా పంట భ్రమణం చేయండి",
#                 "సరైన పొలం శుభ్రతను కాపాడండి",
#                 "అందుబాటులో ఉన్నప్పుడు రోగ నిరోధక రకాలను ఉపయోగించండి",
#                 "ప్రారంభ సంకేతాల కోసం నియమితంగా పంటలను పర్యవేక్షించండి"
#             ]
#         }
#     }

# def generate_multilingual_info(disease_name, existing_raw_labels=None):
#     """Generate multilingual info for a disease with proper fallback"""
#     print(f"🤖 Asking AI about: {disease_name}...")
    
#     # Clean up name for display
#     display_name = disease_name.replace('_', ' ').replace('___', ' - ').title()
    
#     prompt = f"""
#     Provide expert agricultural advice for: "{display_name}".
    
#     IMPORTANT: Return ONLY JSON with this EXACT structure for all 6 languages:
#     {{
#         "description": {{ 
#             "en": "English description here (3-4 sentences)",
#             "hi": "Hindi description here (3-4 वाक्य)",
#             "mr": "Marathi description here (3-4 वाक्ये)",
#             "kn": "Kannada description here (3-4 ವಾಕ್ಯಗಳು)",
#             "ta": "Tamil description here (3-4 வாக்கியங்கள்)",
#             "te": "Telugu description here (3-4 వాక్యాలు)"
#         }},
#         "treatment": {{ 
#             "en": ["Step 1", "Step 2", "Step 3", "Step 4"],
#             "hi": ["कदम 1", "कदम 2", "कदम 3", "कदम 4"],
#             "mr": ["चरण 1", "चरण 2", "चरण 3", "चरण 4"],
#             "kn": ["ಹಂತ 1", "ಹಂತ 2", "ಹಂತ 3", "ಹಂತ 4"],
#             "ta": ["படி 1", "படி 2", "படி 3", "படி 4"],
#             "te": ["దశ 1", "దశ 2", "దశ 3", "దశ 4"]
#         }},
#         "prevention": {{
#             "en": ["Measure 1", "Measure 2", "Measure 3"],
#             "hi": ["उपाय 1", "उपाय 2", "उपाय 3"],
#             "mr": ["उपाय 1", "उपाय 2", "उपाय 3"],
#             "kn": ["ಕ್ರಮ 1", "ಕ್ರಮ 2", "ಕ್ರಮ 3"],
#             "ta": ["நடவடிக்கை 1", "நடவடிக்கை 2", "நடவடிக்கை 3"],
#             "te": ["ప్రయత్నం 1", "ప్రయత్నం 2", "ప్రయత్నం 3"]
#         }}
#     }}
    
#     RULES:
#     1. Be specific about symptoms, causes, and remedies
#     2. Provide 3-4 treatment steps and 3 prevention measures
#     3. Use agricultural terminology appropriate for Indian farmers
#     4. Include organic/sustainable solutions where possible
#     5. Mention specific chemical names if applicable
#     6. Consider regional variations in farming practices
#     """
    
#     try:
#         response = query_llm(prompt)
#         text = response.get("text", str(response))
        
#         # Clean the response
#         text = text.strip()
#         if "```json" in text:
#             text = text.split("```json")[1]
#         if "```" in text:
#             text = text.split("```")[0]
#         text = text.strip()
        
#         if text.startswith("{") and text.endswith("}"):
#             data = json.loads(text)
            
#             # Ensure all languages are present
#             for field in ["description", "treatment", "prevention"]:
#                 if field not in data:
#                     data[field] = create_fallback_response(display_name)[field]
#                 else:
#                     for lang in LANGUAGES:
#                         if lang not in data[field]:
#                             # Use fallback for missing language
#                             fallback = create_fallback_response(display_name)
#                             data[field][lang] = fallback[field][lang]
            
#             # Add raw_labels if provided
#             if existing_raw_labels:
#                 data["raw_labels"] = existing_raw_labels
#             else:
#                 data["raw_labels"] = []
                
#             return data
            
#     except Exception as e:
#         print(f"⚠️ API error for {disease_name}: {e}")
    
#     # Return complete fallback
#     fallback = create_fallback_response(display_name)
#     if existing_raw_labels:
#         fallback["raw_labels"] = existing_raw_labels
#     return fallback

# def check_language_completeness(entry):
#     """Check if all 6 languages are present in all fields"""
#     if not entry:
#         return False
    
#     required_fields = ["description", "treatment", "prevention"]
    
#     for field in required_fields:
#         if field not in entry:
#             return False
        
#         # Check all languages exist in this field
#         if isinstance(entry[field], dict):
#             for lang in LANGUAGES:
#                 if lang not in entry[field]:
#                     return False
#                 # Check content is not empty or placeholder
#                 content = entry[field][lang]

#                 # Case 1: description (string)
#                 if isinstance(content, str):
#                     if content.strip() == "":
#                         return False

#                 # Case 2: treatment / prevention (list)
#                 elif isinstance(content, list):
#                     if len(content) == 0:
#                         return False
#                     # optional: check empty strings inside list
#                     if all((not isinstance(i, str) or i.strip() == "") for i in content):
#                         return False

#                 else:
#                     return False
#         else:
#             return False
    
#     # Check raw_labels exist
#     if "raw_labels" not in entry:
#         return False
    
#     return True

# def main():
#     kb_path = Path(__file__).parent.parent / "ml/knowledge_base/diseases.json"
#     data = {}
    
#     # Load existing data
#     if kb_path.exists():
#         try:
#             with open(kb_path, 'r', encoding='utf-8') as f:
#                 data = json.load(f)
#             print(f"📖 Loaded existing KB with {len(data)} entries")
#         except Exception as e:
#             print(f"⚠️ Could not load existing KB: {e}. Starting fresh...")
#             data = {}
#     else:
#         print("📝 Creating new Knowledge Base file...")
    
#     # Group raw labels by canonical key
#     from collections import defaultdict
#     key_to_raw = defaultdict(list)
    
#     print(f"\n🔍 Processing {len(RAW_CLASSES)} raw labels...")
    
#     for raw_name in RAW_CLASSES:
#         key = normalize_key(raw_name)
#         key_to_raw[key].append(raw_name)
    
#     print(f"📊 Found {len(key_to_raw)} unique diseases after normalization")
    
#     # Process each canonical disease
#     for i, (key, raw_labels) in enumerate(key_to_raw.items()):
#         print(f"\n[{i+1}/{len(key_to_raw)}] Processing: {key}")
#         print(f"   📍 Raw labels: {', '.join(raw_labels[:3])}{'...' if len(raw_labels) > 3 else ''}")
        
#         needs_update = False
        
#         if key not in data:
#             needs_update = True
#             print(f"   ➕ New disease, will generate AI info")
#         elif not check_language_completeness(data[key]):
#             needs_update = True
#             print(f"   🔄 Incomplete/missing languages, will regenerate")
#         else:
#             # Check if raw_labels need updating
#             existing_raw = set(data[key].get("raw_labels", []))
#             new_raw = set(raw_labels)
#             if not new_raw.issubset(existing_raw):
#                 # Merge raw labels
#                 data[key]["raw_labels"] = list(existing_raw.union(new_raw))
#                 needs_update = True
#                 print(f"   🔄 Adding {len(new_raw - existing_raw)} new raw labels")
        
#         if needs_update:
#             # Use the first raw label as display name for AI
#             display_name = raw_labels[0]
            
#             # Generate or regenerate info
#             data[key] = generate_multilingual_info(display_name, raw_labels)
            
#             # Save incrementally
#             with open(kb_path, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, indent=4, ensure_ascii=False)
            
#             print(f"   💾 Saved to KB")
            
#             # Rate limiting (be nice to API)
#             time.sleep(1.5)
#         else:
#             print(f"   ✅ Already complete in KB")
    
#     # Final verification
#     print(f"\n" + "="*50)
#     print("🔍 FINAL VERIFICATION")
#     print("="*50)
    
#     incomplete = []
#     for key, entry in data.items():
#         if not check_language_completeness(entry):
#             incomplete.append(key)
    
#     if incomplete:
#         print(f"⚠️ WARNING: {len(incomplete)} entries still incomplete")
#         print("\nIncomplete entries:")
#         for key in incomplete[:10]:  # Show first 10
#             print(f"   ❌ {key}")
#         if len(incomplete) > 10:
#             print(f"   ... and {len(incomplete) - 10} more")
        
#         # Try to fix incomplete entries
#         print(f"\n🔄 Attempting to fix incomplete entries...")
#         fixed_count = 0
#         for key in incomplete:
#             if key in key_to_raw:
#                 print(f"   Fixing: {key}")
#                 display_name = key_to_raw[key][0]
#                 data[key] = generate_multilingual_info(display_name, key_to_raw[key])
#                 fixed_count += 1
#                 time.sleep(1)
        
#         if fixed_count > 0:
#             with open(kb_path, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, indent=4, ensure_ascii=False)
#             print(f"   ✅ Fixed {fixed_count} entries")
#     else:
#         print(f"✅ PERFECT! All {len(data)} entries have complete multilingual data!")
    
#     # Final statistics
#     print(f"\n" + "="*50)
#     print("📊 KNOWLEDGE BASE STATISTICS")
#     print("="*50)
#     print(f"Total unique diseases: {len(data)}")
#     print(f"Total raw labels processed: {len(RAW_CLASSES)}")
#     print(f"Raw labels in KB: {sum(len(entry.get('raw_labels', [])) for entry in data.values())}")
    
#     # Check coverage
#     all_raw_in_kb = set()
#     for entry in data.values():
#         all_raw_in_kb.update(entry.get('raw_labels', []))
    
#     missing_raw = set(RAW_CLASSES) - all_raw_in_kb
#     if missing_raw:
#         print(f"\n⚠️ WARNING: {len(missing_raw)} raw labels not in KB:")
#         for label in sorted(list(missing_raw))[:5]:
#             print(f"   - {label}")
#         if len(missing_raw) > 5:
#             print(f"   ... and {len(missing_raw) - 5} more")
#     else:
#         print(f"\n✅ 100% COVERAGE: All raw labels are in KB!")
    
#     print(f"\n🎉 MASTER MULTILINGUAL KNOWLEDGE BASE READY!")
#     print(f"📍 Location: {kb_path.absolute()}")

# if __name__ == "__main__":
#     main()


# # backend/build_knowledge_base.py

# import json
# import time
# import sys
# from pathlib import Path

# # Add 'app' to python path so we can import from it
# sys.path.append(str(Path(__file__).parent))

# from app.ml.llm_provider import query_llm 

# # The 51 classes your YOLO model detects
# DISEASE_CLASSES = list(set([
#     "Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust", "Apple___healthy",
#     "Blueberry___healthy", "Cherry_(including_sour)___Powdery_mildew", "Cherry_(including_sour)___healthy",
#     "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot", "Corn_(maize)___Common_rust_", 
#     "Corn_(maize)___Northern_Leaf_Blight", "Corn_(maize)___healthy", "Grape___Black_rot", 
#     "Grape___Esca_(Black_Measles)", "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", "Grape___healthy", 
#     "Orange___Haunglongbing_(Citrus_greening)", "Peach___Bacterial_spot", "Peach___healthy", 
#     "Pepper,_bell___Bacterial_spot", "Pepper,_bell___healthy", "Potato___Early_blight", 
#     "Potato___Late_blight", "Potato___healthy", "Raspberry___healthy", "Soybean___healthy", 
#     "Squash___Powdery_mildew", "Strawberry___Leaf_scorch", "Strawberry___healthy", 
#     "Tomato___Bacterial_spot", "Tomato___Early_blight", "Tomato___Late_blight", "Tomato___Leaf_Mold", 
#     "Tomato___Septoria_leaf_spot", "Tomato___Spider_mites Two-spotted_spider_mite", 
#     "Tomato___Target_Spot", "Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato___Tomato_mosaic_virus", 
#     "Tomato___healthy", "bacterial_leaf_blight", "bacterial_leaf_streak", "bacterial_panicle_blight", 
#     "blast", "brown_spot", "dead_heart", "downy_mildew", "hispa", "normal", "tungro", 
#     "Cassava CB (Cassava Blight)", "Cassava CM (Cassava Mosaic)", "Cassava Healthy leaf"
# ]))
# def generate_disease_info(disease_name):
#     """Asks the LLM for structured data about a disease"""
    
#     if "healthy" in disease_name.lower() or "normal" in disease_name.lower():
#         return {
#             "description": "The plant looks healthy and vigorous.",
#             "symptoms": ["No signs of disease", "Green leaves"],
#             "treatment": ["Maintain regular watering", "Monitor for pests"],
#             "prevention": ["Good field hygiene", "Proper spacing"]
#         }

#     print(f"🤖 Asking AI about: {disease_name}...")
    
#     prompt = f"""
#     Provide agricultural advice for the plant disease: "{disease_name}".
#     Return ONLY a JSON object with this exact structure (no markdown, no extra text):
#     {{
#         "description": "Short 1-sentence description",
#         "symptoms": ["Symptom 1", "Symptom 2"],
#         "treatment": ["Specific chemical cure", "Organic cure"],
#         "prevention": ["Prevention tip 1", "Prevention tip 2"]
#     }}
#     Make the advice practical for a farmer.
#     """

#     try:
#         response = query_llm(prompt)
        
#         # Handle different response types
#         if isinstance(response, dict):
#             text_response = response.get("text", "")
#         else:
#             text_response = str(response)

#         # Clean up markdown
#         text_response = text_response.replace("```json", "").replace("```", "").strip()
        
#         return json.loads(text_response)
#     except Exception as e:
#         print(f"❌ Failed to generate for {disease_name}: {e}")
#         # Keep the fallback so we can retry later
#         return {
#             "description": "Information temporarily unavailable.",
#             "treatment": ["USE_API_FALLBACK"] 
#         }

# def main():
#     # Correct path based on your screenshot: backend/../ml/knowledge_base/diseases.json
#     kb_path = Path(__file__).parent.parent / "ml/knowledge_base/diseases.json"
    
#     print(f"📂 Targeting Knowledge Base at: {kb_path}")

#     # Load existing data
#     if kb_path.exists():
#         with open(kb_path, "r") as f:
#             data = json.load(f)
#     else:
#         print("⚠️ File not found, creating new...")
#         data = {}

#     print(f"🚀 Starting Knowledge Base Enrichment for {len(DISEASE_CLASSES)} diseases...")

#     for disease in DISEASE_CLASSES:
#         # Skip if we already have good data
#         if disease in data:
#             current_treatment = data[disease].get("treatment", [])
#             # Checks if it's a string "USE_API_FALLBACK" or a list containing it
#             is_fallback = False
#             if isinstance(current_treatment, list) and "USE_API_FALLBACK" in current_treatment:
#                 is_fallback = True
#             elif isinstance(current_treatment, str) and "USE_API_FALLBACK" in current_treatment:
#                 is_fallback = True
                
#             if not is_fallback:
#                 print(f"✅ Skipping {disease} (Already has data)")
#                 continue

#         # Generate new data
#         info = generate_disease_info(disease)
#         data[disease] = info
        
#         # Save progress immediately
#         with open(kb_path, "w") as f:
#             json.dump(data, f, indent=4)
            
#         # Sleep to be nice to the API
#         time.sleep(1) 

#     print(f"🎉 Knowledge Base built successfully!")

# if __name__ == "__main__":
#     main()