import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    top_k_accuracy_score,
)


BASE_DIR = Path(__file__).resolve().parents[1]

FEATURE_FILE = BASE_DIR / "ml" / "data" / "soybean_features.csv"
TARGET_FILE = BASE_DIR / "ml" / "data" / "soybean_target.csv"

MODEL_DIR = BASE_DIR / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

X = pd.read_csv(FEATURE_FILE)
y = pd.read_csv(TARGET_FILE).iloc[:, 0]

# Keep classes with at least 10 samples
class_counts = y.value_counts()
valid_classes = class_counts[class_counts >= 10].index

mask = y.isin(valid_classes)

X = X.loc[mask].reset_index(drop=True)
y = y.loc[mask].reset_index(drop=True)

print("=" * 60)
print("FARMSHIELD AI — XGBOOST 5-FOLD VALIDATION")
print("=" * 60)

print(f"\nSamples: {len(X)}")
print(f"Classes: {y.nunique()}")

print("\nClass distribution:")
print(y.value_counts())


# ---------------------------------------------------------
# PREPARE FEATURES
# ---------------------------------------------------------

X = X.astype(str)

X = X.replace(
    ["?", "nan", "None", "NaN"],
    "UNKNOWN"
)

# Convert categorical features to pandas category
for column in X.columns:
    X[column] = X[column].astype("category")


# Encode target
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

num_classes = len(label_encoder.classes_)


# ---------------------------------------------------------
# 5-FOLD STRATIFIED CROSS VALIDATION
# ---------------------------------------------------------

skf = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

results = []

all_true = []
all_pred = []
all_probabilities = []

for fold, (train_idx, test_idx) in enumerate(
    skf.split(X, y_encoded),
    start=1
):

    print(f"\n{'-' * 60}")
    print(f"FOLD {fold}/5")
    print(f"{'-' * 60}")

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y_encoded[train_idx]
    y_test = y_encoded[test_idx]

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        num_class=num_classes,
        eval_metric="mlogloss",
        enable_categorical=True,
        tree_method="hist",
        random_state=42,
    )

    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_test)
    predictions = np.argmax(probabilities, axis=1)

    accuracy = accuracy_score(y_test, predictions)

    precision = precision_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0
    )

    top2 = top_k_accuracy_score(
        y_test,
        probabilities,
        k=2,
        labels=np.arange(num_classes)
    )

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1 Score : {f1:.4f}")
    print(f"Top-2    : {top2:.4f}")

    results.append({
        "fold": fold,
        "accuracy": accuracy,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
        "top2_accuracy": top2,
    })

    all_true.extend(y_test)
    all_pred.extend(predictions)
    all_probabilities.extend(probabilities)


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

results_df = pd.DataFrame(results)

print("\n")
print("=" * 60)
print("5-FOLD VALIDATION SUMMARY")
print("=" * 60)

for column in [
    "accuracy",
    "precision_macro",
    "recall_macro",
    "f1_macro",
    "top2_accuracy",
]:

    mean = results_df[column].mean()
    std = results_df[column].std()

    print(
        f"{column:20s}: "
        f"{mean:.4f} ± {std:.4f}"
    )


# ---------------------------------------------------------
# SAVE RESULTS
# ---------------------------------------------------------

validation_results = {
    "dataset": "UCI Soybean Large",
    "samples": int(len(X)),
    "classes": int(num_classes),
    "cross_validation": "5-fold stratified",
    "metrics": {
        column: {
            "mean": float(results_df[column].mean()),
            "std": float(results_df[column].std()),
        }
        for column in [
            "accuracy",
            "precision_macro",
            "recall_macro",
            "f1_macro",
            "top2_accuracy",
        ]
    },
    "fold_results": results,
    "development_only": True,
    "note": (
        "This validation evaluates the UCI Soybean disease "
        "classification experiment. It is not FarmShield "
        "real-world early-warning accuracy."
    ),
}

output_file = MODEL_DIR / "validation_results.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(validation_results, f, indent=4)


# Save fold metrics
results_df.to_csv(
    MODEL_DIR / "soybean_5fold_metrics.csv",
    index=False
)


print("\nValidation files saved:")
print(output_file)
print(
    MODEL_DIR / "soybean_5fold_metrics.csv"
)

print("\nValidation complete.")