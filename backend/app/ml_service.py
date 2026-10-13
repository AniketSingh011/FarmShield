
from pathlib import Path
from typing import Dict, Any, Union

import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "farmshield_early_warning_random_forest.joblib"
)

MODEL = joblib.load(MODEL_PATH)

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


def normalize_growth_stage(
    growth_stage: Union[str, int, float, None]
) -> int:
    """Map crop growth-stage labels to the model's numeric inputs."""
    if growth_stage is None:
        return 3

    if isinstance(growth_stage, str):
        stage = growth_stage.strip().lower().replace("_", " ").replace("-", " ")

        mapping = {
            "seed": 1,
            "germination": 1,
            "seedling": 1,
            "vegetative": 2,
            "flowering": 3,
            "reproductive": 3,
            "fruiting": 3,
            "maturity": 4,
            "mature": 4,
            "harvest": 4,
        }

        if stage in mapping:
            return mapping[stage]

        try:
            growth_stage = float(stage)
        except ValueError:
            return 3

    return max(1, min(4, int(float(growth_stage))))


def calculate_risk_level(probability: float) -> str:
    if probability < 0.40:
        return "LOW"
    if probability < 0.70:
        return "MEDIUM"
    return "HIGH"


def generate_explanation(features: Dict[str, float]) -> list[str]:
    reasons = []

    if features["soil_moisture"] < 25:
        reasons.append("Low soil moisture may indicate water stress.")
    if features["temperature"] > 32:
        reasons.append("High temperature may increase heat stress.")
    if features["humidity"] > 82:
        reasons.append("High humidity may increase crop stress conditions.")
    if features["ndvi"] < 0.55:
        reasons.append("Lower NDVI may indicate reduced vegetation vigor.")
    if features["rainfall"] > 65:
        reasons.append("High recent rainfall may increase excess-moisture risk.")
    if features["soil_ph"] < 5.5 or features["soil_ph"] > 7.5:
        reasons.append("Soil pH is outside the development model's preferred range.")
    if features["wind_speed"] > 15:
        reasons.append("Higher wind speed may increase environmental stress.")

    if not reasons:
        reasons.append(
            "No major development-rule stress factor was detected "
            "from the supplied inputs."
        )

    return reasons


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

    feature_values = {
        "temperature": float(temperature),
        "humidity": float(humidity),
        "rainfall": float(rainfall),
        "soil_moisture": float(soil_moisture),
        "soil_ph": float(soil_ph),
        "wind_speed": float(wind_speed),
        "ndvi": float(ndvi),
        "crop_age": float(crop_age),
        "growth_stage": normalize_growth_stage(growth_stage),
    }

    input_df = pd.DataFrame(
        [[feature_values[name] for name in FEATURES]],
        columns=FEATURES,
    )

    probability = float(MODEL.predict_proba(input_df)[0][1])
    risk_level = calculate_risk_level(probability)
    explanation = generate_explanation(feature_values)

    return {
        "risk_probability": round(probability, 4),
        "risk_percent": round(probability * 100, 2),
        "risk_level": risk_level,
        "primary_risk": explanation[0],
        "secondary_risks": explanation[1:],
        "confidence": round(abs(probability - 0.5) * 2, 4),
        "model_name": "Random Forest",
        "model_version": "development-1.0",
        "mode": "DEMO",
        "is_demo": True,
        "explanation": explanation,
    }
