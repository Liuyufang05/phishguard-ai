
import re
import ipaddress
from urllib.parse import urlparse


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
