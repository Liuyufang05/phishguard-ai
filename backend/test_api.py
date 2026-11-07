
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200


def test_model_info():
    response = client.get("/api/model-info")
    assert response.status_code == 200


def test_scan_valid_url():
    response = client.post(
        "/api/scan",
        json={"url": "https://example.com"}
    )

    # 503 co the xay ra neu chua co mo hinh
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert "risk_level" in data
        assert "risk_score" in data
        assert "features" in data


def test_scan_invalid_url():
    response = client.post(
        "/api/scan",
        json={"url": "http://"}
    )

    assert response.status_code in [400, 422]


def test_scan_empty_url():
    response = client.post(
        "/api/scan",
        json={"url": ""}
    )

    assert response.status_code == 422
