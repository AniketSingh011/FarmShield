from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        String(50),
        default="FARMER",
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    farms = relationship(
        "Farm",
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(255),
        nullable=False,
    )

    location = Column(
        String(255),
        nullable=False,
    )

    latitude = Column(
        Float,
        nullable=True,
    )

    longitude = Column(
        Float,
        nullable=True,
    )

    area = Column(
        Float,
        nullable=False,
    )

    area_unit = Column(
        String(50),
        default="acres",
    )

    soil_type = Column(
        String(100),
        nullable=True,
    )

    irrigation_type = Column(
        String(100),
        nullable=True,
    )

    soil_ph = Column(
        Float,
        nullable=True,
    )

    soil_moisture = Column(
        Float,
        nullable=True,
    )

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    owner = relationship(
        "User",
        back_populates="farms",
    )

    crops = relationship(
        "Crop",
        back_populates="farm",
        cascade="all, delete-orphan",
    )


class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True)

    crop = Column(
        String(100),
        nullable=False,
    )

    variety = Column(
        String(100),
        nullable=True,
    )

    planting_date = Column(
        Date,
        nullable=True,
    )

    growth_stage = Column(
        String(100),
        nullable=True,
    )

    area = Column(
        Float,
        nullable=True,
    )

    irrigation_method = Column(
        String(100),
        nullable=True,
    )

    expected_harvest_date = Column(
        Date,
        nullable=True,
    )

    farm_id = Column(
        Integer,
        ForeignKey("farms.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    farm = relationship(
        "Farm",
        back_populates="crops",
    )


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Kept because the existing database requires farm_id.
    farm_id = Column(
        Integer,
        ForeignKey("farms.id"),
        nullable=False,
    )

    crop_id = Column(
        Integer,
        ForeignKey("crops.id"),
        nullable=False,
    )

    risk_probability = Column(
        Float,
        nullable=False,
    )

    risk_level = Column(
        String(50),
        nullable=False,
    )

    primary_risk = Column(
        String(255),
        nullable=False,
    )

    secondary_risks = Column(
        Text,
        nullable=True,
    )

    confidence = Column(
        Float,
        nullable=False,
    )

    critical_period = Column(
        String(255),
        nullable=True,
    )

    # Existing database has this column.
    mode = Column(
        String(50),
        default="DEMO",
        nullable=True,
    )

    is_demo = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    model_name = Column(
        String(100),
        default="Random Forest",
        nullable=True,
    )

    model_version = Column(
        String(100),
        default="dev-1.0",
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    farm = relationship(
        "Farm",
    )

    crop = relationship(
        "Crop",
    )