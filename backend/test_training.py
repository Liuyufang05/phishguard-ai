import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from backend.main import ScanRequest, scan_url
from backend.feature_extractor import (
    FEATURE_NAMES,
    URLFeatureTransformer,
    extract_features,
)
from backend.train_model import (
    build_models,
    calibrated_model,
    clean_dataset,
    hostname_group,
    make_group_splits,
    source_label_warnings,
)
from backend.prepare_dataset import build_dataset


class TrainingTests(unittest.TestCase):
    def test_feature_transformer_matches_existing_extractor(self):
        urls = [
            "https://example.com/login",
            "http://192.0.2.1/verify",
        ]
        transformed = URLFeatureTransformer().fit_transform(urls)
        expected = np.asarray([
            [extract_features(url)[name] for name in FEATURE_NAMES]
            for url in urls
        ], dtype=float)

        np.testing.assert_array_equal(transformed, expected)

    def test_clean_dataset_removes_bad_labels_and_duplicate_urls(self):
        data = pd.DataFrame({
            "url": [
                "https://safe.example",
                "https://safe.example",
                "https://phish.example",
                "repeated header",
            ],
            "label": [0, 0, 1, "label"],
        })

        cleaned = clean_dataset(data)

        self.assertEqual(len(cleaned), 2)
        self.assertEqual(set(cleaned["label"]), {0, 1})

    def test_clean_dataset_rejects_conflicting_url_labels(self):
        data = pd.DataFrame({
            "url": ["https://same.example", "https://same.example"],
            "label": [0, 1],
        })

        with self.assertRaisesRegex(ValueError, "conflicting labels"):
            clean_dataset(data)

    def test_source_audit_warns_when_provenance_is_missing(self):
        data = pd.DataFrame({
            "url": ["https://safe.example", "https://phish.example"],
            "label": [0, 1],
        })

        warnings = source_label_warnings(data)

        self.assertIn("no source metadata", warnings[0])

    def test_source_audit_detects_source_label_confounding(self):
        data = pd.DataFrame({
            "source": ["Tranco", "Tranco", "OpenPhish", "OpenPhish"],
            "label": [0, 0, 1, 1],
        })

        warnings = source_label_warnings(data)

        self.assertIn("single label", warnings[0])

    def test_source_audit_warns_on_partial_provenance(self):
        data = pd.DataFrame({
            "source": ["Tranco", None],
            "label": [0, 1],
        })

        warnings = source_label_warnings(data)

        self.assertIn("missing source metadata", warnings[0])

    def test_source_audit_accepts_sources_with_both_labels(self):
        data = pd.DataFrame({
            "source": ["feed-a", "feed-a", "feed-b", "feed-b"],
            "label": [0, 1, 0, 1],
        })

        self.assertEqual(source_label_warnings(data), [])

    def test_dataset_builder_records_source_and_collection_time(self):
        phishing_urls = [
            f"https://phish-{index}.example/login"
            for index in range(50)
        ]
        benign_urls = [
            f"https://safe-{index}.example/"
            for index in range(50)
        ]

        dataset = build_dataset(
            phishing_urls,
            benign_urls,
            collected_at="2026-01-01T00:00:00+00:00",
        )

        self.assertEqual(set(dataset.columns), {
            "url",
            "label",
            "source",
            "collected_at",
        })
        self.assertEqual(dataset["label"].value_counts().to_dict(), {0: 50, 1: 50})
        self.assertEqual(
            set(dataset["source"]),
            {"OpenPhish", "Tranco"},
        )
        self.assertEqual(
            set(dataset["collected_at"]),
            {"2026-01-01T00:00:00+00:00"},
        )

    def test_dataset_builder_rejects_conflicting_labels(self):
        urls = [
            f"https://sample-{index}.example/"
            for index in range(50)
        ]
        phishing_urls = ["https://same.example"] + urls
        benign_urls = ["https://same.example"] + urls

        with self.assertRaisesRegex(ValueError, "mau thuan"):
            build_dataset(phishing_urls, benign_urls)

    def test_grouped_folds_keep_hostnames_separate(self):
        urls = np.asarray([
            f"https://benign-{index}.example/path"
            for index in range(10)
        ] + [
            f"https://phish-{index}.example/login"
            for index in range(10)
        ])
        labels = np.asarray([0] * 10 + [1] * 10)

        for train_indices, validation_indices in make_group_splits(
            urls,
            labels,
        ):
            training_hosts = {
                hostname_group(urls[index])
                for index in train_indices
            }
            validation_hosts = {
                hostname_group(urls[index])
                for index in validation_indices
            }
            self.assertFalse(training_hosts & validation_hosts)
            self.assertEqual(set(labels[validation_indices]), {0, 1})

    def test_sigmoid_calibration_uses_grouped_validation(self):
        urls = np.asarray([
            f"https://benign-{index}.example/path"
            for index in range(10)
        ] + [
            f"https://phish-{index}.example/login"
            for index in range(10)
        ])
        labels = np.asarray([0] * 10 + [1] * 10)
        estimator = build_models()["Character n-gram"][1]

        model = calibrated_model(estimator, urls, labels)
        model.fit(urls, labels)
        probabilities = model.predict_proba(urls[:3])

        self.assertEqual(probabilities.shape, (3, 2))
        self.assertTrue(np.all((probabilities >= 0) & (probabilities <= 1)))
        np.testing.assert_allclose(probabilities.sum(axis=1), 1.0)

        package = {
            "model": model,
            "input_type": "url_text",
            "feature_names": [],
            "model_name": "Character n-gram",
            "version": "2.1.0",
            "probability_calibration": "sigmoid",
        }
        with patch("backend.main.model_package", package):
            result = scan_url(ScanRequest(url=urls[0]))

        self.assertEqual(result["model_name"], "Character n-gram")

    def test_character_and_hybrid_models_accept_raw_urls(self):
        urls = np.asarray([
            "https://bank.example/login",
            "https://bank.example/verify",
            "https://secure.example/account",
            "https://service.example/signin",
            "https://garden.example/plants",
            "https://museum.example/visit",
            "https://weather.example/today",
            "https://books.example/catalog",
        ])
        labels = np.asarray([1, 1, 1, 1, 0, 0, 0, 0])
        models = build_models()

        for name in ("Character n-gram", "Hybrid URL"):
            input_type, model = models[name]
            self.assertEqual(input_type, "url_text")
            model.fit(urls, labels)
            self.assertEqual(model.predict_proba(urls[:2]).shape, (2, 2))

    def test_api_accepts_a_text_pipeline_model_package(self):
        urls = np.asarray([
            "https://bank.example/login",
            "https://secure.example/verify",
            "https://garden.example/plants",
            "https://museum.example/visit",
        ])
        labels = np.asarray([1, 1, 0, 0])
        model = build_models()["Hybrid URL"][1].fit(urls, labels)
        package = {
            "model": model,
            "input_type": "url_text",
            "feature_names": [],
            "model_name": "Hybrid URL",
            "version": "2.0.0",
        }

        with patch("backend.main.model_package", package):
            result = scan_url(ScanRequest(url="https://bank.example/login"))

        self.assertEqual(result["model_name"], "Hybrid URL")
        self.assertIn(result["risk_level"], {"Low", "Medium", "High"})
        self.assertEqual(len(result["features"]), len(FEATURE_NAMES))

    def test_api_keeps_legacy_feature_model_package_compatible(self):
        urls = np.asarray([
            "https://bank.example/login",
            "https://secure.example/verify",
            "https://garden.example/plants",
            "https://museum.example/visit",
        ])
        labels = np.asarray([1, 1, 0, 0])
        features = pd.DataFrame([
            extract_features(url) for url in urls
        ], columns=FEATURE_NAMES)
        model = build_models()["Logistic Regression"][1].fit(
            features,
            labels,
        )
        package = {
            "model": model,
            "feature_names": list(FEATURE_NAMES),
            "model_name": "Logistic Regression",
        }

        with patch("backend.main.model_package", package):
            result = scan_url(ScanRequest(url="https://bank.example/login"))

        self.assertEqual(result["model_name"], "Logistic Regression")
        self.assertEqual(len(result["features"]), len(FEATURE_NAMES))


if __name__ == "__main__":
    unittest.main()
