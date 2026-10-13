"""
FarmShield AI - Development Early-Warning Model

IMPORTANT:
This script creates a SYNTHETIC DEVELOPMENT dataset. It is NOT real farm
data and its evaluation metrics must NOT be presented as real-world
FarmShield accuracy.

The labels are generated from a transparent stress-risk simulation using
environmental variables. The purpose is to build/test the ML pipeline
until real labeled farm observations are available.
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from xgboost import XGBClassifier


SEED = 42
N_SAMPLES = 5000

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "ml" / "data"
MODEL_DIR = BASE_DIR / "ml" / "models"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def make_development_dataset(n=N_SAMPLES, seed=SEED):
    rng = np.random.default_rng(seed)

    # Plausible development ranges. These are simulated, not observations.
    temperature = rng.normal(28, 7, n).clip(10, 45)
    humidity = rng.normal(62, 18, n).clip(20, 98)
    rainfall = rng.gamma(shape=2.0, scale=12.0, size=n).clip(0, 100)
    soil_moisture = rng.normal(35, 16, n).clip(5, 85)
    soil_ph = rng.normal(6.5, 0.65, n).clip(4.5, 8.5)
    wind_speed = rng.gamma(shape=2.0, scale=4.0, size=n).clip(0, 30)
    ndvi = rng.normal(0.62, 0.18, n).clip(0.05, 0.95)
    crop_age = rng.integers(10, 181, n)
    growth_stage = rng.integers(1, 5, n)

    # Transparent simulated stress components.
    heat_stress = np.maximum(temperature - 32, 0) / 13
    cold_stress = np.maximum(15 - temperature, 0) / 10
    dry_stress = np.maximum(35 - soil_moisture, 0) / 30
    wet_stress = np.maximum(soil_moisture - 65, 0) / 25
    humidity_stress = np.maximum(humidity - 82, 0) / 18
    rainfall_stress = np.maximum(rainfall - 65, 0) / 35
    ndvi_stress = np.maximum(0.55 - ndvi, 0) / 0.50
    ph_stress = np.maximum(5.5 - soil_ph, 0) / 1.5 + np.maximum(
        soil_ph - 7.5, 0
    ) / 1.5
    wind_stress = np.maximum(wind_speed - 15, 0) / 15

    stress_score = (
        0.20 * heat_stress
        + 0.05 * cold_stress
        + 0.22 * dry_stress
        + 0.10 * wet_stress
        + 0.10 * humidity_stress
        + 0.08 * rainfall_stress
        + 0.15 * ndvi_stress
        + 0.06 * ph_stress
        + 0.04 * wind_stress
    )

    # Small stochastic component prevents a perfectly deterministic boundary.
    stress_score += rng.normal(0, 0.035, n)

    # Binary target:
    # 0 = LOW / normal development condition
    # 1 = ELEVATED_STRESS
    #
    # IMPORTANT: For development only, use a percentile threshold so that
    # the synthetic dataset contains enough positive examples for meaningful
    # recall/F1 testing. This is NOT a claim about the real-world frequency
    # of crop stress.
    development_threshold = np.quantile(stress_score, 0.55)
    target = (stress_score >= development_threshold).astype(int)

    df = pd.DataFrame(
        {
            "temperature": temperature.round(2),
            "humidity": humidity.round(2),
            "rainfall": rainfall.round(2),
            "soil_moisture": soil_moisture.round(2),
            "soil_ph": soil_ph.round(2),
            "wind_speed": wind_speed.round(2),
            "ndvi": ndvi.round(3),
            "crop_age": crop_age,
            "growth_stage": growth_stage,
            "crop_stress_label": target,
        }
    )

    return df


def evaluate_model(name, model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.50).astype(int)

    metrics = {
        "model": name,
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "f1": f1_score(y_test, predictions, zero_division=0),
        "roc_auc": roc_auc_score(y_test, probabilities),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
    }

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)
    print(f"Accuracy : {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall   : {metrics['recall']:.4f}")
    print(f"F1 Score : {metrics['f1']:.4f}")
    print(f"ROC-AUC  : {metrics['roc_auc']:.4f}")
    print("\nConfusion Matrix:")
    print(np.array(metrics["confusion_matrix"]))
    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            target_names=["LOW", "ELEVATED_STRESS"],
            zero_division=0,
        )
    )

    return model, metrics


def main():
    print("=" * 60)
    print("FARMSHIELD AI - EARLY WARNING DEVELOPMENT MODEL")
    print("=" * 60)
    print("\n*** SYNTHETIC DEVELOPMENT DATA — NOT REAL FARM DATA ***\n")

    df = make_development_dataset()

    dataset_path = DATA_DIR / "early_warning_development.csv"
    df.to_csv(dataset_path, index=False)

    print(f"Generated samples: {len(df)}")
    print("\nTarget distribution:")
    print(df["crop_stress_label"].value_counts().sort_index())
    print(f"\nDataset saved: {dataset_path}")

    X = df.drop(columns=["crop_stress_label"])
    y = df["crop_stress_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=SEED,
    )

    print(f"\nTraining samples: {len(X_train)}")
    print(f"Testing samples : {len(X_test)}")

    rf = RandomForestClassifier(
        n_estimators=400,
        max_depth=8,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=SEED,
        n_jobs=-1,
    )

    xgb_model = XGBClassifier(
        n_estimators=350,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.90,
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        random_state=SEED,
    )

    rf, rf_metrics = evaluate_model(
        "RANDOM FOREST",
        rf,
        X_train,
        X_test,
        y_train,
        y_test,
    )

    xgb_model, xgb_metrics = evaluate_model(
        "XGBOOST",
        xgb_model,
        X_train,
        X_test,
        y_train,
        y_test,
    )

    # 5-fold CV on the training set for stability.
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    rf_cv = cross_val_score(
        rf,
        X_train,
        y_train,
        cv=cv,
        scoring="f1",
        n_jobs=-1,
    )

    xgb_cv = cross_val_score(
        xgb_model,
        X_train,
        y_train,
        cv=cv,
        scoring="f1",
        n_jobs=1,
    )

    print("\n" + "=" * 60)
    print("5-FOLD TRAINING-SET CROSS-VALIDATION (F1)")
    print("=" * 60)
    print(f"Random Forest: {rf_cv.mean():.4f} ± {rf_cv.std():.4f}")
    print(f"XGBoost      : {xgb_cv.mean():.4f} ± {xgb_cv.std():.4f}")

    # Feature importance from XGBoost.
    importance = pd.DataFrame(
        {
            "feature": X.columns,
            "importance": xgb_model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    print("\nXGBoost feature importance:")
    print(importance.to_string(index=False))

    importance.to_csv(
        MODEL_DIR / "early_warning_xgboost_feature_importance.csv",
        index=False,
    )

    # Save XGBoost model.
    xgb_model.save_model(
        MODEL_DIR / "farmshield_early_warning_xgboost.json"
    )

    # Save RF model using joblib.
    import joblib

    joblib.dump(
        rf,
        MODEL_DIR / "farmshield_early_warning_random_forest.joblib",
    )

    results = {
        "dataset": "FarmShield Synthetic Early-Warning Development Dataset",
        "samples": int(len(df)),
        "features": list(X.columns),
        "target": "crop_stress_label",
        "label_definition": {
            "0": "LOW / normal development condition",
            "1": "ELEVATED_STRESS",
        },
        "data_status": "SYNTHETIC_DEVELOPMENT_ONLY",
        "warning": (
            "Metrics must not be represented as real-world FarmShield "
            "accuracy. Labels are generated from a transparent simulation "
            "until real labeled farm observations are available."
        ),
        "random_forest": {
            **{k: v for k, v in rf_metrics.items()},
            "cv_f1_mean": float(rf_cv.mean()),
            "cv_f1_std": float(rf_cv.std()),
        },
        "xgboost": {
            **{k: v for k, v in xgb_metrics.items()},
            "cv_f1_mean": float(xgb_cv.mean()),
            "cv_f1_std": float(xgb_cv.std()),
        },
    }

    with open(
        MODEL_DIR / "early_warning_validation_results.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(results, f, indent=4)

    print("\n" + "=" * 60)
    print("FILES SAVED")
    print("=" * 60)
    print(DATA_DIR / "early_warning_development.csv")
    print(MODEL_DIR / "farmshield_early_warning_xgboost.json")
    print(MODEL_DIR / "farmshield_early_warning_random_forest.joblib")
    print(MODEL_DIR / "early_warning_xgboost_feature_importance.csv")
    print(MODEL_DIR / "early_warning_validation_results.json")

    print("\nTraining complete.")


if __name__ == "__main__":
    main()
