from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any
from datetime import datetime, timedelta

router = APIRouter(tags=["Auth & Security"])

# --- MOCK USER DATABASE ---
# Asliyat mein ye database se aayega
MOCK_USERS = {
    "kisan": {
        "username": "kisan",
        "password": "password123", # Plain text for simplicity, usually needs hashing
        "farmer_id": "123e4567-e89b-12d3-a456-426614174000"
    }
}

# --- MOCK JWT GENERATION ---
# Ye asal mein JWT nahi hai, bas ek random string hai jo token jaisa lagega
def create_mock_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Creates a predictable, long-lasting mock token for demonstration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=365) # 1 saal ka token
    
    # Ye ek base64 encoded string jaisa dikhega
    token_data = f"{to_encode['sub']}|{expire.isoformat()}|HACKATHON_TOKEN_SECURE"
    # Note: Asli JWT nahi banaya, simple string return kiya hai.
    return token_data.encode('utf-8').hex() 

# --- ENDPOINT ---
@router.post("/auth/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = MOCK_USERS.get(form_data.username)
    
    # 1. Credentials Check
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 2. Token Generation (Mock)
    access_token = create_mock_access_token(data={"sub": user["username"]})
    
    # 3. Return Token & User ID
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "farmer_id": user["farmer_id"], # Frontend is farmer_id ko use karega
        "username": user["username"]
    }