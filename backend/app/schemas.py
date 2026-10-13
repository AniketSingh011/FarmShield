from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# =========================
# AUTH
# =========================

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "FARMER"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)


# =========================
# FARM
# =========================

class FarmCreate(BaseModel):
    name: str
    location: str

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    area: float
    area_unit: str = "acres"

    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None

    soil_ph: Optional[float] = None
    soil_moisture: Optional[float] = None


class FarmResponse(FarmCreate):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================
# CROP
# =========================

class CropCreate(BaseModel):
    crop: str
    variety: Optional[str] = None

    planting_date: Optional[date] = None
    growth_stage: Optional[str] = None

    area: Optional[float] = None

    irrigation_method: Optional[str] = None
    expected_harvest_date: Optional[date] = None


class CropResponse(CropCreate):
    id: int
    farm_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================
# RISK
# =========================

class RiskResponse(BaseModel):
    risk_probability: float
    risk_level: str
    primary_risk: str
    secondary_risks: list[str]
    confidence: float
    critical_period: Optional[str]
    is_demo: bool
    model_name: str
    model_version: str
    explanation: list[str]