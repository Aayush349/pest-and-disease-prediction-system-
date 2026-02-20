from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.sql_models import Farmer, FarmField
from ..models.schemas import (
    FarmerProfileResponse,
    FarmerProfileUpdate,
    FarmFieldCreate,
    FarmFieldResponse,
)
from .auth import get_current_farmer

router = APIRouter(tags=["Farmer Profile"])


# --- Get Profile ---
@router.get("/farmer/profile", response_model=FarmerProfileResponse)
async def get_profile(farmer: Farmer = Depends(get_current_farmer)):
    return FarmerProfileResponse(
        id=farmer.id,
        name=farmer.name,
        phone=farmer.phone,
        email=farmer.email,
        location=farmer.location,
        state=farmer.state,
        district=farmer.district,
        farm_size=farmer.farm_size,
        crops=farmer.crops,
        created_at=farmer.created_at.isoformat() if farmer.created_at else "",
        fields=[
            FarmFieldResponse(
                id=f.id,
                field_name=f.field_name,
                area_acres=f.area_acres,
                crop=f.crop,
                soil_type=f.soil_type,
                irrigation_type=f.irrigation_type,
                sowing_date=f.sowing_date,
            )
            for f in farmer.fields
        ],
    )


# --- Update Profile ---
@router.put("/farmer/profile", response_model=FarmerProfileResponse)
async def update_profile(
    data: FarmerProfileUpdate,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(farmer, key, value)

    db.commit()
    db.refresh(farmer)

    return FarmerProfileResponse(
        id=farmer.id,
        name=farmer.name,
        phone=farmer.phone,
        email=farmer.email,
        location=farmer.location,
        state=farmer.state,
        district=farmer.district,
        farm_size=farmer.farm_size,
        crops=farmer.crops,
        created_at=farmer.created_at.isoformat() if farmer.created_at else "",
        fields=[
            FarmFieldResponse(
                id=f.id,
                field_name=f.field_name,
                area_acres=f.area_acres,
                crop=f.crop,
                soil_type=f.soil_type,
                irrigation_type=f.irrigation_type,
                sowing_date=f.sowing_date,
            )
            for f in farmer.fields
        ],
    )


# --- Add Field ---
@router.post("/farmer/fields", response_model=FarmFieldResponse, status_code=201)
async def add_field(
    data: FarmFieldCreate,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    field = FarmField(
        farmer_id=farmer.id,
        field_name=data.field_name,
        area_acres=data.area_acres,
        crop=data.crop,
        soil_type=data.soil_type,
        irrigation_type=data.irrigation_type,
        sowing_date=data.sowing_date,
    )
    db.add(field)
    db.commit()
    db.refresh(field)

    return FarmFieldResponse(
        id=field.id,
        field_name=field.field_name,
        area_acres=field.area_acres,
        crop=field.crop,
        soil_type=field.soil_type,
        irrigation_type=field.irrigation_type,
        sowing_date=field.sowing_date,
    )


# --- List Fields ---
@router.get("/farmer/fields", response_model=list[FarmFieldResponse])
async def list_fields(
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    fields = db.query(FarmField).filter(FarmField.farmer_id == farmer.id).all()
    return [
        FarmFieldResponse(
            id=f.id,
            field_name=f.field_name,
            area_acres=f.area_acres,
            crop=f.crop,
            soil_type=f.soil_type,
            irrigation_type=f.irrigation_type,
            sowing_date=f.sowing_date,
        )
        for f in fields
    ]


# --- Delete Field ---
@router.delete("/farmer/fields/{field_id}", status_code=204)
async def delete_field(
    field_id: str,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    field = (
        db.query(FarmField)
        .filter(FarmField.id == field_id, FarmField.farmer_id == farmer.id)
        .first()
    )
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    db.delete(field)
    db.commit()
