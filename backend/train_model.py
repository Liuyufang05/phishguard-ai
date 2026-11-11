import sys
from pathlib import Path
from urllib.parse import urlparse

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import VarianceThreshold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "dataset" / "url_dataset.csv"
MODEL_DIR = BASE_DIR / "models"
CANDIDATE_MODEL_FILE = MODEL_DIR / "phishguard_candidate.pkl"
N_SPLITS = 5
CALIBRATION_SPLITS = 3
RANDOM_STATE = 42

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.feature_extractor import (  # noqa: E402
    FEATURE_NAMES,
    URLFeatureTransformer,
    extract_features,
)


def hostname_group(url):
    candidate = str(url).strip()
    if "://" not in candidate:
        candidate = "http://" + candidate

    try:
        hostname = urlparse(candidate).hostname
    except ValueError:
        hostname = None

    return (hostname or candidate).lower().rstrip(".")


def clean_dataset(df):
    required_columns = {"url", "label"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(
            "Dataset must contain columns: url, label."
        )

    cleaned = df.dropna(subset=["url", "label"]).copy()
    cleaned["url"] = cleaned["url"].astype(str).str.strip()
    cleaned["label"] = pd.to_numeric(cleaned["label"], errors="coerce")
    cleaned = cleaned.dropna(subset=["label"])
    cleaned = cleaned[cleaned["url"].ne("")]

    if not cleaned["label"].isin([0, 1]).all():
        raise ValueError("Dataset labels must be 0 or 1.")

    cleaned["label"] = cleaned["label"].astype(int)
    if set(cleaned["label"].unique()) != {0, 1}:
        raise ValueError("Dataset must contain both labels 0 and 1.")

    conflicting_urls = (
        cleaned.groupby("url")["label"].nunique().gt(1)
    )
    if conflicting_urls.any():
        raise ValueError(
            "Dataset contains URLs with conflicting labels."
        )

    return cleaned.drop_duplicates(subset=["url"]).reset_index(drop=True)


def source_label_warnings(df):
    if "source" not in df.columns:
        return [
            "Dataset has no source metadata; source-label bias cannot be audited."
        ]

    normalized_sources = df["source"].astype("string").str.strip()
    missing_sources = normalized_sources.isna() | normalized_sources.eq("")
    warnings = []
    if missing_sources.any():
        warnings.append("Some dataset rows are missing source metadata.")

    source_labels = pd.DataFrame({
        "source": normalized_sources[~missing_sources],
        "label": df.loc[~missing_sources, "label"],
    }).groupby("source")["label"].nunique()
    if source_labels.empty:
        warnings.append("Dataset source metadata is empty.")
        return warnings
    if source_labels.eq(1).all():
        warnings.append(
            "Each source maps to a single label; metrics may reflect "
            "source-specific patterns."
        )

    return warnings


def make_group_splits(urls, labels, n_splits=N_SPLITS):
    groups = np.asarray([hostname_group(url) for url in urls])
    class_group_counts = pd.DataFrame(
        {"label": labels, "group": groups}
    ).drop_duplicates()["label"].value_counts()
    if len(class_group_counts) != 2 or class_group_counts.min() < n_splits:
        raise ValueError(
            f"Need at least {n_splits} distinct hostnames in each class "
            "for stratified group validation."
        )

    splitter = StratifiedGroupKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=RANDOM_STATE,
    )
    splits = list(splitter.split(urls, labels, groups))

    for train_indices, validation_indices in splits:
        if set(labels[train_indices]) != {0, 1}:
            raise ValueError("A training fold is missing a class.")
        if set(labels[validation_indices]) != {0, 1}:
            raise ValueError("A validation fold is missing a class.")
        if set(groups[train_indices]) & set(groups[validation_indices]):
            raise ValueError("Hostname leakage detected between folds.")

    return splits


def calibrated_model(estimator, urls, labels):
    return CalibratedClassifierCV(
        estimator=clone(estimator),
        method="sigmoid",
        cv=make_group_splits(
            urls,
            labels,
            n_splits=CALIBRATION_SPLITS,
        ),
        ensemble=False,
    )


def build_models():
    numeric_models = {
        "Logistic Regression": Pipeline([
            ("variance", VarianceThreshold()),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            )),
        ]),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=10,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "SVM": Pipeline([
            ("variance", VarianceThreshold()),
            ("scaler", StandardScaler()),
            ("model", SVC(
                kernel="rbf",
                class_weight="balanced",
                random_state=RANDOM_STATE,
            )),
        ]),
    }

    character_model = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char",
            ngram_range=(3, 5),
            min_df=2,
            max_features=150_000,
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("model", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )),
    ])

    hybrid_model = Pipeline([
        ("features", FeatureUnion([
            ("character_ngrams", TfidfVectorizer(
                analyzer="char",
                ngram_range=(3, 5),
                min_df=2,
                max_features=150_000,
                sublinear_tf=True,
                strip_accents="unicode",
            )),
            ("url_features", Pipeline([
                ("extract", URLFeatureTransformer()),
                ("scale", StandardScaler(with_mean=False)),
            ])),
        ])),
        ("model", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )),
    ])

    return {
        **{
            name: ("url_features", model)
            for name, model in numeric_models.items()
        },
        "Character n-gram": ("url_text", character_model),
        "Hybrid URL": ("url_text", hybrid_model),
    }


