import google.generativeai as genai
import os

# Test Gemini API directly
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in environment")
    exit(1)

try:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Try new model name
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # Simple test
    response = model.generate_content("What is 2+2?")
    print(f"✅ Gemini Test Successful: {response.text}")
    
except Exception as e:
    print(f"❌ Gemini Test Failed: {e}")
    
    # Try old model name
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("What is 2+2?")
        print(f"✅ Gemini 1.5-flash works: {response.text}")
    except Exception as e2:
        print(f"❌ Both models failed: {e2}")