import ee

print("🌍 Authenticating with Google Earth Engine...")

# Ye command browser open karega permission ke liye
try:
    ee.Authenticate(force=True)
    ee.Initialize(project='youtube-automation-483920')
    print("✅ Success! GEE is now connected to this laptop.")
except Exception as e:
    print(f"❌ Error: {e}")