import json
from datetime import date
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import models, schemas
from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from .ml_service import predict_crop_risk

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FarmShield AI API",
    description="Agricultural crop-stress risk assessment (development/demo mode)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
   allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "FarmShield AI", "status": "running", "mode": "DEMO"}


@app.get("/health")
def health():
    return {"status": "ok", "mode": "DEMO"}


@app.post("/api/v1/auth/register", response_model=schemas.UserResponse)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    role = payload.role.upper()
    if role not in {"FARMER", "EXPERT"}:
        raise HTTPException(status_code=400, detail="Role must be FARMER or EXPERT")

    user = models.User(
        email=email,
        password_hash=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/v1/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(user.id, user.role), "token_type": "bearer"}


@app.get("/api/v1/auth/me", response_model=schemas.UserResponse)
def me(user: models.User = Depends(get_current_user)):
    return user


@app.post("/api/v1/farms", response_model=schemas.FarmResponse)
def create_farm(
    payload: schemas.FarmCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    farm = models.Farm(**payload.model_dump(), owner_id=user.id)
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@app.get("/api/v1/farms", response_model=list[schemas.FarmResponse])
def list_farms(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return db.query(models.Farm).filter(models.Farm.owner_id == user.id).all()


@app.get("/api/v1/farms/{farm_id}", response_model=schemas.FarmResponse)
def get_farm(
    farm_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    farm = db.query(models.Farm).filter(
        models.Farm.id == farm_id,
        models.Farm.owner_id == user.id,
    ).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@app.post("/api/v1/farms/{farm_id}/crops", response_model=schemas.CropResponse)
def create_crop(
    farm_id: int,
    payload: schemas.CropCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    farm = db.query(models.Farm).filter(
        models.Farm.id == farm_id,
        models.Farm.owner_id == user.id,
    ).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    crop = models.Crop(**payload.model_dump(), farm_id=farm_id)
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return crop


@app.get("/api/v1/farms/{farm_id}/crops", response_model=list[schemas.CropResponse])
def list_crops(
    farm_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    farm = db.query(models.Farm).filter(
        models.Farm.id == farm_id,
        models.Farm.owner_id == user.id,
    ).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return db.query(models.Crop).filter(models.Crop.farm_id == farm_id).all()


@app.post(
    "/api/v1/farms/{farm_id}/crops/{crop_id}/risk",
    response_model=schemas.RiskResponse,
)
def assess_crop_risk(
    farm_id: int,
    crop_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    farm = db.query(models.Farm).filter(
        models.Farm.id == farm_id,
        models.Farm.owner_id == user.id,
    ).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    crop = db.query(models.Crop).filter(
        models.Crop.id == crop_id,
        models.Crop.farm_id == farm_id,
    ).first()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    age = (date.today() - crop.planting_date).days if crop.planting_date else 50
    result = predict_crop_risk(
        temperature=38.0,
        humidity=70.0,
        rainfall=20.0,
        soil_moisture=farm.soil_moisture if farm.soil_moisture is not None else 25.0,
        soil_ph=farm.soil_ph if farm.soil_ph is not None else 6.5,
        wind_speed=10.0,
        ndvi=0.45,
        crop_age=max(0, age),
        growth_stage=crop.growth_stage or 3,
    )

    prediction = models.RiskPrediction(
        farm_id=farm_id,
        crop_id=crop_id,
        risk_probability=float(result["risk_probability"]),
        risk_level=result["risk_level"],
        primary_risk=result["primary_risk"],
        secondary_risks=json.dumps(result.get("secondary_risks", [])),
        confidence=float(result["confidence"]),
        critical_period=None,
        mode="DEMO",
        is_demo=True,
        model_name=result.get("model_name", "Random Forest"),
        model_version=result.get("model_version", "development-1.0"),
    )
    db.add(prediction)
    db.commit()

    return {
        "risk_probability": prediction.risk_probability,
        "risk_level": prediction.risk_level,
        "primary_risk": prediction.primary_risk,
        "secondary_risks": result.get("secondary_risks", []),
        "confidence": prediction.confidence,
        "critical_period": None,
        "is_demo": True,
        "model_name": prediction.model_name,
        "model_version": prediction.model_version,
        "explanation": result.get("explanation", []),
    }


@app.get("/api/v1/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    farms = db.query(models.Farm).filter(models.Farm.owner_id == user.id).all()
    farm_ids = [farm.id for farm in farms]
    crops = db.query(models.Crop).filter(models.Crop.farm_id.in_(farm_ids)).all() if farm_ids else []
    predictions = (
        db.query(models.RiskPrediction)
        .filter(models.RiskPrediction.farm_id.in_(farm_ids))
        .order_by(models.RiskPrediction.created_at.desc())
        .limit(10)
        .all()
    ) if farm_ids else []

    return {
        "mode": "DEMO",
        "is_demo": True,
        "farm_count": len(farms),
        "crop_count": len(crops),
        "farms": [
            {
                "id": farm.id,
                "name": farm.name,
                "location": farm.location,
                "crop_count": sum(1 for crop in crops if crop.farm_id == farm.id),
            }
            for farm in farms
        ],
        "recent_predictions": [
            {
                "id": p.id,
                "farm_id": p.farm_id,
                "crop_id": p.crop_id,
                "risk_level": p.risk_level,
                "risk_probability": p.risk_probability,
                "primary_risk": p.primary_risk,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "is_demo": True,
            }
            for p in predictions
        ],
    }
