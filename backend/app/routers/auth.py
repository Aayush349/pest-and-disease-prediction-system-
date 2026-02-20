from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt

from ..database import get_db
from ..models.sql_models import Farmer
from ..models.schemas import FarmerSignup
from ..config import get_settings

router = APIRouter(tags=["Auth & Security"])
settings = get_settings()

# --- OAuth2 scheme ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# --- Dependency: get current farmer from JWT ---
async def get_current_farmer(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Farmer:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        farmer_id: str = payload.get("sub")
        if farmer_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if farmer is None:
        raise credentials_exception
    return farmer


# --- Signup ---
@router.post("/auth/signup")
async def signup(data: FarmerSignup, db: Session = Depends(get_db)):
    # Check if phone already registered
    existing = db.query(Farmer).filter(Farmer.phone == data.phone).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered",
        )

    farmer = Farmer(
        name=data.name,
        phone=data.phone,
        password_hash=hash_password(data.password),
        location=data.location,
        email=data.email,
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)

    access_token = create_access_token(data={"sub": farmer.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "farmer_id": farmer.id,
        "username": farmer.name,
    }


# --- Login (uses OAuth2PasswordRequestForm for compatibility) ---
@router.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Username field carries the phone number
    farmer = db.query(Farmer).filter(Farmer.phone == form_data.username).first()

    if not farmer or not verify_password(form_data.password, farmer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": farmer.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "farmer_id": farmer.id,
        "username": farmer.name,
    }