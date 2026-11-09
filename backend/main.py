
from pathlib import Path
from urllib.parse import urlparse

import joblib
import pandas as pd
from feature_extractor import extract_features

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import logging
from pathlib import Path

import os
from dotenv import load_dotenv

# Doc cau hinh tu file .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "PhishGuard AI")
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
# ==============================
# LOGGING CONFIGURATION
# ==============================

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "phishguard.log",
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("PhishGuardAI")
# =====================================
# 1. KHOI TAO UNG DUNG
# =====================================

app = FastAPI(
    title=APP_NAME,
    debug=DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# =====================================
# 2. DUONG DAN VA TAI MO HINH
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "phishguard_model.pkl"

model_package = None

if MODEL_PATH.exists():
    model_package = joblib.load(MODEL_PATH)
    print("PhishGuard AI: Da tai mo hinh thanh cong!")
else:
    print("CANH BAO: Chua tim thay mo hinh Machine Learning!")


# =====================================
# 3. DU LIEU DAU VAO
# =====================================

from pydantic import BaseModel, Field

class ScanRequest(BaseModel):
    url: str = Field(
        ...,
        min_length=4,
        max_length=2048,
        description="URL cần phân tích"
    )


# =====================================
# 4. CAC API CO BAN
# =====================================

@app.get("/")
def home():
    return {
        "message": "Chao mung den voi PhishGuard AI!",
        "status": "Backend is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "OK",
        "project": "PhishGuard AI",
        "model_loaded": model_package is not None
    }


# =====================================
# 5. API KIEM TRA URL
# =====================================


@app.post("/api/scan")
def scan_url(request: ScanRequest):

    # 1. Kiem tra mo hinh AI
    if model_package is None:
        raise HTTPException(
            status_code=503,
            detail="Mo hinh AI chua duoc huan luyen hoac chua duoc tai."
        )

    # 2. Lay va chuan hoa URL
    url = request.url.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail="Vui long nhap dia chi URL."
        )

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    # 3. Kiem tra cau truc URL
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError("Giao thuc khong hop le.")

        if not parsed.hostname:
            raise ValueError("URL khong co ten mien.")

        if any(char.isspace() for char in parsed.hostname):
            raise ValueError("Ten mien khong hop le.")

        # Kiem tra port
        _ = parsed.port

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Dia chi URL khong hop le."
        )

    # 4. Kiem tra cau truc goi mo hinh
    try:
        feature_names = model_package["feature_names"]
        model = model_package["model"]

        if not feature_names or not isinstance(feature_names, list):
            raise ValueError("Danh sach dac trung khong hop le.")

        if not hasattr(model, "predict_proba"):
            raise ValueError("Mo hinh khong ho tro predict_proba.")

    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=503,
            detail="Cau hinh mo hinh AI khong hop le."
        )

    # 5. Trich xuat dac trung URL
    try:
        features = extract_features(url)

        missing_features = [
            name for name in feature_names
            if name not in features
        ]

        if missing_features:
            raise ValueError("Thieu dac trung dau vao.")

        input_data = pd.DataFrame(
            [[features[name] for name in feature_names]],
            columns=feature_names
        )

        if input_data.isnull().values.any():
            raise ValueError("Du lieu dac trung chua hop le.")

    except Exception:
        logger.exception("Loi khi trich xuat dac trung URL")
        raise HTTPException(
            status_code=422,
            detail="Khong the trich xuat dac trung tu URL."
        )

    # 6. Du doan bang Machine Learning
    try:
        prediction = int(model.predict(input_data)[0])

        probabilities = model.predict_proba(input_data)[0]
        classes = list(model.classes_)

        if 1 not in classes:
            raise ValueError("Mo hinh khong co lop phishing.")

        phishing_index = classes.index(1)
        phishing_probability = float(
            probabilities[phishing_index]
        )

        if not 0 <= phishing_probability <= 1:
            raise ValueError("Xac suat du doan khong hop le.")

        risk_score = round(phishing_probability * 100, 2)

    except Exception:
        logger.exception("Loi khi mo hinh phan tich URL")
        raise HTTPException(
            status_code=500,
            detail="Mo hinh AI gap loi khi phan tich URL."
        )

    # 7. Phan loai muc do rui ro
    if risk_score >= 70:
        risk_level = "High"
        result = "Phishing"

    elif risk_score >= 40:
        risk_level = "Medium"
        result = "Suspicious"

    else:
        risk_level = "Low"
        result = "Benign"

    # 8. Tra ve ket qua
    return {
        "url": url,
        "prediction": prediction,
        "result": result,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "phishing_probability": round(
            phishing_probability, 4
        ),
        "model_name": model_package.get(
            "model_name", "Unknown"
        ),
        "features": features,
        "warning": (
            "Ket qua la danh gia tu mo hinh hoc may, "
            "khong dam bao website an toan tuyet doi."
        )
    }


# =====================================
# 6. API THONG TIN MO HINH
# =====================================

@app.get("/api/model-info")
def model_info():

    if model_package is None:
        raise HTTPException(
            status_code=503,
            detail="Chua co mo hinh AI."
        )

    return {
        "model_name": model_package["model_name"],
        "version": model_package["version"],
        "features": model_package["feature_names"],
        "number_of_features": len(
            model_package["feature_names"]
        )
    }
