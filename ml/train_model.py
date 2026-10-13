import os
import json
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

from xgboost import XGBClassifier


# ============================================================
# FARMShield AI — Crop Health Classification
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR,
    "ml",
    "data",
    "agriculture_dataset_with_target.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "ml",
    "models"
)

os.makedirs(MODEL_DIR, exist_ok=True)


FEATURES = [
    "Soil_Moisture",
    "Soil_Temperature",
    "Soil_pH",
    "Humidity",
    "Air_Temperature",
    "Solar_Radiation",
    "Wind_Speed",
    "NDVI_Index",
    "5G_Latency_ms",
]

TARGET = "Crop_Health"


# ============================================================
# 1. LOAD DATA
# ============================================================

print("Loading dataset...")

df = pd.read_csv(DATA_PATH)

print(f"Dataset loaded: {len(df):,} rows")

X = df[FEATURES]
y = df[TARGET]


# ============================================================
# 2. ENCODE TARGET
# ============================================================

label_mapping = {
    "Healthy": 0,
    "Moderate_Stress": 1,
    "High_Stress": 2,
}

y = y.map(label_mapping)

if y.isnull().any():
    raise ValueError("Unknown target label found.")

print("\nTarget distribution:")
print(df[TARGET].value_counts())


# ============================================================
# 3. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print(f"\nTraining records: {len(X_train):,}")
print(f"Testing records:  {len(X_test):,}")


# ============================================================
# 4. RANDOM FOREST
# ============================================================

print("\n" + "=" * 60)
print("TRAINING RANDOM FOREST")
print("=" * 60)

rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)

rf.fit(X_train, y_train)

rf_pred = rf.predict(X_test)


# ============================================================
# 5. XGBOOST
# ============================================================

print("\n" + "=" * 60)
print("TRAINING XGBOOST")
print("=" * 60)

xgb = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    objective="multi:softmax",
    num_class=3,
    eval_metric="mlogloss",
    random_state=42,
    n_jobs=-1,
)

xgb.fit(X_train, y_train)

xgb_pred = xgb.predict(X_test)


# ============================================================
# 6. EVALUATION FUNCTION
# ============================================================

def evaluate_model(name, y_true, predictions):

    accuracy = accuracy_score(y_true, predictions)

    precision = precision_score(
        y_true,
        predictions,
        average="weighted",
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        predictions,
        average="weighted",
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        predictions,
        average="weighted",
        zero_division=0,
    )

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1 Score : {f1:.4f}")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_true, predictions))

    print("\nClassification Report:")
    print(
        classification_report(
            y_true,
            predictions,
            target_names=[
                "Healthy",
                "Moderate Stress",
                "High Stress",
            ],
            zero_division=0,
        )
    )

    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
    }


# ============================================================
# 7. EVALUATE BOTH
# ============================================================

rf_metrics = evaluate_model(
    "RANDOM FOREST RESULTS",
    y_test,
    rf_pred,
)

xgb_metrics = evaluate_model(
    "XGBOOST RESULTS",
    y_test,
    xgb_pred,
)


# ============================================================
# 8. SELECT BEST MODEL
# ============================================================

if xgb_metrics["accuracy"] > rf_metrics["accuracy"]:
    best_model = xgb
    best_name = "XGBoost"
    best_metrics = xgb_metrics
else:
    best_model = rf
    best_name = "Random Forest"
    best_metrics = rf_metrics


# ============================================================
# 9. SAVE BEST MODEL
# ============================================================

model_path = os.path.join(
    MODEL_DIR,
    "farmshield_crop_health_model.joblib"
)

joblib.dump(best_model, model_path)


# ============================================================
# 10. SAVE METADATA
# ============================================================

metadata = {
    "model": best_name,
    "target": TARGET,
    "features": FEATURES,
    "classes": {
        "0": "Healthy",
        "1": "Moderate_Stress",
        "2": "High_Stress",
    },
    "dataset_rows": len(df),
    "test_size": 0.20,
    "random_state": 42,
    "metrics": best_metrics,
}

metadata_path = os.path.join(
    MODEL_DIR,
    "crop_health_model_metadata.json"
)

with open(metadata_path, "w") as f:
    json.dump(metadata, f, indent=4)


# ============================================================
# 11. FINAL RESULT
# ============================================================

print("\n" + "=" * 60)
print("FARMSHIELD AI — FINAL MODEL")
print("=" * 60)

print(f"Best model: {best_name}")
print(f"Accuracy:   {best_metrics['accuracy']:.4f}")
print(f"Precision:  {best_metrics['precision']:.4f}")
print(f"Recall:     {best_metrics['recall']:.4f}")
print(f"F1 Score:   {best_metrics['f1_score']:.4f}")

print("\nModel saved:")
print(model_path)

print("\nTraining completed successfully.")