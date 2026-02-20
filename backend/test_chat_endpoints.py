"""
Test Chat Endpoints
Simple script to test if chat.py and chatbot_agent.py are working
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"

def test_chat_without_image():
    """Test text-only chat endpoint"""
    print("\n" + "="*50)
    print("Testing: /api/chat/message (text-only)")
    print("="*50)
    
    url = f"{BASE_URL}/api/chat/message"
    payload = {
        "message": "What are the best practices for tomato farming?",
        "farmer_id": "test_farmer_123",
        "language": "en"
    }
    
    try:
        print(f"Sending request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"Provider: {data.get('provider', 'unknown')}")
            print(f"Response: {data.get('ai_response', 'No response')[:200]}...")
            return True
        else:
            print(f"❌ FAILED!")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_chat_with_image():
    """Note: This requires a test image file"""
    print("\n" + "="*50)
    print("Testing: /api/chat/with-image (image + text)")
    print("="*50)
    print("⚠️ Skipped - requires test image file")
    print("  To test manually, use curl:")
    print('  curl -X POST "http://localhost:8000/api/chat/with-image" \\')
    print('    -F "file=@/path/to/plant/image.jpg" \\')
    print('    -F "message=What disease is this?" \\')
    print('    -F "farmer_id=test_farmer"')


if __name__ == "__main__":
    print("\n🌾 AgroGuard Chat Endpoint Tests\n")
    
    # Test 1: Text-only chat
    result = test_chat_without_image()
    
    # Test 2: Image chat (manual test instructions)
    test_chat_with_image()
    
    print("\n" + "="*50)
    if result:
        print("✅ Tests PASSED!")
    else:
        print("❌ Tests FAILED - check backend logs")
    print("="*50 + "\n")
