
import numpy as np
import re
import ipaddress
from urllib.parse import urlparse

from sklearn.base import BaseEstimator, TransformerMixin


FEATURE_NAMES = (
    "url_length",
    "hostname_length",
    "dot_count",
    "hyphen_count",
    "at_count",
    "question_count",
    "equal_count",
    "slash_count",
    "https",
    "has_ip",
    "has_at_symbol",
    "has_suspicious_keyword",
    "has_double_slash",
    "subdomain_count",
)


def extract_features(url):
    """Trích xuất các đặc trưng cơ bản từ URL."""

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    try:
        ipaddress.ip_address(hostname)
        has_ip = 1
    except ValueError:
        has_ip = 0

    features = {
        "url_length": len(url),
        "hostname_length": len(hostname),
        "dot_count": url.count("."),
        "hyphen_count": url.count("-"),
        "at_count": url.count("@"),
        "question_count": url.count("?"),
        "equal_count": url.count("="),
        "slash_count": url.count("/"),
        "https": 1 if parsed.scheme == "https" else 0,
        "has_ip": has_ip,
        "has_at_symbol": 1 if "@" in url else 0,
        "has_suspicious_keyword": 1 if re.search(
            r"login|verify|update|secure|account|banking|password",
            url,
            re.IGNORECASE
        ) else 0,
        "has_double_slash": 1 if "//" in url.split("://", 1)[-1] else 0,
        "subdomain_count": max(0, len(hostname.split(".")) - 2)
    }

    return features


class URLFeatureTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = [
            [extract_features(str(url))[name] for name in FEATURE_NAMES]
            for url in X
        ]
        return np.asarray(rows, dtype=float).reshape(-1, len(FEATURE_NAMES))
