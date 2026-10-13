from pathlib import Path
from typing import Dict, Any, Union

import joblib
import pandas as pd


# --------------------------------------------------
# MODEL PATH
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "farmshield_early_warning_random_forest.joblib"
)


# --------------------------------------------------
# LOAD TRAINED MODEL
# --------------------------------------------------

MODEL = joblib.load(MODEL_PATH)


# These MUST remain in the same order used during training.
FEATURES = [
    "temperature",
    "humidity",
    "rainfall",
    "soil_moisture",
    "soil_ph",
    "wind_speed",
    "ndvi",
    "crop_age",
    "growth_stage",
]


# --------------------------------------------------
# GROWTH-STAGE NORMALIZATION
# --------------------------------------------------

def normalize_growth_stage(
    growth_stage: Union[str, int, float, None]
) -> int:
    """
    Convert the crop's stored growth-stage value into the
    numeric representation expected by the development model.

    Development mapping:

        1 = seedling / germination
        2 = vegetative
        3 = flowering / reproductive
        4 = maturity / harvest

    The ML model was trained using numeric stages 1-4.
    """

    if growth_stage is None:
        return 3

    # Already numeric
    if isinstance(growth_stage, (int, float)):
        value = int(growth_stage)

        if value < 1:
            return 1

        if value > 4:
            return 4

        return value

    # Text representation
    stage = str(growth_stage).strip().lower()

    stage_mapping = {
        "seed": 1,
        "germination": 1,
        "germination stage": 1,
        "seedling": 1,
        "seedling stage": 1,

        "vegetative": 2,
        "vegetative stage": 2,
        "vegetative growth": 2,
        "growth": 2,

        "flowering": 3,
        "flowering stage": 3,
        "reproductive": 3,
        "reproductive stage": 3,
        "fruiting": 3,
        "fruiting stage": 3,

        "maturity": 4,
        "mature": 4,
        "maturity stage": 4,
        "harvest": 4,
        "harvesting": 4,
    }

    return stage_mapping.get(stage, 3)


# --------------------------------------------------
# RISK LEVEL
# --------------------------------------------------

def calculate_risk_level(probability: float) -> str:
    """
    Convert model probability into FarmShield risk levels.

    These are development thresholds only.
    They are NOT agronomically validated thresholds.
    """

    if probability < 0.40:
        return "LOW"

    if probability < 0.70:
        return "MEDIUM"

    return "HIGH"


# --------------------------------------------------
# EXPLANATION
# --------------------------------------------------

def generate_explanation(
    features: Dict[str, float]
) -> list[str]:

    reasons = []

    if features["soil_moisture"] < 25:
        reasons.append(
            "Low soil moisture may indicate water stress."
        )

    if features["temperature"] > 32:
        reasons.append(
            "High temperature may increase heat stress."
        )

    if features["humidity"] > 82:
        reasons.append(
            "High humidity may increase crop stress conditions."
        )

    if features["ndvi"] < 0.55:
        reasons.append(
            "Lower NDVI may indicate reduced vegetation vigor."
        )

    if features["rainfall"] > 65:
        reasons.append(
            "High recent rainfall may increase excess-moisture risk."
        )

    if (
        features["soil_ph"] < 5.5
        or features["soil_ph"] > 7.5
    ):
        reasons.append(
            "Soil pH is outside the development model's preferred range."
        )

    if features["wind_speed"] > 15:
        reasons.append(
            "Higher wind speed may increase environmental stress."
        )

    if not reasons:
        reasons.append(
            "No major development-rule stress factor was detected "
            "from the supplied inputs."
        )

    return reasons


# --------------------------------------------------
# PREDICTION
# --------------------------------------------------

def predict_crop_risk(
    temperature: float,
    humidity: float,
    rainfall: float,
    soil_moisture: float,
    soil_ph: float,
    wind_speed: float,
    ndvi: float,
    crop_age: int,
    growth_stage: Union[str, int, float, None],
) -> Dict[str, Any]:

    # Convert text stages such as "vegetative"
    # into the numeric representation used during training.
    normalized_growth_stage = normalize_growth_stage(
        growth_stage
    )

    feature_values = {
        "temperature": float(temperature),
        "humidity": float(humidity),
        "rainfall": float(rainfall),
        "soil_moisture": float(soil_moisture),
        "soil_ph": float(soil_ph),
        "wind_speed": float(wind_speed),
        "ndvi": float(ndvi),
        "crop_age": int(crop_age),
        "growth_stage": normalized_growth_stage,
    }

    # --------------------------------------------------
    # CREATE MODEL INPUT
    # --------------------------------------------------

    input_df = pd.DataFrame(
        [[
            feature_values["temperature"],
            feature_values["humidity"],
            feature_values["rainfall"],
            feature_values["soil_moisture"],
            feature_values["soil_ph"],
            feature_values["wind_speed"],
            feature_values["ndvi"],
            feature_values["crop_age"],
            feature_values["growth_stage"],
        ]],
        columns=FEATURES,
    )

    # --------------------------------------------------
    # MODEL PREDICTION
    # --------------------------------------------------

    probability = float(
        MODEL.predict_proba(input_df)[0][1]
    )

    risk_level = calculate_risk_level(
        probability
    )

    explanation = generate_explanation(
        feature_values
    )

    # Development confidence indicator.
    confidence = abs(probability - 0.5) * 2

    return {
        "risk_probability": round(
            probability,
            4,
        ),

        "risk_percent": round(
            probability * 100,
            2,
        ),

        "risk_level": risk_level,

        "primary_risk": (
            explanation[0]
            if explanation
            else "No major development-rule risk detected."
        ),

        "secondary_risks": explanation[1:],

        "confidence": round(
            confidence,
            4,
        ),

        "model_name": "Random Forest",

        "model_version": "development-1.0",

        "mode": "DEMO",

        "is_demo": True,

        "explanation": explanation,
    }