from fastapi import APIRouter, HTTPException, Query
import requests
import json
import os

router = APIRouter()

# ============================================================
# 🔑 CONFIGURATION
# ============================================================
OPENWEATHER_KEY = "025fd0f7a6731edd3dcbc40f7fc5ecdd"

# 🔴 IMPORTANT: Put your real OpenRouter or AIPipe Key here for AI to work
# If you don't have a key, the code will automatically use the Fallback (Layer 3)
LLM_API_KEY = "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" 
LLM_API_URL = "https://openrouter.ai/api/v1/chat/completions" 
LLM_MODEL = "google/gemini-2.0-flash-exp:free" 

# 📢 LAYER 1: OFFICIAL ALERTS (Mock Database)
OFFICIAL_ALERTS = {
    
}

@router.get("/advisory", tags=["Smart Weather Advisory"])
async def get_weather_advisory(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    language: str = Query("english", description="User's language (hindi, tamil, marathi, english)")
):
    try:
        # 1. 📡 Fetch Real Weather
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_KEY}&units=metric"
        response = requests.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Weather API Error")
        
        data = response.json()
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        condition = data['weather'][0]['main']
        desc = data['weather'][0]['description']
        city = data.get('name', 'Unknown')

        # Default Values
        advisory_msg = ""
        source = ""
        spray_rec = "CHECK"
        alert_color = "orange"
        lang_lower = language.lower()

        # ============================================================
        # 🛡️ LAYER 1: OFFICIAL GOVT ALERT
        # ============================================================
        if city in OFFICIAL_ALERTS:
            # Simple toggle between Hindi and English for Govt alerts
            lang_key = "hindi" if "hindi" in lang_lower else "english"
            advisory_msg = "🏛️ " + OFFICIAL_ALERTS[city].get(lang_key, OFFICIAL_ALERTS[city]['english'])
            source = "Government Official"
            spray_rec = "NO"
            alert_color = "red"

        # ============================================================
        # 🧠 LAYER 2: AI EXPERT (OpenRouter / AIPipe)
        # ============================================================
        elif "YOUR_REAL_API_KEY" not in LLM_API_KEY and len(LLM_API_KEY) > 10:
            try:
                # Prompt: Explicitly ask for Native Script
                prompt = f"""
                Act as an Indian Agriculture Expert.
                Context: Location: {city}, Weather: {condition} ({desc}), Temp: {temp}C, Humidity: {humidity}%.
                
                CRITICAL TASK:
                1. Analyze if pesticide spraying is safe.
                2. Translate advice into "{language}" language script (NOT English characters).
                3. If language is Tamil, use Tamil letters. If Hindi, use Devanagari.
                
                Output strictly valid JSON:
                {{ "message": "Translated advice string", "spray": "YES/NO/CAUTION", "color": "green/red/orange" }}
                """

                payload = {
                    "model": LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"} 
                }
                headers = {
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000",
                }

                llm_res = requests.post(LLM_API_URL, json=payload, headers=headers)
                
                if llm_res.status_code == 200:
                    llm_data = llm_res.json()
                    content = llm_data['choices'][0]['message']['content']
                    
                    # Clean JSON (remove markdown backticks if AI adds them)
                    clean_json = content.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)

                    advisory_msg = parsed['message']
                    spray_rec = parsed['spray']
                    alert_color = parsed['color']
                    source = f"AI Expert ({LLM_MODEL})"
                else:
                    raise Exception("LLM API returned error")

            except Exception as e:
                print(f"LLM Error: {e}")
                source = "Fallback" # AI failed, go to Layer 3

        # ============================================================
        # ⚠️ LAYER 3: FALLBACK (Basic Logic - Now with Tamil/Marathi!)
        # ============================================================
        if source == "" or source == "Fallback":
            source = "Basic Logic (Fallback)"
            is_rain = "Rain" in condition or "Thunderstorm" in condition
            is_hot = temp > 35

            # --- TAMIL FALLBACK ---
            if "tamil" in lang_lower:
                if is_rain:
                    advisory_msg = f"{city}-il mazhai peiyyum. Poochikolli thelikka vendam." # Or use script: "மழை பெய்யும்..."
                elif is_hot:
                    advisory_msg = "Veppam athigam. Maalaiyil thelikkavum."
                else:
                    advisory_msg = "Vaanilai thelivaaga ullathu. Neengal thelikkalaam."

            # --- MARATHI FALLBACK ---
            elif "marathi" in lang_lower:
                if is_rain:
                    advisory_msg = "Pavsachi shakyata aahe. Fawarni karu naka."
                elif is_hot:
                    advisory_msg = "Tapman jast aahe. Sandhyakali fawarni kara."
                else:
                    advisory_msg = "Havaman saaf aahe. Fawarni karu shakta."

            # --- HINDI FALLBACK ---
            elif "hindi" in lang_lower:
                if is_rain:
                    advisory_msg = "Barish hone wali hai. Spray na karein."
                elif is_hot:
                    advisory_msg = "Garmi jyada hai. Shaam ko spray karein."
                else:
                    advisory_msg = "Mausam saaf hai. Aap spray kar sakte hain."

            # --- ENGLISH (Default) ---
            else:
                if is_rain: 
                    advisory_msg = "Rain expected. Do not spray."
                elif is_hot: 
                    advisory_msg = "High temperature. Spray in the evening."
                else: 
                    advisory_msg = "Weather is clear. Safe to spray."
            
            # Logic for Spray Tag
            if is_rain or is_hot:
                spray_rec = "NO"
                alert_color = "red" if is_rain else "orange"
            else:
                spray_rec = "YES"
                alert_color = "green"

        return {
            "location": city,
            "weather": { "temp": f"{temp}°C", "condition": desc },
            "advisory": {
                "source": source,
                "message": advisory_msg,
                "spray_recommendation": spray_rec,
                "alert_color": alert_color
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))