def score_model(y_true, predictions, probabilities):
    true_negatives, false_positives, _, _ = confusion_matrix(
        y_true,
        predictions,
        labels=[0, 1],
    ).ravel()

    return {
        "Accuracy": accuracy_score(y_true, predictions),
        "Precision": precision_score(y_true, predictions, zero_division=0),
        "Recall": recall_score(y_true, predictions, zero_division=0),
        "F1-score": f1_score(y_true, predictions, zero_division=0),
        "ROC-AUC": roc_auc_score(y_true, probabilities),
        "PR-AUC": average_precision_score(y_true, probabilities),
        "False-positive rate": (
            false_positives / (true_negatives + false_positives)
            if true_negatives + false_positives
            else 0.0
        ),
        "Brier score": brier_score_loss(y_true, probabilities),
    }


def cross_validate_model(model, input_type, urls, features, labels, splits):
    predictions = np.empty(len(labels), dtype=int)
    probabilities = np.empty(len(labels), dtype=float)

    for train_indices, validation_indices in splits:
        train_input = (
            urls[train_indices]
            if input_type == "url_text"
            else features.iloc[train_indices]
        )
        validation_input = (
            urls[validation_indices]
            if input_type == "url_text"
            else features.iloc[validation_indices]
        )

        fold_urls = urls[train_indices]
        fold_labels = labels[train_indices]
        fold_model = calibrated_model(model, fold_urls, fold_labels)
        fold_model.fit(train_input, labels[train_indices])
        predictions[validation_indices] = fold_model.predict(
            validation_input
        )
        classes = list(fold_model.classes_)
        phishing_index = classes.index(1)
        probabilities[validation_indices] = fold_model.predict_proba(
            validation_input
        )[:, phishing_index]

    return score_model(labels, predictions, probabilities), predictions


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "Khong tim thay dataset/url_dataset.csv. "
            "Hay chay prepare_dataset.py truoc."
        )

    df = clean_dataset(pd.read_csv(DATA_FILE))
    urls = df["url"].to_numpy(dtype=str)
    labels = df["label"].to_numpy(dtype=int)
    groups = np.asarray([hostname_group(url) for url in urls])
    features = pd.DataFrame([
        extract_features(url)
        for url in urls
    ], columns=FEATURE_NAMES)
    splits = make_group_splits(urls, labels)

    print("=" * 65)
    print("PHISHGUARD AI - HOSTNAME-GROUPED CROSS-VALIDATION")
    print("=" * 65)
    print(f"URLs after cleaning: {len(df)}")
    print(f"Benign: {(labels == 0).sum()} | Phishing: {(labels == 1).sum()}")
    print(f"Unique hostnames: {len(np.unique(groups))}")
    print(f"Validation folds: {len(splits)}")
    print("Features:", list(FEATURE_NAMES))
    data_warnings = source_label_warnings(df)
    if "source" in df.columns:
        print("\nSource/label counts:")
        print(pd.crosstab(df["source"], df["label"]).to_string())
    for warning in data_warnings:
        print(f"WARNING: {warning}")

    models = build_models()
    results = []
    predictions_by_model = {}
    for name, (input_type, model) in models.items():
        print(f"\nEvaluating: {name}")
        metrics, predictions = cross_validate_model(
            model,
            input_type,
            urls,
            features,
            labels,
            splits,
        )
        results.append({
            "Model": name,
            "Input type": input_type,
            **metrics,
        })
        predictions_by_model[name] = predictions
        print(", ".join(
            f"{metric}: {value:.4f}"
            for metric, value in metrics.items()
        ))

    results_df = pd.DataFrame(results).sort_values(
        by=["F1-score", "Recall", "Precision", "PR-AUC"],
        ascending=False,
    ).reset_index(drop=True)

    print("\n" + results_df.to_string(index=False))
    MODEL_DIR.mkdir(exist_ok=True)
    results_df.to_csv(MODEL_DIR / "model_comparison.csv", index=False)

    best_name = results_df.iloc[0]["Model"]
    best_input_type, best_template = models[best_name]
    final_input = urls if best_input_type == "url_text" else features
    best_model = calibrated_model(best_template, urls, labels)
    best_model.fit(final_input, labels)

    best_predictions = results_df.iloc[0]
    model_package = {
        "model": best_model,
        "input_type": best_input_type,
        "feature_names": (
            list(FEATURE_NAMES)
            if best_input_type != "url_text"
            else []
        ),
        "model_name": best_name,
        "version": "2.1.0",
        "evaluation": {
            metric: float(best_predictions[metric])
            for metric in (
                "Accuracy",
                "Precision",
                "Recall",
                "F1-score",
                "ROC-AUC",
                "PR-AUC",
                "False-positive rate",
                "Brier score",
            )
        },
        "evaluation_strategy": (
            f"{N_SPLITS}-fold hostname-group cross-validation with "
            f"{CALIBRATION_SPLITS}-fold hostname-group sigmoid calibration"
        ),
        "probability_calibration": "sigmoid",
        "data_sources": (
            sorted(df["source"].dropna().astype(str).unique())
            if "source" in df.columns
            else []
        ),
        "data_warnings": data_warnings,
    }

    joblib.dump(model_package, CANDIDATE_MODEL_FILE)

    print("\nSelected model:", best_name)
    print("Out-of-fold confusion matrix:")
    print(confusion_matrix(
        labels,
        predictions_by_model[best_name],
        labels=[0, 1],
    ))
    print(classification_report(
        labels,
        predictions_by_model[best_name],
        labels=[0, 1],
        target_names=["Benign", "Phishing"],
        zero_division=0,
    ))
    print("Saved candidate model:", CANDIDATE_MODEL_FILE)
    print("Saved comparison:", MODEL_DIR / "model_comparison.csv")


if __name__ == "__main__":
    main()
