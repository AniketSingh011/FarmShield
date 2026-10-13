import os
import joblib
import pandas as pd


MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models",
    "random_forest.pkl"
)


model = joblib.load(MODEL_PATH)


FEATURES = [
    "temperature",
    "rainfall",
    "soil_moisture",
    "soil_ph",
    "crop_age_days",
    "humidity"
]


def predict_risk(
    temperature,
    rainfall,
    soil_moisture,
    soil_ph,
    crop_age_days,
    humidity
):
    input_data = pd.DataFrame([{
        "temperature": temperature,
        "rainfall": rainfall,
        "soil_moisture": soil_moisture,
        "soil_ph": soil_ph,
        "crop_age_days": crop_age_days,
        "humidity": humidity
    }])

    probability = float(
        model.predict_proba(input_data)[0][1]
    )

    if probability >= 0.70:
        risk_level = "HIGH"
    elif probability >= 0.40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_probability": round(probability, 4),
        "risk_level": risk_level
    }


if __name__ == "__main__":

    result = predict_risk(
        temperature=38,
        rainfall=20,
        soil_moisture=25,
        soil_ph=6.5,
        crop_age_days=55,
        humidity=70
    )

    print(result)