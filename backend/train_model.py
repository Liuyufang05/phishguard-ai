
import sys
from pathlib import Path

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

# =====================================
# 1. KHAI BAO DUONG DAN
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "dataset" / "url_dataset.csv"
MODEL_DIR = BASE_DIR / "models"

MODEL_DIR.mkdir(exist_ok=True)

# Cho phep import feature_extractor
sys.path.insert(0, str(Path(__file__).resolve().parent))

from feature_extractor import extract_features

print("=" * 55)
print("PHISHGUARD AI - MACHINE LEARNING TRAINING")
print("=" * 55)

# =====================================
# 2. DOC DU LIEU
# =====================================

if not DATA_FILE.exists():
    raise FileNotFoundError(
        "Khong tim thay dataset/url_dataset.csv. "
        "Hay chay prepare_dataset.py truoc."
    )

df = pd.read_csv(DATA_FILE)

df = df.dropna(subset=["url", "label"])

df["url"] = df["url"].astype(str)
df["label"] = pd.to_numeric(df["label"], errors="coerce")

df = df.dropna(subset=["label"])
df["label"] = df["label"].astype(int)

if set(df["label"].unique()) != {0, 1}:
    raise ValueError("Dataset phai co ca hai nhan 0 va 1.")

print("\nTong so URL:", len(df))
print("Phishing:", (df["label"] == 1).sum())
print("Benign:", (df["label"] == 0).sum())

# =====================================
# 3. TRICH XUAT DAC TRUNG
# =====================================

print("\nDang trich xuat dac trung URL...")

feature_data = []

for url in df["url"]:
    feature_data.append(extract_features(url))

X = pd.DataFrame(feature_data)
y = df["label"]

print("So dac trung:", X.shape[1])
print("Ten dac trung:", list(X.columns))

# =====================================
# 4. CHIA TRAIN VA TEST
# =====================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("\nDu lieu huan luyen:", len(X_train))
print("Du lieu kiem tra:", len(X_test))

# =====================================
# 5. KHAI BAO CAC MO HINH
# =====================================

models = {
    "Logistic Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(
            max_iter=1000,
            class_weight="balanced"
        ))
    ]),

    "Decision Tree": DecisionTreeClassifier(
        max_depth=10,
        class_weight="balanced",
        random_state=42
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    ),

    "SVM": Pipeline([
        ("scaler", StandardScaler()),
        ("model", SVC(
            kernel="rbf",
            probability=True,
            class_weight="balanced",
            random_state=42
        ))
    ])
}

# =====================================
# 6. HUAN LUYEN VA DANH GIA
# =====================================

results = []
trained_models = {}

for name, model in models.items():

    print("\nDang huan luyen:", name)

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(
        y_test, predictions, zero_division=0
    )
    recall = recall_score(
        y_test, predictions, zero_division=0
    )
    f1 = f1_score(
        y_test, predictions, zero_division=0
    )
    auc = roc_auc_score(y_test, probabilities)

    results.append({
        "Model": name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1-score": f1,
        "ROC-AUC": auc
    })

    trained_models[name] = model

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1-score : {f1:.4f}")
    print(f"ROC-AUC  : {auc:.4f}")

# =====================================
# 7. SO SANH CAC MO HINH
# =====================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by=["Recall", "F1-score"],
    ascending=False
)

print("\n" + "=" * 65)
print("KET QUA SO SANH CAC MO HINH")
print("=" * 65)

print(results_df.to_string(index=False))

results_df.to_csv(
    MODEL_DIR / "model_comparison.csv",
    index=False
)

# =====================================
# 8. LUA CHON MO HINH
# =====================================

best_name = results_df.iloc[0]["Model"]
best_model = trained_models[best_name]

# =====================================
# 9. LUU MO HINH
# =====================================

model_package = {
    "model": best_model,
    "feature_names": list(X.columns),
    "model_name": best_name,
    "version": "1.0.0"
}

joblib.dump(
    model_package,
    MODEL_DIR / "phishguard_model.pkl"
)

# =====================================
# 10. CONFUSION MATRIX
# =====================================

best_predictions = best_model.predict(X_test)

print("\nMO HINH DUOC LUA CHON:", best_name)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, best_predictions))

print("\nClassification Report:")
print(classification_report(
    y_test,
    best_predictions,
    target_names=["Benign", "Phishing"],
    zero_division=0
))

print("\nDa luu mo hinh tai:")
print(MODEL_DIR / "phishguard_model.pkl")

print("\nHOAN THANH HUAN LUYEN PHISHGUARD AI!")
