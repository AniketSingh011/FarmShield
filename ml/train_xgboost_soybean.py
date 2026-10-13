import os
import pandas as pd
import xgboost as xgb

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# --------------------------------------------------
# 1. Load data
# --------------------------------------------------

X = pd.read_csv(r"ml\data\soybean_features.csv")
y = pd.read_csv(r"ml\data\soybean_target.csv").iloc[:, 0]

# --------------------------------------------------
# 2. Remove extremely rare classes
# --------------------------------------------------

counts = y.value_counts()

valid_classes = counts[counts >= 10].index

mask = y.isin(valid_classes)

X = X.loc[mask].reset_index(drop=True)
y = y.loc[mask].reset_index(drop=True)

print("Samples after filtering:", len(X))
print("Classes:", y.nunique())
print("\nClass distribution:")
print(y.value_counts())

# --------------------------------------------------
# 3. Handle missing/unknown values
# --------------------------------------------------

X = X.astype(str)
X = X.replace(["?", "nan", "None"], "UNKNOWN")

# Convert every feature to categorical
for col in X.columns:
    X[col] = X[col].astype("category")

# --------------------------------------------------
# 4. Encode target
# --------------------------------------------------

encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)

# --------------------------------------------------
# 5. Train/test split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.20,
    random_state=42,
    stratify=y_encoded
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# --------------------------------------------------
# 6. XGBoost
# --------------------------------------------------

model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.85,
    colsample_bytree=0.85,
    objective="multi:softprob",
    num_class=len(encoder.classes_),
    eval_metric="mlogloss",
    enable_categorical=True,
    tree_method="hist",
    random_state=42
)

model.fit(X_train, y_train)

# --------------------------------------------------
# 7. Prediction
# --------------------------------------------------

y_pred = model.predict(X_test)

# --------------------------------------------------
# 8. Metrics
# --------------------------------------------------

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)
recall = recall_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)
f1 = f1_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

print("\n==============================")
print("XGBOOST RESULTS")
print("==============================")

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=encoder.classes_,
        zero_division=0
    )
)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# --------------------------------------------------
# 9. Save model
# --------------------------------------------------

os.makedirs(r"ml\models", exist_ok=True)

model.save_model(r"ml\models\farmshield_xgboost_soybean.json")

# Save class mapping
pd.Series(
    encoder.classes_
).to_csv(
    r"ml\models\soybean_classes.csv",
    index=False,
    header=["class"]
)

print("\nModel saved:")
print(r"ml\models\farmshield_xgboost_soybean.json")