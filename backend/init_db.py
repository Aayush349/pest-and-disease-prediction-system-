# backend/init_db.py
from app.database import engine, Base
# Ab ye line chalegi kyunki tumne sql_models.py bana di hai
from app.models.sql_models import Farmer, Prediction, ChatHistory, FarmField 

print("⏳ Creating database tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Success! 'agroguard.db' file has been created.")
except Exception as e:
    print(f"❌ Error: {e}")